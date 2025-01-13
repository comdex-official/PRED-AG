from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

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
    question_text = Column(Text, nullable=False)
    interest = Column(String(50), nullable=False)
    source_articles = Column(Text)  # Stored as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Question(interest='{self.interest}', question='{self.question_text[:50]}...'>"

# Create database engine and session
engine = create_engine('sqlite:///prediction_questions.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine) 