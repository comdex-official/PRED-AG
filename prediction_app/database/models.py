from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from prediction_app.config.loader import get_database_url

Base = declarative_base()

# Association table for User-Question relationship
user_questions = Table('user_questions', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('question_id', Integer, ForeignKey('questions.id')),
    Column('viewed_at', DateTime, default=datetime.utcnow)
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    interests = Column(Text)  # Stored as JSON string
    viewed_questions = relationship('Question', 
                                  secondary=user_questions,
                                  backref='viewed_by')

    def __repr__(self):
        return f"<User(username='{self.username}'>"

class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    question_text = Column(String, nullable=False)
    interest = Column(String, nullable=False)
    source_articles = Column(String, nullable=False)  # JSON string of article URLs
    source_links = Column(String, nullable=False)  # JSON string of source links
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    outcome = Column(Boolean, nullable=True)
    resolution_note = Column(String, nullable=True)

    def __repr__(self):
        return f"<Question(interest='{self.interest}', question='{self.question_text[:50]}...'>"

# Create database engine with error handling
try:
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
except Exception as e:
    sqlite_url = "sqlite:///prediction_questions.db"
    engine = create_engine(sqlite_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine) 