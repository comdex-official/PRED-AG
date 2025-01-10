from typing import Dict

# News source configurations
NEWS_SOURCES = {
    "sports": [
        "https://www.espn.com",
        "https://sports.yahoo.com",
    ],
    "technology": [
        "https://news.ycombinator.com",
        "https://www.reddit.com/r/technology/.json",
        "https://www.bbc.com/news/technology"
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
        "title_selector": "a"
    },
    "www.bbc.com": {
        "article_selector": ".gs-c-promo",
        "title_selector": ".gs-c-promo-heading"
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