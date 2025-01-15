from prediction_app.database.models import Base, engine

def init_database():
    """Initialize the database by creating all tables"""
    try:
        Base.metadata.create_all(engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")

if __name__ == "__main__":
    init_database() 