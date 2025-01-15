import os
from typing import Dict
from .loader import load_config

# Load environment variables first
load_config()

# News source configurations
NEWS_SOURCES = {
    "sports": [
        "https://www.espn.com",
        "https://www.reddit.com/r/sports/hot/.json",
        "https://sports.yahoo.com"
    ],
    "technology": [
        "https://news.ycombinator.com",
        "https://www.reddit.com/r/technology/hot/.json",
        "https://techcrunch.com"
    ],
    "football": [
        "https://www.reddit.com/r/soccer/hot/.json",
        "https://www.goal.com/en",
        "https://www.espn.com/soccer/"
    ],
    "cricket": [
        "https://www.reddit.com/r/Cricket/hot/.json",
        "https://www.espncricinfo.com/latest-cricket-news",
        "https://www.cricbuzz.com/cricket-news"
    ],
    "politics": [
        "https://www.reddit.com/r/politics/hot/.json",
        "https://www.politico.com",
        "https://thehill.com"
    ]
}

# Scraping rules for different websites
SCRAPING_RULES = {
    "www.espn.com": {
        "article_selector": ".headlineStack__list li",
        "title_selector": "a"
    },
    "sports.yahoo.com": {
        "article_selector": "ul.js-stream-content li",
        "title_selector": "h3"
    },
    "news.ycombinator.com": {
        "article_selector": ".titleline",
        "title_selector": "a",
        "date_selector": ".age"
    },
    "www.goal.com": {
        "article_selector": "article.card-type-article",
        "title_selector": "h3"
    },
    "www.espncricinfo.com": {
        "article_selector": ".ds-py-3.ds-px-4",
        "title_selector": "h2 a, h3 a",
        "date_selector": "time"
    },
    "www.cricbuzz.com": {
        "article_selector": ".cb-nws-hdln",
        "title_selector": "a",
        "date_selector": ".cb-nws-time"
    },
    "www.politico.com": {
        "article_selector": ".story-card",
        "title_selector": "h3"
    },
    "thehill.com": {
        "article_selector": ".article-list__item",
        "title_selector": "h1"
    }
}

# Request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

# OpenAI configuration
OPENAI_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 100
}

# Question generation configuration
QUESTION_CONFIG = {
    "default_count": int(os.getenv('DEFAULT_QUESTION_COUNT', '5')),
    "min_count": int(os.getenv('MIN_QUESTION_COUNT', '1')),
    "max_count": int(os.getenv('MAX_QUESTION_COUNT', '10'))
}