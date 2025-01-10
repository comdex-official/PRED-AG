from typing import Dict, Set, List
import datetime
import random
from functools import lru_cache
import time

from ..scrapers.news_scraper import NewsScraper
from ..agents.question_generator import QuestionGenerator

class PredictionManager:
    def __init__(self, openai_api_key: str):
        self.scraper = NewsScraper()
        self.generator = QuestionGenerator(openai_api_key)
        self.user_interests: Set[str] = set()
        self.question_history: List[Dict] = []
        self.last_scrape_time: Dict[str, float] = {}
        self.scrape_cooldown = 3600  # 1 hour cooldown

    def add_user_interest(self, interest: str) -> None:
        """Add a new interest to user's preferences"""
        self.user_interests.add(interest.lower())

    @lru_cache(maxsize=100)
    def _cached_scrape(self, interest: str, timestamp: int) -> List[str]:
        """Cache scraped results for an hour"""
        return self.scraper.scrape_news(interest)

    def get_fresh_question(self) -> Dict:
        """Get a new question based on user interests"""
        if not self.user_interests:
            return {"error": "No user interests set"}

        interest = random.choice(list(self.user_interests))
        
        # Check cooldown
        current_time = time.time()
        if (interest in self.last_scrape_time and 
            current_time - self.last_scrape_time[interest] < self.scrape_cooldown):
            timestamp = self.last_scrape_time[interest]
        else:
            timestamp = current_time
            self.last_scrape_time[interest] = timestamp
            
        articles = self._cached_scrape(interest, int(timestamp))
        
        if not articles:
            return {"error": f"No recent articles found for {interest}"}
            
        question = self.generator.generate_question(articles, interest)
        
        question_data = {
            "question": question,
            "interest": interest,
            "timestamp": datetime.datetime.now(),
            "source_articles": articles[:3]
        }
        
        self.question_history.append(question_data)
        return question_data 