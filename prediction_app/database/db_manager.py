from typing import List, Optional
import json
from datetime import datetime, timedelta
from .models import Session, Question, User, user_questions
from sqlalchemy.sql import func

class DatabaseManager:
    def __init__(self):
        self.session = Session()

    def create_user(self, username: str, interests: List[str]) -> int:
        """Create a new user and return their ID"""
        user = User(
            username=username,
            interests=json.dumps(interests)
        )
        self.session.add(user)
        self.session.commit()
        return user.id

    def get_user(self, username: str) -> Optional[dict]:
        """Get user by username"""
        user = self.session.query(User).filter(User.username == username).first()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'interests': json.loads(user.interests),
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        return None

    def get_unused_question(self, interest: str, user_id: int) -> Optional[dict]:
        """Get a random question that hasn't been shown to this user"""
        # Get questions for the interest that haven't been viewed by this user
        subquery = self.session.query(user_questions.c.question_id)\
            .filter(user_questions.c.user_id == user_id)\
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
                'source_articles': json.loads(question.source_articles),
                'created_at': question.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        return None

    def mark_question_as_viewed(self, question_id: int, user_id: int) -> None:
        """Mark that a user has viewed a question"""
        self.session.execute(
            user_questions.insert().values(
                user_id=user_id,
                question_id=question_id,
                viewed_at=datetime.utcnow()
            )
        )
        self.session.commit()

    def get_user_question_history(self, user_id: int, interest: Optional[str] = None) -> List[dict]:
        """Get questions viewed by a specific user"""
        query = self.session.query(Question, user_questions.c.viewed_at)\
            .join(user_questions)\
            .filter(user_questions.c.user_id == user_id)
            
        if interest:
            query = query.filter(Question.interest == interest)
            
        results = query.order_by(user_questions.c.viewed_at.desc()).all()
        
        return [{
            'id': q.Question.id,
            'question': q.Question.question_text,
            'interest': q.Question.interest,
            'source_articles': json.loads(q.Question.source_articles),
            'viewed_at': q.viewed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': q.Question.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': q.Question.status,
            'result': q.Question.result,
            'resolution_note': q.Question.resolution_note
        } for q in results] 

    def save_question(self, question_text: str, interest: str, source_articles: List[str]) -> int:
        """Save a question with resolution date"""
        # Extract resolution date from question text (implement this based on your needs)
        resolution_date = self._extract_resolution_date(question_text)
        
        question = Question(
            question_text=question_text,
            interest=interest,
            source_articles=json.dumps(source_articles),
            resolution_date=resolution_date,
            status='pending'
        )
        self.session.add(question)
        self.session.commit()
        return question.id

    def _extract_resolution_date(self, question: str) -> datetime:
        """Extract resolution date from question text"""
        # This is a simple implementation - enhance based on your needs
        now = datetime.utcnow()
        
        # Check for specific time markers
        if 'tomorrow' in question.lower():
            return now + timedelta(days=1)
        elif 'this week' in question.lower():
            return now + timedelta(days=7)
        elif 'weekend' in question.lower():
            # Calculate next Sunday
            days_until_sunday = (6 - now.weekday()) % 7
            return now + timedelta(days=days_until_sunday)
            
        # Default to 7 days if no specific time found
        return now + timedelta(days=7)

    def get_pending_resolutions(self) -> List[dict]:
        """Get questions that need resolution (past resolution_date and still pending)"""
        now = datetime.utcnow()
        questions = self.session.query(Question)\
            .filter(Question.status == 'pending')\
            .filter(Question.resolution_date <= now)\
            .all()
            
        return [{
            'id': q.id,
            'question': q.question_text,
            'interest': q.interest,
            'created_at': q.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'resolution_date': q.resolution_date.strftime('%Y-%m-%d %H:%M:%S')
        } for q in questions]

    def resolve_question(self, question_id: int, result: bool, note: str = None) -> None:
        """Resolve a question with its result"""
        question = self.session.query(Question).get(question_id)
        if question:
            question.status = 'resolved'
            question.result = result
            question.resolution_note = note
            self.session.commit() 

    def update_user_interests(self, user_id: int, interests: List[str]) -> None:
        """Update user interests"""
        user = self.session.query(User).filter(User.id == user_id).first()
        if user:
            user.interests = json.dumps(interests)
            self.session.commit() 