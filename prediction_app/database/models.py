from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Text,
    Boolean, ForeignKey, Enum, JSON, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from prediction_app.config.loader import get_database_url
import enum

Base = declarative_base()

class ResponseEnum(enum.Enum):
    yes = 'yes'
    no = 'no'
    ignore = 'ignore'

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    interests = Column(JSON, nullable=False, default=[])

    responses = relationship('UserQuestionResponse', backref='user')

    def __repr__(self):
        return f"<User(username='{self.username}')>"

class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    question_text = Column(String, nullable=False)
    interest = Column(String, nullable=False)
    source_articles = Column(JSON, nullable=False, default=[])
    source_links = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    outcome = Column(Boolean, nullable=True)
    resolution_note = Column(String, nullable=True)

    responses = relationship('UserQuestionResponse', backref='question')

    def __repr__(self):
        return f"<Question(interest='{self.interest}', question='{self.question_text[:50]}...')>"

class UserQuestionResponse(Base):
    __tablename__ = 'user_question_responses'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    viewed_at = Column(DateTime, nullable=True)
    answered_at = Column(DateTime, nullable=True)
    response = Column(Enum(ResponseEnum), nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'question_id', name='uq_user_question'),
    )

    def __repr__(self):
        return (
            f"<UserQuestionResponse(user_id={self.user_id}, "
            f"question_id={self.question_id}, response='{self.response}')>"
        )

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