from anthropic import Anthropic
from typing import List

class QuestionGenerator:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def generate_question(self, articles: List[str], interest: str) -> str:
        """Generate a question using Claude based on scraped articles"""
        prompt = self._create_prompt(articles, interest)

        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=100
            )
            
            question = response.content[0].text.strip()
            return question if self._validate_question(question) else self.generate_question(articles, interest)
            
        except Exception as e:
            return f"Failed to generate question: {str(e)}"

    def _create_prompt(self, articles: List[str], interest: str) -> str:
        return f"""
        Based on these recent {interest} headlines:
        {' | '.join(articles[:3])}
        
        Create a single yes/no prediction question about {interest} that:
        1. Starts with words like 'Will', 'Can', 'Is', 'Are', 'Does', or 'Has'
        2. Is specific and focused on a clear outcome
        3. Can be definitively answered within 7 days
        4. Is related to the provided headlines
        5. Is a complete, grammatically correct question
        
        Return ONLY the question, without any additional text or context.
        """

    def _validate_question(self, question: str) -> bool:
        """Validate question quality"""
        if len(question) < 20:
            return False
            
        if not question.startswith(('Will ', 'Do ', 'Is ', 'Are ', 'Can ', 'Could ', 'Should ')):
            return False
            
        if not any(char.isupper() for char in question):
            return False
            
        return True 