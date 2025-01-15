from datetime import datetime, timedelta
import requests
from typing import List, Dict
import json
import spacy
import re
from ..database.db_manager import DatabaseManager
from ..config.config import RESOLVER_CONFIG
import os

class QuestionResolver:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.news_api_key = os.getenv('NEWS_API_KEY', '')
        # Load English language model
        self.nlp = spacy.load("en_core_web_sm")
        
        # Confidence thresholds
        self.CONFIDENCE_THRESHOLD = RESOLVER_CONFIG['confidence_threshold']
        self.MIN_ARTICLES = RESOLVER_CONFIG['min_articles']
        
    def resolve_pending_questions(self):
        """Automatically resolve questions that are due"""
        pending = self.db_manager.get_pending_resolutions()
        resolved_count = 0
        
        for question in pending:
            try:
                result = self._determine_result(question)
                if result is not None:
                    self.db_manager.resolve_question(
                        question['id'],
                        result['outcome'],
                        result['note']
                    )
                    resolved_count += 1
            except Exception as e:
                print(f"Error resolving question {question['id']}: {str(e)}")
                
        return resolved_count

    def _determine_result(self, question: Dict) -> Dict:
        """Determine the result of a question based on news articles"""
        # Extract key entities and metrics from question
        entities = self._extract_entities(question['question'])
        
        # Search news articles for results
        articles = self._search_news(entities)
        
        if not articles:
            return None
            
        # Analyze articles to determine outcome
        result = self._analyze_articles(articles, question['question'], entities)
        
        return {
            'outcome': result['outcome'],
            'note': f"Based on {len(articles)} news articles. {result['explanation']}"
        }

    def _extract_entities(self, question: str) -> Dict:
        """Extract entities using spaCy NLP"""
        doc = self.nlp(question)
        
        entities = {
            'teams': [],
            'players': [],
            'metrics': set(),
            'values': [],
            'comparison_type': None,
            'time_reference': None
        }
        
        # Extract numerical values
        entities['values'] = [token.text for token in doc if token.like_num]
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PERSON']:
                if any(team_indicator in ent.text for team_indicator in ['FC', 'United', 'City']):
                    entities['teams'].append(ent.text)
                else:
                    entities['players'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['time_reference'] = ent.text
        
        # Extract metrics and comparison type
        metrics_patterns = {
            'goals': r'goals?|scor(e|ing)',
            'assists': r'assists?',
            'wickets': r'wickets?',
            'runs': r'runs?',
            'points': r'points?'
        }
        
        for metric, pattern in metrics_patterns.items():
            if re.search(pattern, question.lower()):
                entities['metrics'].add(metric)
        
        # Determine comparison type
        comparison_patterns = {
            'more_than': r'more than|higher than|better than',
            'first': r'first|before|earlier',
            'both': r'both|and.*will',
            'exact': r'exactly|precisely'
        }
        
        for comp_type, pattern in comparison_patterns.items():
            if re.search(pattern, question.lower()):
                entities['comparison_type'] = comp_type
                break
        
        return entities

    def _search_news(self, entities: Dict) -> List[str]:
        """Search news articles for relevant results"""
        if not self.news_api_key:
            return []
            
        query = ' OR '.join(entities['players'] + entities['teams'])
        
        url = f"https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d'),
            'sortBy': 'publishedAt',
            'apiKey': self.news_api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            return [article['description'] for article in data.get('articles', [])]
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            return []

    def _analyze_articles(self, articles: List[str], question: str, entities: Dict) -> Dict:
        """Enhanced article analysis using NLP"""
        docs = [self.nlp(article) for article in articles]
        question_doc = self.nlp(question)
        
        confidence = 0.0
        outcome = False
        evidence = []
        
        # Different analysis strategies based on question type
        if entities['comparison_type'] == 'more_than':
            outcome, confidence, evidence = self._analyze_comparison(
                docs, entities['players'], entities['metrics']
            )
        elif entities['comparison_type'] == 'first':
            outcome, confidence, evidence = self._analyze_sequence(
                docs, entities['players'], entities['metrics']
            )
        elif entities['comparison_type'] == 'both':
            outcome, confidence, evidence = self._analyze_multiple_achievements(
                docs, entities['players'], entities['metrics']
            )
        else:
            outcome, confidence, evidence = self._analyze_single_achievement(
                docs, entities['players'], entities['teams'], 
                entities['metrics'], entities['values']
            )
        
        return {
            'outcome': outcome if confidence >= self.CONFIDENCE_THRESHOLD else None,
            'confidence': confidence,
            'explanation': self._format_evidence(evidence)
        }

    def _analyze_comparison(self, docs, players, metrics) -> tuple:
        """Analyze comparative questions"""
        if len(players) < 2:
            return False, 0.0, []
        
        player1, player2 = players[:2]
        evidence = []
        scores = {player1: 0, player2: 0}
        
        for doc in docs:
            # Look for sentences mentioning both players
            for sent in doc.sents:
                if player1 in sent.text and player2 in sent.text:
                    # Analyze sentiment and achievement mentions
                    for metric in metrics:
                        pattern = f"{metric}|score|achieve"
                        if re.search(pattern, sent.text.lower()):
                            # Use sentiment analysis to determine who performed better
                            for name, score in self._analyze_sentence_sentiment(sent, [player1, player2]):
                                scores[name] += score
                            evidence.append(sent.text)
        
        total_mentions = sum(scores.values())
        if total_mentions == 0:
            return False, 0.0, evidence
            
        confidence = min(1.0, total_mentions / 5)  # Scale confidence with mentions
        outcome = scores[player1] > scores[player2]
        
        return outcome, confidence, evidence

    def _analyze_sentence_sentiment(self, sent, entities) -> List[tuple]:
        """Analyze sentiment in relation to specific entities"""
        results = []
        doc = sent.doc
        
        for entity in entities:
            # Find entity mentions
            mentions = [token for token in sent if entity.lower() in token.text.lower()]
            if not mentions:
                continue
                
            # Calculate sentiment score based on surrounding words
            sentiment_score = 0
            for mention in mentions:
                # Look at words around the mention
                window = 5  # words before and after
                start = max(0, mention.i - window)
                end = min(len(doc), mention.i + window + 1)
                
                for token in doc[start:end]:
                    # Use spaCy's built-in sentiment analysis
                    if token._.sentiment != 0:  # You might need to install a sentiment model
                        sentiment_score += token._.sentiment
                    
                    # Look for positive/negative achievement words
                    if token.text.lower() in RESOLVER_CONFIG['positive_words']:
                        sentiment_score += 1
                    elif token.text.lower() in RESOLVER_CONFIG['negative_words']:
                        sentiment_score -= 1
            
            results.append((entity, sentiment_score))
        
        return results

    def _format_evidence(self, evidence: List[str]) -> str:
        """Format evidence into a readable explanation"""
        if not evidence:
            return "No conclusive evidence found."
            
        # Deduplicate and limit evidence
        unique_evidence = list(set(evidence))[:3]  # Show top 3 pieces of evidence
        
        formatted = "Evidence:\n"
        for i, e in enumerate(unique_evidence, 1):
            formatted += f"{i}. {e}\n"
            
        return formatted 