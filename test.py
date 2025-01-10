from prediction_app.managers.prediction_manager import PredictionManager
import os
from dotenv import load_dotenv

# Load OpenAI API key from .env file
load_dotenv()

def test_prediction_system():
    # Initialize manager with your API key
    manager = PredictionManager(os.getenv('OPENAI_API_KEY'))
    
    # Add some test interests
    manager.add_user_interest("technology")
    manager.add_user_interest("sports")
    
    # Get and print a question
    result = manager.get_fresh_question()
    
    print("\n=== Generated Question ===")
    print(result["question"])
    print("\n=== Based on Articles ===")
    for article in result["source_articles"]:
        print(f"- {article}")

if __name__ == "__main__":
    test_prediction_system() 