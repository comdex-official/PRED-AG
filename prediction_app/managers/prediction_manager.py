from typing import Dict, Set, List, Optional
import datetime
import random
from functools import lru_cache
import time

from ..scrapers.news_scraper import NewsScraper
from ..agents.question_generator import QuestionGenerator
from ..database.db_manager import DatabaseManager
from ..config.config import QUESTION_CONFIG

class PredictionManager:
    def __init__(self, username: str):
        self.scraper = NewsScraper()
        self.generator = QuestionGenerator()
        self.interests = set()
        self.db_manager = DatabaseManager()
        
        # Get or create user
        user = self.db_manager.get_user(username)
        if user:
            self.user_id = user['id']
            self.interests = set(user['interests'])
        else:
            self.user_id = self.db_manager.create_user(username, [])

    def add_user_interest(self, interest: str) -> None:
        """Add a new interest to user's preferences"""
        self.interests.add(interest.lower())

    @lru_cache(maxsize=100)
    def _cached_scrape(self, interest: str, timestamp: int) -> List[str]:
        """Cache scraped results for an hour"""
        return self.scraper.scrape_news(interest)

    def get_fresh_questions(self, count: int = None) -> dict:
        """Get multiple fresh questions"""
        if count is None:
            count = QUESTION_CONFIG["default_count"]
        
        if not self.interests:
            return {"error": "No interests added"}
        
        results = []
        used_interests = set()
        
        while len(results) < count:
            # Try to use different interests for variety
            available_interests = list(self.interests - used_interests) or list(self.interests)
            interest = random.choice(available_interests)
            used_interests.add(interest)
            
            # First try to get unused questions from the database
            unused_questions = self.db_manager.get_multiple_unused_questions(
                interest, 
                self.user_id, 
                count=count-len(results)
            )
            
            for q in unused_questions:
                self.db_manager.mark_question_as_viewed(q['id'], self.user_id)
                results.append({
                    "question": q['question'],
                    "source_articles": q['source_articles'],
                    "interest": interest,
                    "source": "database"
                })
            
            # If we still need more questions, generate new ones
            if len(results) < count:
                articles = self.scraper.scrape_news(interest)
                if articles:
                    new_questions = self.generator.generate_multiple_questions(
                        articles, 
                        interest,
                        count=count-len(results)
                    )
                    
                    for question in new_questions:
                        # Save to database and mark as viewed
                        question_id = self.db_manager.save_question(question, interest, articles)
                        self.db_manager.mark_question_as_viewed(question_id, self.user_id)
                        
                        results.append({
                            "question": question,
                            "source_articles": articles,
                            "interest": interest,
                            "source": "generated"
                        })
        
        return {
            "questions": results,
            "count": len(results)
        }

    def get_question_history(self, interest: Optional[str] = None) -> List[dict]:
        """Get question history for this user"""
        return self.db_manager.get_user_question_history(self.user_id, interest)

    def reset_used_questions(self, interest: Optional[str] = None) -> None:
        """Reset the 'used' flag for questions, optionally for a specific interest"""
        self.db_manager.reset_used_questions(interest) 

    def get_pending_resolutions(self) -> List[dict]:
        """Get questions that need resolution"""
        return self.db_manager.get_pending_resolutions()

    def resolve_question(self, question_id: int, result: str, note: str = None) -> None:
        """Resolve a question with yes/no result"""
        result_bool = result.lower() == 'yes'
        self.db_manager.resolve_question(question_id, result_bool, note) 