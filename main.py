from prediction_app.managers.prediction_manager import PredictionManager
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the prediction manager with Anthropic API key
    manager = PredictionManager(os.getenv('ANTHROPIC_API_KEY'))
    
    # Add interests (you can modify these)
    print("Adding user interests...")
    manager.add_user_interest("technology")
    manager.add_user_interest("sports")
    #manager.add_user_interest("Science")

    
    while True:
        # Get a new question
        print("\nGenerating new question...")
        result = manager.get_fresh_question()
        
        if "error" in result:
            print(f"Error: {result['error']}")
            break
            
        print("\n=== Generated Question ===")
        print(result["question"])
        print("\n=== Based on Articles ===")
        for article in result["source_articles"]:
            print(f"- {article}")
            
        # Ask if user wants another question
        choice = input("\nWould you like another question? (y/n): ").lower()
        if choice != 'y':
            break

if __name__ == "__main__":
    main()