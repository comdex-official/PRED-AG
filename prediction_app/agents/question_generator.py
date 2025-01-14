from typing import List
from pydantic import BaseModel, Field, validator
import random

class PredictionQuestion(BaseModel):
    """Pydantic model for validating prediction questions"""
    question_text: str = Field(..., min_length=20, max_length=150)
    interest: str
    source_articles: List[str]

    @validator('question_text')
    def validate_question_format(cls, v):
        # Must start with specific words
        if not v.startswith(('Will ', 'Can ')):
            raise ValueError("Question must start with 'Will' or 'Can'")
        
        # Must contain a number
        if not any(char.isdigit() for char in v):
            raise ValueError("Question must contain a number")
        
        # Must contain a time reference
        time_markers = [
            'tomorrow', 'today', 'tonight', 'week',
            'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday', 'weekend'
        ]
        if not any(marker in v.lower() for marker in time_markers):
            raise ValueError("Question must contain a time reference")
        
        # Must contain a capitalized entity
        words = v.split()
        if not any(word[0].isupper() and len(word) > 1 for word in words):
            raise ValueError("Question must contain a named entity")
            
        return v

class QuestionGenerator:
    def __init__(self):  # Remove api_key parameter
        self.templates = {
            'cricket': [
                "Will {team} score {runs} runs against {opponent} {time}?",
                "Can {player} take {wickets} wickets in the match {time}?",
                "Will {team} win by {runs} runs {time}?"
            ],
            'football': [
                "Will {team} score {goals} goals against {opponent} {time}?",
                "Can {player} score in the first {minutes} minutes {time}?",
                "Will {team} win with a {goals}-goal margin {time}?"
            ],
            'technology': [
                "Will {company}'s stock rise by {percent}% {time}?",
                "Can {product} reach {users} million users by {time}?",
                "Will {company} launch {product} {time}?",
                "Can {company} fix {number} major bugs in their {product} {time}?"
            ],
            'sports': [
                "Will {team} win against {opponent} by {points} points {time}?",
                "Can {player} break the {record} record {time}?",
                "Will {team} qualify for {tournament} {time}?"
            ],
            'politics': [
                "Will {politician} win {percent}% votes in {region} {time}?",
                "Can {bill} get {number} votes in parliament {time}?",
                "Will {policy} affect {number} million citizens {time}?",
                "Can {party} form government in {region} {time}?"
            ]
        }
        
        # Entity data for template filling
        self.entities = {
            'cricket': {
                'team': ['India', 'Australia', 'England', 'South Africa'],
                'player': ['Kohli', 'Smith', 'Root', 'Williamson'],
                'runs': [200, 250, 300, 350],
                'wickets': [3, 4, 5, 6],
                'opponent': ['Pakistan', 'New Zealand', 'West Indies', 'Sri Lanka']
            },
            'football': {
                'team': ['Manchester United', 'Liverpool', 'Barcelona', 'Real Madrid'],
                'player': ['Haaland', 'Mbappe', 'Salah', 'Kane'],
                'goals': [2, 3, 4, 5],
                'minutes': [30, 45, 60],
                'opponent': ['Chelsea', 'Arsenal', 'Bayern Munich', 'PSG']
            },
            'technology': {
                'company': ['Apple', 'Google', 'Microsoft', 'Meta', 'Amazon'],
                'product': ['iPhone', 'Android', 'Windows', 'ChatGPT', 'AWS'],
                'percent': [5, 10, 15, 20, 25],
                'users': [1, 5, 10, 50, 100],
                'number': [10, 20, 50, 100]
            },
            'sports': {
                'team': ['Lakers', 'Warriors', 'Celtics', 'Heat'],
                'player': ['LeBron', 'Curry', 'Djokovic', 'Nadal'],
                'points': [10, 15, 20, 25],
                'tournament': ['Champions League', 'World Cup', 'Olympics', 'Super Bowl'],
                'record': ['scoring', 'assists', 'points', 'championship']
            },
            'politics': {
                'politician': ['Biden', 'Trump', 'Johnson', 'Macron'],
                'party': ['Democrats', 'Republicans', 'Labour', 'Conservative'],
                'region': ['California', 'Texas', 'Florida', 'New York'],
                'bill': ['Healthcare Bill', 'Tax Reform', 'Climate Act', 'Education Bill'],
                'policy': ['Healthcare Reform', 'Tax Policy', 'Climate Policy', 'Immigration Reform'],
                'percent': [30, 40, 50, 60],
                'number': [1, 5, 10, 50]
            }
        }

    def generate_question(self, articles: List[str], interest: str) -> str:
        """Generate a prediction question based on articles and interest"""
        try:
            # Extract entities from articles
            article_entities = self._extract_entities_from_articles(articles)
            
            # Get template and entities for the interest
            templates = self.templates.get(interest, self.templates['sports'])  # Default to sports
            entities = self.entities.get(interest, self.entities['sports'])
            
            # Merge article entities with predefined ones
            if article_entities:
                # Add entities to appropriate categories based on context
                for entity in article_entities:
                    if any(entity in v for v in entities.values()):
                        continue  # Skip if already in our lists
                    if entity.endswith(('Corp', 'Inc', 'Ltd')):
                        entities['company'] = [entity] + entities.get('company', [])
                    else:
                        # Add to most appropriate list based on interest
                        if interest in ['cricket', 'football', 'sports']:
                            entities['team'] = [entity] + entities['team']
                        elif interest == 'technology':
                            entities['company'] = [entity] + entities.get('company', [])
                        elif interest == 'politics':
                            entities['politician'] = [entity] + entities.get('politician', [])
            
            # Generate time reference
            time_refs = ['tomorrow', 'this weekend', 'next Saturday', 'this week']
            time_ref = random.choice(time_refs)
            
            # Fill template with random entities
            template = random.choice(templates)
            question = template.format(
                **{k: random.choice(v) for k, v in entities.items()},
                time=time_ref
            )
            
            # Validate using Pydantic model
            validated_question = PredictionQuestion(
                question_text=question,
                interest=interest,
                source_articles=articles
            )
            
            return validated_question.question_text
            
        except Exception as e:
            print(f"Error generating question: {str(e)}")
            return self._generate_fallback_question(articles, interest)

    def _extract_entities_from_articles(self, articles: List[str]) -> List[str]:
        """Extract named entities from articles"""
        entities = []
        for article in articles:
            words = article.split()
            # Get capitalized words that are likely team/player names
            entities.extend([w for w in words if w[0].isupper() and len(w) > 1])
        return list(set(entities))  # Remove duplicates

    def _generate_fallback_question(self, articles: List[str], interest: str) -> str:
        """Generate a simple fallback question"""
        entities = self.entities.get(interest, self.entities['cricket'])
        return f"Will {random.choice(entities['team'])} win tomorrow?" 