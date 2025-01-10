import requests
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urlparse
from ..config.config import NEWS_SOURCES, SCRAPING_RULES, HEADERS

class NewsScraper:
    def __init__(self):
        self.sources = NEWS_SOURCES
        self.rules = SCRAPING_RULES
        self.headers = HEADERS

    def scrape_news(self, interest: str) -> List[str]:
        """Scrape recent news articles based on interest"""
        articles = []
        
        if interest not in self.sources:
            return articles
            
        for source in self.sources[interest]:
            try:
                articles.extend(self._scrape_single_source(source))
            except Exception as e:
                print(f"Error scraping {source}: {str(e)}")
                continue
                
        return articles[:5]  # Return top 5 articles

    def _scrape_single_source(self, url: str) -> List[str]:
        """Scrape a single news source"""
        articles = []
        domain = urlparse(url).netloc
        
        try:
            print(f"Attempting to scrape: {url}")  # Debug line
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if domain in self.rules:
                rule = self.rules[domain]
                articles_elements = soup.select(rule["article_selector"])
                print(f"Found {len(articles_elements)} articles for {domain}")  # Debug line
                
                for article in articles_elements:
                    title = article.select_one(rule["title_selector"])
                    if title and title.text.strip():
                        articles.append(title.text.strip())
            
            print(f"Successfully scraped {len(articles)} articles from {domain}")  # Debug line
            return articles
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")  # Debug line
            return [] 