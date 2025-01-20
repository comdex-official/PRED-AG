from typing import List, Optional, Dict
import json
from datetime import datetime, timezone
from .models import Session, Question, User, UserQuestionResponse
from sqlalchemy.sql import func
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

class DatabaseManager:
    def __init__(self):
        self.session = Session()

    def create_user(self, username: str, interests: List[str]) -> int:
        """Create a new user and return their ID"""
        user = User(
            username=username,
            interests=interests  # Assuming interests are stored directly as a list
        )
        self.session.add(user)
        self.session.commit()
        return user.id

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username with sanitized input"""
        try:
            user = self.session.query(User)\
                .filter(User.username == username)\
                .first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'interests': user.interests,
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            return None
        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}")
            return None

    def get_unused_question(self, interest: str, user_id: int) -> Optional[Dict]:
        """Get a random question that hasn't been shown to this user"""
        subquery = self.session.query(UserQuestionResponse.question_id)\
            .filter(UserQuestionResponse.user_id == user_id)\
            .subquery()
        question = self.session.query(Question)\
            .filter(Question.interest == interest)\
            .filter(~Question.id.in_(subquery))\
            .order_by(func.random())\
            .first()
        if question:
            return {
                'id': question.id,
                'question': question.question_text,
                'interest': question.interest,
                'source_articles': question.source_articles,
                'created_at': question.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        return None

    def mark_question_as_viewed(self, question_id: int, user_id: int) -> None:
        """Mark question as viewed with input validation"""
        try:
            if not isinstance(question_id, int) or not isinstance(user_id, int):
                raise ValueError("Invalid input types")
            response = UserQuestionResponse(
                user_id=user_id,
                question_id=question_id,
                viewed_at=datetime.now(timezone.utc)
            )
            self.session.add(response)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error: {str(e)}")

    def get_user_question_history(self, user_id: int, interest: Optional[str] = None) -> List[Dict]:
        """Get questions answered by a specific user"""
        try:
            query = self.session.query(UserQuestionResponse, Question)\
                .join(Question, UserQuestionResponse.question_id == Question.id)\
                .filter(UserQuestionResponse.user_id == user_id)\
                .filter(UserQuestionResponse.response.isnot(None))  # Add filter for non-null response
            if interest:
                query = query.filter(Question.interest == interest)
            results = query.order_by(UserQuestionResponse.viewed_at.desc()).all()
            return [{
                'id': q.Question.id,
                'question': q.Question.question_text,
                'interest': q.Question.interest,
                'source_articles': q.Question.source_articles,
                'viewed_at': q.UserQuestionResponse.viewed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': q.Question.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'response': q.UserQuestionResponse.response.value,
                'answered_at': q.UserQuestionResponse.answered_at.strftime('%Y-%m-%d %H:%M:%S') if q.UserQuestionResponse.answered_at else None,
                'resolution': q.Question.outcome,
                'resolved_at': q.Question.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if q.Question.resolved_at else None
            } for q in results]
        except Exception as e:
            return []

    def resolve_question(self, question_id: int, result: bool, note: str = None) -> None:
        """Resolve question with input validation"""
        try:
            if not isinstance(question_id, int):
                raise ValueError("Invalid question_id type")
            if not isinstance(result, bool):
                raise ValueError("Invalid result type")
            if note is not None:
                note = str(note)[:500]  # Limit note length
            question = self.session.query(Question).get(question_id)
            if question:
                question.resolved_at = datetime.now(timezone.utc)
                question.outcome = result
                question.resolution_note = note
                self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error: {str(e)}")

    def update_user_interests(self, user_id: int, interests: List[str]) -> None:
        """Update user interests with input validation"""
        try:
            if not isinstance(user_id, int):
                raise ValueError("Invalid user_id type")
            if not isinstance(interests, list):
                raise ValueError("Invalid interests type")
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                user.interests = interests
                self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error: {str(e)}")

    def get_multiple_unused_questions(self, interest: str, user_id: int, count: int = 5) -> List[Dict]:
        """Get multiple random questions with sanitized inputs"""
        try:
            if not isinstance(user_id, int) or not isinstance(count, int):
                raise ValueError("Invalid input types")
            interest = str(interest).lower()
            
            # Get all question IDs that this user has already responded to
            responded_question_ids = [
                r[0] for r in self.session.query(UserQuestionResponse.question_id)
                .filter(UserQuestionResponse.user_id == user_id)
                .all()
            ]
            
            # Query for questions this user hasn't seen yet
            query = self.session.query(Question)\
                .filter(Question.interest == interest)
            
            if responded_question_ids:
                query = query.filter(~Question.id.in_(responded_question_ids))
                
            questions = query.order_by(func.random())\
                .limit(count)\
                .all()
            
            return [{
                'id': q.id,
                'question': q.question_text,
                'interest': q.interest,
                'source_articles': q.source_articles,
                'created_at': q.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for q in questions]
        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}")
            return []

    def create_question(self, question_text: str, interest: str, 
                        source_articles: List[str], source_links: List[str]) -> int:
        """Create a new question and return its ID"""
        question = Question(
            question_text=question_text,
            interest=interest,
            source_articles=source_articles,
            source_links=source_links
        )
        self.session.add(question)
        self.session.commit()
        return question.id

    def get_questions(self, interest: str = None) -> List[Dict]:
        """Get all questions, optionally filtered by interest"""
        query = self.session.query(Question)
        if interest:
            query = query.filter(Question.interest == interest)
        questions = query.all()
        return [{
            'id': q.id,
            'question': q.question_text,
            'interest': q.interest,
            'source_articles': q.source_articles,
            'source_links': q.source_links,
            'created_at': q.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'resolved_at': q.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if q.resolved_at else None,
            'outcome': q.outcome,
            'resolution_note': q.resolution_note
        } for q in questions]

    def update_question_response(self, question_id: int, user_id: int, response: str) -> None:
        """Update user's response to a question with input validation"""
        try:
            if not isinstance(question_id, int) or not isinstance(user_id, int):
                raise ValueError("Invalid input types")
            
            # Find the existing response record
            user_response = self.session.query(UserQuestionResponse)\
                .filter(UserQuestionResponse.user_id == user_id)\
                .filter(UserQuestionResponse.question_id == question_id)\
                .first()
            
            if user_response:
                user_response.response = response
                user_response.answered_at = datetime.now(timezone.utc)
            else:
                # Create new response if it doesn't exist
                user_response = UserQuestionResponse(
                    user_id=user_id,
                    question_id=question_id,
                    response=response,
                    responded_at=datetime.now(timezone.utc)
                )
                self.session.add(user_response)
                
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error: {str(e)}")