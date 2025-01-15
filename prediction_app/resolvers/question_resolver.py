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
        """Enhanced article analysis using interest-specific NLP"""
        docs = [self.nlp(article) for article in articles]
        question_doc = self.nlp(question)
        interest = self._determine_interest(question)
        
        # Interest-specific analysis
        if interest == 'technology':
            outcome, confidence, evidence = self._analyze_tech_question(
                docs, question, entities
            )
        elif interest == 'politics':
            outcome, confidence, evidence = self._analyze_politics_question(
                docs, question, entities
            )
        elif interest == 'football':
            outcome, confidence, evidence = self._analyze_football_question(
                docs, question, entities
            )
        elif interest == 'cricket':
            outcome, confidence, evidence = self._analyze_cricket_question(
                docs, question, entities
            )
        else:
            # Fall back to generic analysis
            if entities['comparison_type'] == 'more_than':
                outcome, confidence, evidence = self._analyze_comparison(
                    docs, entities['players'], entities['metrics']
                )
            elif entities['comparison_type'] == 'first':
                outcome, confidence, evidence = self._analyze_sequence(
                    docs, entities['players'], entities['metrics']
                )
        
        return {
            'outcome': outcome if confidence >= self.CONFIDENCE_THRESHOLD else None,
            'confidence': confidence,
            'explanation': self._format_evidence(evidence)
        }

    def _analyze_football_question(self, docs, question: str, entities: Dict) -> tuple:
        """Football-specific analysis"""
        # Extract football-specific metrics
        metrics = {
            'goals': r'(?:scored|netted|put away|slotted home)\s*(\d+)\s*goals?',
            'assists': r'(?:assisted|set up|provided)\s*(\d+)\s*(?:goals?|times)',
            'shots': r'(?:had|took|attempted)\s*(\d+)\s*shots?',
            'saves': r'(?:made|recorded|managed)\s*(\d+)\s*saves?'
        }
        
        evidence = []
        stats = {metric: [] for metric in metrics}
        
        for doc in docs:
            for sent in doc.sents:
                sent_lower = sent.text.lower()
                
                # Match all relevant players/teams in sentence
                relevant = any(entity in sent.text for entity in 
                             entities['players'] + entities['teams'])
                
                if relevant:
                    # Extract statistics using patterns
                    for metric, pattern in metrics.items():
                        matches = re.finditer(pattern, sent_lower)
                        for match in matches:
                            value = int(match.group(1))
                            stats[metric].append(value)
                            evidence.append(sent.text)
        
        # Determine outcome based on question type
        if 'goals' in question.lower():
            target = int(entities['values'][0]) if entities['values'] else 0
            achieved = any(v >= target for v in stats['goals'])
            confidence = min(1.0, len(stats['goals']) / 3)
            return achieved, confidence, evidence
        
        return self._analyze_comparison(docs, entities['players'], entities['metrics'])

    def _analyze_cricket_question(self, docs, question: str, entities: Dict) -> tuple:
        """Cricket-specific analysis"""
        # Extract cricket-specific metrics
        metrics = {
            'runs': r'(?:scored|made|hit)\s*(\d+)\s*runs?',
            'wickets': r'(?:took|claimed|grabbed)\s*(\d+)\s*wickets?',
            'centuries': r'(?:scored|hit|completed)\s*(?:a|his|her)\s*(?:century|hundred)',
            'fifties': r'(?:scored|hit|made)\s*(?:a|his|her)\s*(?:fifty|half-century)'
        }
        
        evidence = []
        stats = {metric: [] for metric in metrics}
        achievements = {
            'centuries': 0,
            'fifties': 0
        }
        
        for doc in docs:
            for sent in doc.sents:
                sent_lower = sent.text.lower()
                
                # Match relevant players/teams
                relevant = any(entity in sent.text for entity in 
                             entities['players'] + entities['teams'])
                
                if relevant:
                    # Extract numerical statistics
                    for metric, pattern in metrics.items():
                        if metric in ['runs', 'wickets']:
                            matches = re.finditer(pattern, sent_lower)
                            for match in matches:
                                value = int(match.group(1))
                                stats[metric].append(value)
                                evidence.append(sent.text)
                        else:
                            # Count achievements like centuries/fifties
                            if re.search(pattern, sent_lower):
                                achievements[metric] += 1
                                evidence.append(sent.text)
        
        # Determine outcome based on question type
        if 'century' in question.lower():
            achieved = achievements['centuries'] > 0
            confidence = min(1.0, len(evidence) / 2)
            return achieved, confidence, evidence
        elif 'fifty' in question.lower() or 'half-century' in question.lower():
            achieved = achievements['fifties'] > 0
            confidence = min(1.0, len(evidence) / 2)
            return achieved, confidence, evidence
        
        return self._analyze_comparison(docs, entities['players'], entities['metrics'])

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

    def _determine_interest(self, question: str) -> str:
        """Determine the interest based on question content"""
        keywords = {
            'football': {'goal', 'assist', 'shot', 'save', 'striker', 'midfielder'},
            'cricket': {'run', 'wicket', 'century', 'batting', 'bowling', 'innings'},
            'politics': {'votes', 'bill', 'policy', 'election', 'approval', 'parliament',
                        'congress', 'senate', 'government', 'polling'},
            'technology': {'launch', 'release', 'users', 'download', 'bug', 'feature',
                         'update', 'version', 'app', 'software', 'device', 'product',
                         'startup', 'tech', 'AI', 'cloud', 'platform'}
        }
        
        question_lower = question.lower()
        for interest, words in keywords.items():
            if any(word in question_lower for word in words):
                return interest
        
        return 'general'

    def _analyze_politics_question(self, docs, question: str, entities: Dict) -> tuple:
        """Politics-specific analysis"""
        metrics = {
            'votes': r'(?:received|got|won)\s*(\d+)(?:\s*%|\s*percent)\s*(?:of\s*)?(?:the\s*)?votes?',
            'approval': r'(?:approval|rating)\s*(?:of|at)\s*(\d+)(?:\s*%|\s*percent)',
            'polls': r'polling\s*at\s*(\d+)(?:\s*%|\s*percent)',
            'seats': r'(?:won|secured|got)\s*(\d+)\s*seats?',
            'majority': r'(?:majority|lead)\s*of\s*(\d+)(?:\s*%|\s*percent)?'
        }
        
        evidence = []
        stats = {metric: [] for metric in metrics}
        
        # Additional political outcomes
        bill_status = {
            'passed': 0,
            'failed': 0,
            'pending': 0
        }
        
        for doc in docs:
            for sent in doc.sents:
                sent_lower = sent.text.lower()
                
                # Match relevant politicians/parties
                relevant = any(entity in sent.text for entity in 
                             entities['players'] + entities['teams'])
                
                if relevant:
                    # Extract numerical statistics
                    for metric, pattern in metrics.items():
                        matches = re.finditer(pattern, sent_lower)
                        for match in matches:
                            value = int(match.group(1))
                            stats[metric].append(value)
                            evidence.append(sent.text)
                    
                    # Check for bill/policy outcomes
                    if 'bill' in question.lower() or 'policy' in question.lower():
                        if any(word in sent_lower for word in ['passed', 'approved', 'enacted']):
                            bill_status['passed'] += 1
                            evidence.append(sent.text)
                        elif any(word in sent_lower for word in ['failed', 'rejected', 'defeated']):
                            bill_status['failed'] += 1
                            evidence.append(sent.text)
                        elif any(word in sent_lower for word in ['pending', 'proposed', 'introduced']):
                            bill_status['pending'] += 1
                            evidence.append(sent.text)
        
        # Determine outcome based on question type
        if any(word in question.lower() for word in ['votes', 'polling', 'approval']):
            target = int(entities['values'][0]) if entities['values'] else 0
            relevant_stats = stats['votes'] + stats['approval'] + stats['polls']
            if relevant_stats:
                achieved = any(v >= target for v in relevant_stats)
                confidence = min(1.0, len(relevant_stats) / 3)
                return achieved, confidence, evidence
        
        elif 'bill' in question.lower() or 'policy' in question.lower():
            if bill_status['passed'] > bill_status['failed']:
                return True, min(1.0, bill_status['passed'] / 2), evidence
            elif bill_status['failed'] > 0:
                return False, min(1.0, bill_status['failed'] / 2), evidence
        
        return self._analyze_comparison(docs, entities['players'], entities['metrics']) 

    def _analyze_tech_question(self, docs, question: str, entities: Dict) -> tuple:
        """Technology-specific analysis"""
        metrics = {
            'users': r'(?:reached|achieved|hit)\s*(\d+)(?:\s*million|\s*k|\s*M)?\s*(?:users|customers|downloads)',
            'revenue': r'(?:revenue|sales)\s*of\s*\$?(\d+)(?:\s*million|\s*M|\s*B)?',
            'growth': r'(?:grew|increased|up)\s*(?:by\s*)?(\d+)(?:\s*%|\s*percent)',
            'market_share': r'(?:market share|share)\s*of\s*(\d+)(?:\s*%|\s*percent)',
            'bugs': r'(?:fixed|resolved|patched)\s*(\d+)\s*(?:bugs|issues|defects)'
        }
        
        # Product launch indicators
        launch_status = {
            'announced': 0,
            'released': 0,
            'delayed': 0,
            'cancelled': 0
        }
        
        evidence = []
        stats = {metric: [] for metric in metrics}
        
        for doc in docs:
            for sent in doc.sents:
                sent_lower = sent.text.lower()
                
                # Match relevant companies/products
                relevant = any(entity in sent.text for entity in 
                             entities['players'] + entities['teams'])
                
                if relevant:
                    # Extract numerical metrics
                    for metric, pattern in metrics.items():
                        matches = re.finditer(pattern, sent_lower)
                        for match in matches:
                            try:
                                value = int(match.group(1))
                                # Handle million/billion multipliers
                                if 'million' in sent_lower or 'M' in sent.text:
                                    value *= 1_000_000
                                elif 'B' in sent.text:
                                    value *= 1_000_000_000
                                elif 'k' in sent_lower:
                                    value *= 1_000
                                stats[metric].append(value)
                                evidence.append(sent.text)
                            except ValueError:
                                continue
                    
                    # Check for product launches
                    if 'launch' in question.lower() or 'release' in question.lower():
                        if any(word in sent_lower for word in ['announced', 'unveiled', 'revealed']):
                            launch_status['announced'] += 1
                            evidence.append(sent.text)
                        elif any(word in sent_lower for word in ['launched', 'released', 'available']):
                            launch_status['released'] += 1
                            evidence.append(sent.text)
                        elif any(word in sent_lower for word in ['delayed', 'postponed']):
                            launch_status['delayed'] += 1
                            evidence.append(sent.text)
                        elif any(word in sent_lower for word in ['cancelled', 'scrapped']):
                            launch_status['cancelled'] += 1
                            evidence.append(sent.text)
        
        # Determine outcome based on question type
        if any(word in question.lower() for word in ['users', 'customers', 'downloads']):
            target = int(entities['values'][0]) if entities['values'] else 0
            if stats['users']:
                achieved = any(v >= target for v in stats['users'])
                confidence = min(1.0, len(stats['users']) / 2)
                return achieved, confidence, evidence
        
        elif 'launch' in question.lower() or 'release' in question.lower():
            if launch_status['cancelled'] > 0:
                return False, 1.0, evidence
            elif launch_status['released'] > 0:
                return True, 1.0, evidence
            elif launch_status['delayed'] > 0:
                return False, min(1.0, launch_status['delayed'] / 2), evidence
            elif launch_status['announced'] > 0:
                return True, 0.7, evidence
        
        elif 'bugs' in question.lower() or 'issues' in question.lower():
            target = int(entities['values'][0]) if entities['values'] else 0
            if stats['bugs']:
                achieved = any(v >= target for v in stats['bugs'])
                confidence = min(1.0, len(stats['bugs']) / 2)
                return achieved, confidence, evidence
        
        return self._analyze_comparison(docs, entities['players'], entities['metrics']) 