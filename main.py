from prediction_app.managers.prediction_manager import PredictionManager
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Get username
    username = input("Enter your username: ")
    
    # Initialize the prediction manager with Anthropic API key and username
    manager = PredictionManager(os.getenv('ANTHROPIC_API_KEY'), username)
    
    # Add interests
    print("Adding user interests...")
    #interests = ["technology", "sports", "football", "cricket", "politics"]
    interests = ["cricket"]
    
    # Let user choose interests
    print("\nAvailable interests:")
    for i, interest in enumerate(interests, 1):
        print(f"{i}. {interest}")
    
    choice = input("\nEnter the number of the interest you want to follow (1-5): ")
    try:
        index = int(choice) - 1
        if 0 <= index < len(interests):
            chosen_interest = interests[index]
            manager.add_user_interest(chosen_interest)
            print(f"\nSelected interest: {chosen_interest}")
        else:
            print("Invalid choice. Using default interest: sports")
            manager.add_user_interest("sports")
    except ValueError:
        print("Invalid input. Using default interest: sports")
        manager.add_user_interest("sports")
    
    while True:
        # Get a new question
        print("\nGenerating new question...")
        result = manager.get_fresh_question()
        
        if "error" in result:
            print(f"Error: {result['error']}")
            break
            
        print("\n=== Generated Question ===")
        print(result["question"])
        print(f"(Source: {result['source']})")
        print("\n=== Based on Articles ===")
        for article in result["source_articles"]:
            print(f"- {article}")
            
        # Ask if user wants another question
        choice = input("\nWould you like another question? (y/n): ").lower()
        if choice != 'y':
            break

def show_question_history(manager: PredictionManager):
    """Display question history"""
    print("\n=== Question History ===")
    print("1. View all recent questions")
    print("2. View questions by interest")
    
    choice = input("Enter your choice (1-2): ")
    
    if choice == "1":
        questions = manager.get_question_history()
        for q in questions:
            print(f"\n[{q['created_at']}] {q['interest'].upper()}")
            print(f"Q: {q['question']}")
    elif choice == "2":
        interest = input("Enter interest: ").lower()
        questions = manager.get_question_history(interest)
        for q in questions:
            print(f"\n[{q['created_at']}]")
            print(f"Q: {q['question']}")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()