from typing import Dict, Set, List, Optional
import datetime
import random
from functools import lru_cache
import time

from ..scrapers.news_scraper import NewsScraper
from ..agents.question_generator import QuestionGenerator
from ..database.db_manager import DatabaseManager

class PredictionManager:
    def __init__(self, api_key: str, username: str):
        self.scraper = NewsScraper()
        self.generator = QuestionGenerator(api_key)
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

    def get_fresh_question(self) -> dict:
        """Get a question, first trying unused ones from DB, then generating new ones"""
        if not self.interests:
            return {"error": "No interests added"}
            
        interest = random.choice(list(self.interests))
        
        # First try to get an unused question from the database
        unused_question = self.db_manager.get_unused_question(interest, self.user_id)
        if unused_question:
            # Mark it as viewed by this user
            self.db_manager.mark_question_as_viewed(unused_question['id'], self.user_id)
            return {
                "question": unused_question['question'],
                "source_articles": unused_question['source_articles'],
                "interest": interest,
                "source": "database"
            }
        
        # If no unused questions, generate a new one
        articles = self.scraper.scrape_news(interest)
        if not articles:
            return {"error": f"No recent articles found for {interest}"}
            
        question = self.generator.generate_question(articles, interest)
        
        # Save to database and mark as viewed
        question_id = self.db_manager.save_question(question, interest, articles)
        self.db_manager.mark_question_as_viewed(question_id, self.user_id)
        
        return {
            "question": question,
            "source_articles": articles,
            "interest": interest,
            "source": "generated"
        }

    def get_question_history(self, interest: Optional[str] = None) -> List[dict]:
        """Get question history for this user"""
        return self.db_manager.get_user_question_history(self.user_id, interest)

    def reset_used_questions(self, interest: Optional[str] = None) -> None:
        """Reset the 'used' flag for questions, optionally for a specific interest"""
        self.db_manager.reset_used_questions(interest) 