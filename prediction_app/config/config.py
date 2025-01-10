from typing import Dict

# News source configurations
NEWS_SOURCES = {
    "sports": [
        "https://www.espn.com",
        "https://sports.yahoo.com",
        "https://www.cbssports.com",
        # Add more sports news sources
    ],
    "technology": [
        "https://techcrunch.com",
        "https://www.theverge.com"  # Adding another reliable source
    ],
    "science": [
        "https://techcrunch.com",
        "https://www.theverge.com"  # Adding another reliable source
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
    "techcrunch.com": {
        "article_selector": "article.post-block",
        "title_selector": "h2.post-block__title a"
    },
    "www.theverge.com": {
        "article_selector": "h2.c-entry-box--compact__title",
        "title_selector": "a"
    },
    # Add more domain-specific rules
}

# Request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# OpenAI configuration
OPENAI_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 100
}