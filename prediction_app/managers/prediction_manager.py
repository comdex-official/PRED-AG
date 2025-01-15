from typing import Dict, Set, List, Optional
import datetime
import random
from functools import lru_cache
import time
import json
import logging

from ..scrapers.news_scraper import NewsScraper
from ..agents.question_generator import QuestionGenerator
from ..database.db_manager import DatabaseManager
from ..config.config import QUESTION_CONFIG

logger = logging.getLogger(__name__)

class PredictionManager:
    def __init__(self, username: str):
        self.username = username
        self.scraper = NewsScraper()
        self.generator = QuestionGenerator()
        self.db_manager = DatabaseManager()
        
        # Get or create user
        user = self.db_manager.get_user(username)
        if user:
            self.user_id = user['id']
            self.interests = set(user['interests'])
        else:
            self.user_id = self.db_manager.create_user(username, [])
            self.interests = set()

    def add_user_interest(self, interest: str) -> None:
        """Add a new interest to user's preferences"""
        self.interests.add(interest.lower())

    @lru_cache(maxsize=100)
    def _cached_scrape(self, interest: str, timestamp: int) -> List[str]:
        """Cache scraped results for an hour"""
        return self.scraper.scrape_news(interest)

    def get_fresh_questions(self, count: int = 5) -> dict:
        """Get fresh questions for user's interests"""
        try:
            user = self.db_manager.get_user(self.username)
            if not user:
                return {"error": "User not found"}
            
            interests = user['interests']
            if not interests:
                return {"error": "No interests defined for user"}
            
            interest = random.choice(interests)
            articles = self.scraper.scrape_news(interest)
            sources = [f"https://news.source/{i}" for i in range(len(articles))]
            
            if not articles:
                return {"error": f"No articles found for {interest}"}
            
            questions = self.generator.generate_multiple_questions(
                articles=articles,
                sources=sources,
                interest=interest,
                count=count
            )
            
            # Save questions to database and mark as viewed
            saved_questions = []
            for q in questions:
                question_id = self.db_manager.create_question(
                    question_text=q["question"],
                    interest=interest,
                    source_articles=articles,
                    source_links=q["sources"]
                )
                # Mark question as viewed by this user
                self.db_manager.mark_question_as_viewed(question_id, self.user_id)
                saved_questions.append(q)
            
            return {
                "questions": saved_questions,
                "interest": interest
            }
            
        except Exception as e:
            return {"error": str(e)}

    def get_question_history(self, interest: Optional[str] = None) -> List[dict]:
        """Get question history for this user"""
        try:
            return self.db_manager.get_user_question_history(self.user_id, interest)
        except Exception as e:
            return []

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