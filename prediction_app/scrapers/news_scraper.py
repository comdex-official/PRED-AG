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
        
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        if domain in self.rules:
            rule = self.rules[domain]
            articles_elements = soup.select(rule["article_selector"])
            
            for article in articles_elements:
                title = article.select_one(rule["title_selector"])
                if title and title.text.strip():
                    articles.append(title.text.strip())
        else:
            # Default scraping if no specific rules
            headlines = soup.find_all(['h1', 'h2', 'h3'], class_=['headline', 'title'])
            articles.extend([h.text.strip() for h in headlines if h.text.strip()])
            
        return articles 