from fastapi import FastAPI, HTTPException, Depends, Header, Query
from typing import List, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from ..managers.prediction_manager import PredictionManager
from fastapi.middleware.cors import CORSMiddleware
from ..config.config import QUESTION_CONFIG

# Load environment variables
load_dotenv()

app = FastAPI(title="Prediction Questions API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get PredictionManager instance
def get_manager(username: str = Header(..., description="Username for the current user")):
    """Get PredictionManager instance with username from header"""
    return PredictionManager(username)

# Pydantic models for request/response
class User(BaseModel):
    username: str
    interests: List[str] = []

class Question(BaseModel):
    id: int
    question: str
    interest: str
    source_articles: List[str]
    created_at: str
    status: str
    result: Optional[bool] = None
    resolution_note: Optional[str] = None

class QuestionResolution(BaseModel):
    result: str  # "yes" or "no"
    note: Optional[str] = None

@app.post("/users/", response_model=dict)
async def create_user(user: User):
    """Create a new user or return existing user"""
    # Create a temporary manager just for user creation
    manager = PredictionManager(user.username)
    
    # Check if user already exists
    existing_user = manager.db_manager.get_user(user.username)
    if existing_user:
        # Update interests if provided
        if user.interests:
            # Add method to update user interests
            manager.db_manager.update_user_interests(existing_user['id'], user.interests)
        return {
            "user_id": existing_user['id'],
            "message": "User already exists, interests updated if provided",
            "status": "existing"
        }
    
    # Create new user if doesn't exist
    try:
        user_id = manager.db_manager.create_user(user.username, user.interests)
        return {
            "user_id": user_id,
            "message": "User created successfully",
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/questions/fresh/")
async def get_fresh_questions(
    count: int = Query(
        default=QUESTION_CONFIG["default_count"],
        ge=QUESTION_CONFIG["min_count"],
        le=QUESTION_CONFIG["max_count"]
    ),
    manager: PredictionManager = Depends(get_manager)
):
    """Get multiple fresh prediction questions"""
    result = manager.get_fresh_questions(count)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/questions/history/")
async def get_question_history(
    interest: Optional[str] = None,
    manager: PredictionManager = Depends(get_manager)
):
    """Get question history for a user"""
    return manager.get_question_history(interest)

@app.get("/questions/pending/")
async def get_pending_resolutions(manager: PredictionManager = Depends(get_manager)):
    """Get questions pending resolution"""
    return manager.get_pending_resolutions()

@app.post("/questions/{question_id}/resolve/")
async def resolve_question(
    question_id: int,
    resolution: QuestionResolution,
    manager: PredictionManager = Depends(get_manager)
):
    """Resolve a question"""
    try:
        manager.resolve_question(question_id, resolution.result, resolution.note)
        return {"message": "Question resolved successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 