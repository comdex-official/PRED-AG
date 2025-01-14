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
    interests = ["football"]
    
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
        print("\n=== Menu ===")
        print("1. Get new prediction question")
        print("2. View question history")
        print("3. Resolve pending questions")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
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
        elif choice == "2":
            show_question_history(manager)
        elif choice == "3":
            resolve_questions(manager)
        elif choice == "4":
            break
        else:
            print("Invalid choice")

def show_question_history(manager: PredictionManager):
    """Display question history"""
    print("\n=== Question History ===")
    print("1. View all recent questions")
    print("2. View questions by interest")
    
    choice = input("Enter your choice (1-2): ")
    
    if choice == "1":
        questions = manager.get_question_history()
        for q in questions:
            print(f"\n[{q['viewed_at']}] {q['interest'].upper()}")
            print(f"Q: {q['question']}")
            if q['status'] == 'resolved':
                result = "Yes" if q['result'] else "No"
                print(f"Result: {result}")
                if q['resolution_note']:
                    print(f"Note: {q['resolution_note']}")
    elif choice == "2":
        interest = input("Enter interest: ").lower()
        questions = manager.get_question_history(interest)
        for q in questions:
            print(f"\n[{q['viewed_at']}]")
            print(f"Q: {q['question']}")
            if q['status'] == 'resolved':
                result = "Yes" if q['result'] else "No"
                print(f"Result: {result}")
                if q['resolution_note']:
                    print(f"Note: {q['resolution_note']}")
    else:
        print("Invalid choice")

def resolve_questions(manager: PredictionManager):
    """Handle resolution of pending questions"""
    pending = manager.get_pending_resolutions()
    
    if not pending:
        print("\nNo questions pending resolution.")
        return
        
    print("\n=== Questions Pending Resolution ===")
    for i, q in enumerate(pending, 1):
        print(f"\n{i}. Question: {q['question']}")
        print(f"   Created: {q['created_at']}")
        print(f"   Due: {q['resolution_date']}")
    
    while True:
        try:
            choice = int(input("\nEnter question number to resolve (0 to exit): "))
            if choice == 0:
                break
            if 1 <= choice <= len(pending):
                q = pending[choice-1]
                result = input("Was the prediction correct? (yes/no): ").lower()
                if result in ['yes', 'no']:
                    note = input("Add a note (optional): ")
                    manager.resolve_question(q['id'], result, note)
                    print("Question resolved!")
                else:
                    print("Invalid input. Please enter 'yes' or 'no'")
            else:
                print("Invalid question number")
        except ValueError:
            print("Invalid input. Please enter a number")

if __name__ == "__main__":
    main()