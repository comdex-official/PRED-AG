from anthropic import Anthropic
from typing import List

class QuestionGenerator:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def generate_question(self, articles: List[str], interest: str) -> str:
        """Generate a question using Claude based on scraped articles"""
        prompt = self._create_prompt(articles, interest)
        max_attempts = 3  # Limit retries

        for attempt in range(max_attempts):
            try:
                print(f"Attempt {attempt + 1} to generate question...")
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=100
                )
                
                question = response.content[0].text.strip()
                print(f"Generated: {question}")
                
                if self._validate_question(question):
                    return question
                else:
                    print("Question failed validation, retrying...")
                    
            except Exception as e:
                print(f"Error generating question: {str(e)}")
                
        # If all attempts fail, return a fallback question
        return self._generate_fallback_question(articles, interest)

    def _generate_fallback_question(self, articles: List[str], interest: str) -> str:
        """Generate a simple fallback question if main generation fails"""
        if not articles:
            return "Failed to generate question: No articles available"
            
        # Extract a named entity from the first article
        words = articles[0].split()
        named_entities = [w for w in words if w[0].isupper() and len(w) > 1]
        entity = named_entities[0] if named_entities else "team"
        
        # Generate a simple question
        return f"Will {entity} succeed this week?"

    def _create_prompt(self, articles: List[str], interest: str) -> str:
        return f"""
        Based on these headlines:
        {' | '.join(articles[:3])}
        
        Generate ONE short yes/no prediction question that:
        1. Starts with 'Will' or 'Can'
        2. Includes:
           - At least one number
           - A time reference (tomorrow, this week, or specific day)
           - A person, team, or company name
        3. Must be:
           - Under 15 words
           - Clearly measurable
           - About a 50-50 chance
        
        Examples:
        - "Will India score 300 runs tomorrow?"
        - "Can Apple stock rise 5% this week?"
        - "Will Manchester United win by 2 goals on Saturday?"
        
        Return ONLY the question, no other text.
        """

    def _validate_question(self, question: str) -> bool:
        """Validate question quality with more lenient rules"""
        # Check length (between 5 and 20 words)
        words = question.split()
        if not (5 <= len(words) <= 20):
            print("Failed length validation")
            return False
            
        if not question.startswith(('Will ', 'Can ')):
            print("Failed start word validation")
            return False
            
        # Check for numbers
        has_number = any(char.isdigit() for char in question)
        
        # Check for named entities (capitalized words)
        capitalized_words = [w for w in words if w[0].isupper() and len(w) > 1]
        has_entities = len(capitalized_words) >= 1
        
        # Expanded time references
        time_markers = [
            # Days
            'tomorrow', 'today', 'tonight', 'week',
            'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday', 'days', 'next',
            # Months
            'january', 'february', 'march', 'april',
            'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul',
            'aug', 'sep', 'oct', 'nov', 'dec',
            # Ordinals
            '1st', '2nd', '3rd', '4th', '5th',
            '6th', '7th', '8th', '9th', '10th',
            # Other time indicators
            'weekend', 'upcoming', 'following',
            'innings', 'match', 'test', 'game'
        ]
        
        # Case-insensitive time marker check
        question_lower = question.lower()
        has_time = any(marker in question_lower for marker in time_markers)
        
        if not (has_number and has_entities and has_time):
            print(f"Validation details: numbers={has_number}, entities={has_entities}, time={has_time}")
            print(f"Question: {question}")
            
        return has_number and has_entities and has_time 