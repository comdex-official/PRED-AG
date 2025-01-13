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
        
        Generate ONE creative yes/no prediction question that:
        1. Must start with 'Will', 'Can', 'Is', 'Are', 'Does', 'Has', or 'Could'
        2. Should be highly specific (include names, numbers, dates, or measurable outcomes)
        3. Must be definitively answerable within exactly 7 days
        4. Should directly relate to one of the provided headlines
        5. Must avoid obvious or generic predictions
        6. Should focus on an interesting or unexpected aspect of the story
        7. Must be phrased in a way that creates genuine uncertainty about the outcome
        
        Bad example: "Will Apple release new products this year?"
        Good example: "Will Apple's new Vision Pro headset sell more than 100,000 units in its first week of release?"
        
        Return ONLY the question, with no additional text, explanation, or context.
        """

    def _validate_question(self, question: str) -> bool:
        """Validate question quality"""
        if len(question) < 30:  # Increased minimum length to encourage more specific questions
            return False
            
        if not question.startswith(('Will ', 'Do ', 'Is ', 'Are ', 'Can ', 'Could ', 'Has ', 'Does ')):
            return False
            
        if not any(char.isupper() for char in question):
            return False
            
        # Check for specificity indicators
        specificity_markers = ['%', '$', '#', 
                             'million', 'billion', 
                             'next week', 'within', 'by',
                             'more than', 'less than',
                             'at least', 'first', 'new']
        if not any(marker in question.lower() for marker in specificity_markers):
            return False
            
        return True 