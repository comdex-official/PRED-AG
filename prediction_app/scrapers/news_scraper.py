import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urlparse
import json
import time
from datetime import datetime, timedelta
from ..config.config import NEWS_SOURCES, SCRAPING_RULES, HEADERS

class NewsScraper:
    def __init__(self):
        self.sources = NEWS_SOURCES
        self.rules = SCRAPING_RULES
        self.headers = HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def scrape_news(self, interest: str) -> List[str]:
        """Scrape recent news articles based on interest"""
        articles = []
        
        if interest not in self.sources:
            print(f"No sources configured for {interest}")
            return articles
            
        for source in self.sources[interest]:
            try:
                time.sleep(1)  # Rate limiting
                new_articles = self._scrape_single_source(source)
                print(f"Found {len(new_articles)} recent articles from {source}")
                articles.extend(new_articles)
            except Exception as e:
                print(f"Error scraping {source}: {str(e)}")
                continue
                
        # Remove duplicates and clean titles
        articles = list(dict.fromkeys(articles))  # Remove duplicates
        articles = [self._clean_title(title) for title in articles]
        articles = [a for a in articles if len(a) > 20]  # Filter out short titles
        
        return articles[:5]  # Return top 5 articles

    def _scrape_single_source(self, url: str) -> List[str]:
        """Scrape a single news source"""
        domain = urlparse(url).netloc
        
        # Handle Reddit JSON endpoint
        if 'reddit.com' in domain and url.endswith('.json'):
            return self._scrape_reddit(url)
            
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Handle different content types
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type:
                return self._parse_json_response(response.json(), domain)
            else:
                return self._parse_html_response(response.text, domain)
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {str(e)}")
            return []

    def _parse_html_response(self, html: str, domain: str) -> List[str]:
        """Parse HTML response using BeautifulSoup"""
        articles = []
        soup = BeautifulSoup(html, 'html.parser')
        
        if domain in self.rules:
            rule = self.rules[domain]
            articles_elements = soup.select(rule["article_selector"])
            print(f"Found {len(articles_elements)} elements matching selector for {domain}")
            
            for article in articles_elements[:15]:
                try:
                    title = article.select_one(rule["title_selector"])
                    if title:
                        text = title.get_text(strip=True)
                        if text and len(text) > 20:
                            articles.append(text)
                except Exception as e:
                    print(f"Error parsing article: {str(e)}")
                    continue
        
        print(f"Successfully extracted {len(articles)} articles from {domain}")
        return articles[:10]

    def _scrape_reddit(self, url: str) -> List[str]:
        """Handle Reddit JSON API"""
        articles = []
        response = self.session.get(url, headers={'User-agent': 'Mozilla/5.0'})
        data = response.json()
        
        try:
            posts = data['data']['children']
            now = datetime.utcnow()
            cutoff_time = now - timedelta(days=2)
            
            for post in posts:
                created_utc = datetime.fromtimestamp(post['data']['created_utc'])
                if created_utc > cutoff_time:  # Only include recent posts
                    title = post['data']['title']
                    if not post['data']['stickied'] and len(title) > 20:
                        articles.append(title)
        except KeyError as e:
            print(f"Error parsing Reddit JSON: {str(e)}")
            
        return articles[:10]

    def _clean_title(self, title: str) -> str:
        """Clean and normalize article titles"""
        # Remove extra whitespace
        title = ' '.join(title.split())
        # Remove common prefix/suffix patterns
        prefixes = ['Breaking:', 'BREAKING:', 'Exclusive:', 'Watch:', 'Video:', 'Live Updates:']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        return title

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        # Add your date parsing logic here based on the format of your sources
        # This is a placeholder that should be customized
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            return datetime.utcnow()  # Return current time if parsing fails 