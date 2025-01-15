import schedule
import time
from .resolvers.question_resolver import QuestionResolver

def run_resolver():
    resolver = QuestionResolver()
    resolved = resolver.resolve_pending_questions()
    print(f"Resolved {resolved} questions")

def start_scheduler():
    # Run resolver every hour
    schedule.every(1).hour.do(run_resolver)
    
    while True:
        schedule.run_pending()
        time.sleep(60) 