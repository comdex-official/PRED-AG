import sqlite3
from sqlalchemy.orm import Session
from models import engine, User, Question

def migrate_from_sqlite():
    """Migrate data from SQLite to PostgreSQL"""
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect('prediction_questions.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Create SQLAlchemy session for PostgreSQL
    pg_session = Session(engine)
    
    try:
        # Migrate users
        sqlite_cursor.execute('SELECT * FROM users')
        users = sqlite_cursor.fetchall()
        for user in users:
            new_user = User(
                id=user[0],
                username=user[1],
                created_at=user[2],
                interests=user[3]
            )
            pg_session.add(new_user)
        
        # Migrate questions
        sqlite_cursor.execute('SELECT * FROM questions')
        questions = sqlite_cursor.fetchall()
        for question in questions:
            new_question = Question(
                id=question[0],
                question_text=question[1],
                interest=question[2],
                source_articles=question[3],
                source_links=question[4],
                created_at=question[5],
                resolved_at=question[6],
                outcome=question[7],
                resolution_note=question[8]
            )
            pg_session.add(new_question)
        
        pg_session.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        pg_session.rollback()
        print(f"Error during migration: {str(e)}")
    finally:
        sqlite_conn.close()
        pg_session.close()

if __name__ == "__main__":
    migrate_from_sqlite() 