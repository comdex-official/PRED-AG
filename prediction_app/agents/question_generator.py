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

        # Add common words to filter out from entity extraction
        self.filter_words = {
            # Months
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
            # Days
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            # Common words that might be capitalized
            'The', 'A', 'An', 'And', 'Or', 'But', 'For', 'With', 'In', 'On', 'At',
            'To', 'By', 'From', 'Up', 'Down', 'Over', 'Under'
        }

    def generate_question(self, articles: List[str], interest: str) -> str:
        """Generate a prediction question based on articles and interest"""
        try:
            # Extract and validate entities from articles
            article_entities = self._extract_entities_from_articles(articles)
            validated_entities = [
                entity for entity in article_entities 
                if self._validate_entity_for_interest(entity, interest)
            ]
            
            # Get template and entities for the interest
            templates = self.templates.get(interest, self.templates['sports'])
            entities = self.entities.get(interest, self.entities['sports'])
            
            # Merge article entities with predefined ones
            if validated_entities:
                for entity in validated_entities:
                    if any(entity in v for v in entities.values()):
                        continue  # Skip if already in our lists
                    if interest in ['cricket', 'football', 'sports']:
                        if len(entity.split()) >= 2:  # Prefer full team names
                            entities['team'] = [entity] + entities['team']
                    elif interest == 'technology':
                        if any(suffix in entity for suffix in ['Inc', 'Corp', 'Tech']):
                            entities['company'] = [entity] + entities.get('company', [])
                    elif interest == 'politics':
                        if len(entity.split()) <= 2:  # Names are usually 1-2 words
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
        """Extract named entities from articles with improved filtering"""
        entities = []
        for article in articles:
            words = article.split()
            # Get capitalized words with better filtering
            for word in words:
                if (word[0].isupper() and  # Must start with capital letter
                    len(word) > 1 and      # Must be longer than 1 character
                    word.lower() not in self.filter_words and  # Not in filter list
                    not any(char.isdigit() for char in word) and  # No digits
                    not any(char in '.,!?;:' for char in word)):  # No punctuation
                    entities.append(word)
        
        return list(set(entities))  # Remove duplicates

    def _validate_entity_for_interest(self, entity: str, interest: str) -> bool:
        """Validate if an entity is appropriate for the given interest"""
        # Add specific validation rules for each interest
        if interest == 'cricket':
            invalid_cricket = {'Test', 'ODI', 'T20', 'Series', 'Cup', 'Trophy', 'Match'}
            return entity not in invalid_cricket
        elif interest == 'football':
            invalid_football = {'League', 'Cup', 'FC', 'United', 'City'}
            return not any(word in entity for word in invalid_football)
        elif interest == 'technology':
            tech_indicators = {'Inc', 'Corp', 'Technologies', 'Software', 'Tech'}
            return any(word in entity for word in tech_indicators)
        return True

    def _generate_fallback_question(self, articles: List[str], interest: str) -> str:
        """Generate a simple fallback question"""
        entities = self.entities.get(interest, self.entities['cricket'])
        return f"Will {random.choice(entities['team'])} win tomorrow?" 

    def generate_multiple_questions(self, articles: List[str], interest: str, count: int = 5) -> List[str]:
        """Generate multiple prediction questions based on articles and interest"""
        questions = []
        attempts = 0
        max_attempts = count * 2  # Allow some extra attempts for validation failures
        
        while len(questions) < count and attempts < max_attempts:
            try:
                question = self.generate_question(articles, interest)
                if question not in questions:  # Avoid duplicates
                    questions.append(question)
            except Exception as e:
                print(f"Failed to generate question: {str(e)}")
            attempts += 1
        
        return questions[:count]  # Return exactly count questions 