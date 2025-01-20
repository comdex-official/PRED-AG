from fastapi import FastAPI, HTTPException, Header, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Union
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timezone
from enum import Enum
import logging

from prediction_app.database.db_manager import DatabaseManager
from prediction_app.managers.prediction_manager import PredictionManager


app = FastAPI(title="Prediction Questions API")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, username",
        },
        status_code=204,
    )

db_manager = DatabaseManager()

# Pydantic Models
class ResponseEnum(str, Enum):
    YES = "yes"
    NO = "no"
    SKIP = "skip"

class QuestionResponse(BaseModel):
    response: ResponseEnum

class Question(BaseModel):
    id: int
    question: str
    interest: str
    source_articles: List[str]
    created_at: str

class UserInterests(BaseModel):
    interests: List[str]

class QuestionHistoryItem(BaseModel):
    question: str  # The question text
    response: Optional[ResponseEnum] = None
    answered_at: Optional[str] = None
    resolution: Optional[bool] = None  # True/False for correct/incorrect prediction
    resolved_at: Optional[str] = None

class UserInfo(BaseModel):
    user_id: int
    username: str
    interests: List[str]
    responses: List[QuestionHistoryItem]

# Dependencies
def get_user(username: Union[str, None] = Header(default=None)) -> dict:
    """Fetch user from the database using the username from the header."""
    if not username:
        return {"id": None, "interests": []}
    user = db_manager.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_manager(username: str = Header(...)) -> PredictionManager:
    """Fetch the PredictionManager instance."""
    return PredictionManager(username)

# Endpoints

@app.get("/health")
async def root():
    return {"message": "Healthy"}

@app.post("/auth/login/", response_model=dict)
async def login(username: str = Header(...)):
    """Login or register a user."""
    user = db_manager.get_user(username)
    if not user:
        user_id = db_manager.create_user(username, interests=[])
        return {"user_id": user_id, "message": "User created successfully"}
    return {"user_id": user["id"], "message": "User already exists"}

@app.put("/users/interests/", response_model=dict)
async def update_user_interests(interests: UserInterests, user: dict = Depends(get_user)):
    """Update user interests."""
    db_manager.update_user_interests(user_id=user["id"], interests=interests.interests)
    return {"message": "User interests updated"}

QUESTION_CONFIG = {
    "default_count": 5,
    "min_count": 1,
    "max_count": 30
}

@app.get("/questions/", response_model=List[Question])
async def fetch_questions(
    count: int = Query(
        default=QUESTION_CONFIG["default_count"],
        ge=QUESTION_CONFIG["min_count"],
        le=QUESTION_CONFIG["max_count"]
    ),
    username: Optional[str] = Header(default=None),  # Don't make username mandatory
    user: Optional[dict] = Depends(get_user),  # Handle missing username gracefully
    manager: Optional[PredictionManager] = Depends(get_manager),
    search: Optional[str] = None
):
    if not username or not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    interests = user["interests"]
    if not interests:
        raise HTTPException(status_code=400, detail="User has no interests")
    
    # Try to get existing questions first
    questions = []
    try:
        # If search term provided, search across all interests
        if search:
            logging.info(f"Searching questions with term: {search}")
            # Search questions in database first
            searched_questions = db_manager.search_questions(
                search_term=search,
                user_id=user["id"],
                count=count
            )
            if searched_questions:
                questions.extend(searched_questions)
        else:
            print("Searching for unused questions", len(interests), interests[0])
            # Get unused questions for each interest
            for interest in interests:
                unused_questions = db_manager.get_multiple_unused_questions(
                    interest=interest,
                    user_id=user["id"],
                    count=count - len(questions)
                )
                
                # Log the results for debugging
                print(f"Got {len(unused_questions)} unused questions for interest {interest}")
                
                if unused_questions:
                    questions.extend(unused_questions)
                    
                # Break if we have enough questions
                if len(questions) >= count:
                    break
                    
        # logging.info(f"Total unused questions found in DB: {len(questions)}")
            
    except Exception as e:
        logging.error(f"Error getting unused questions: {str(e)}")
        questions = []  # Reset questions on error
    
    # If we don't have enough questions, fetch fresh ones
    if len(questions) < count:
        needed_count = count - len(questions)
        logging.info(f"Fetching {needed_count} fresh questions for user {user['id']}")
        fresh_questions = manager.get_fresh_questions(needed_count)
        logging.info(f"Fresh questions response: {fresh_questions}")
        
        if "error" in fresh_questions:
            error_msg = fresh_questions["error"]
            logging.error(f"Error fetching fresh questions: {error_msg}")
            if not questions:  # Only raise error if we have no questions at all
                raise HTTPException(status_code=400, detail=error_msg)
        else:
            logging.info(f"Successfully retrieved {len(fresh_questions['questions'])} fresh questions")
            # Add fresh questions to the database
            for q in fresh_questions["questions"]:
                question_id = db_manager.create_question(
                    question_text=q["question"],
                    interest=q["interest"],
                    source_articles=q["source_articles"],
                    source_links=q["source_links"]
                )
                questions.append({
                    "id": question_id,
                    "question": q["question"],
                    "interest": q["interest"],
                    "source_articles": q["source_articles"],
                    "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return questions[:count]

@app.patch("/questions/{question_id}/", response_model=dict)
async def update_question_response(
    question_id: int,
    response_data: QuestionResponse,
    user: dict = Depends(get_user)
):
    """Update question response and mark it as viewed."""
    db_manager.mark_question_as_viewed(question_id=question_id, user_id=user["id"])
    db_manager.update_question_response(
        question_id=question_id,
        user_id=user["id"],
        response=response_data.response
    )
    return {"message": "Question response updated"}

@app.get("/questions/history/", response_model=List[QuestionHistoryItem])
async def get_question_history(
    user: dict = Depends(get_user),
    interest: Optional[str] = None
):
    """Fetch the user's question history with their responses and resolutions."""
    history = db_manager.get_user_question_history(user_id=user["id"], interest=interest)
    if not history:
        raise HTTPException(status_code=404, detail="No question history found")
    return history

@app.post("/internal/questions/{question_id}/resolve/", response_model=dict)
async def resolve_question_internal(
    question_id: int,
    result: bool,
    note: Optional[str] = None
):
    """Resolve a question (internal route)."""
    db_manager.resolve_question(question_id, result, note)
    return {"message": "Question resolved successfully"}

@app.get("/user/info/", response_model=UserInfo)
async def get_user_info(
    user: dict = Depends(get_user)
):
    """Get detailed user information including responses."""
    if not user or not user.get("id"):
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's question history
    history = db_manager.get_user_question_history(user_id=user["id"])
    
    return {
        "user_id": user["id"],
        "username": user["username"],
        "interests": user["interests"],
        "responses": history
    }
