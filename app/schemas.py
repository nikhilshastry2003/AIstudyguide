# Import BaseModel and EmailStr from Pydantic
# BaseModel → lets us define data models that validate inputs/outputs automatically.
# EmailStr → special type that ensures the input is a valid email address.
from pydantic import BaseModel, EmailStr  

# Import typing utilities
# Optional → field may or may not be provided.
# List → represents a list (array) of items.
from typing import Optional, List  


# ---------------------------
# AUTH + CORE APP SCHEMAS
# ---------------------------

# Schema for user registration input
# When a user signs up, they must provide name, email, password.
# FastAPI will validate that email is properly formatted.
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


# Schema for login input
# At login, we only need email + password.
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Schema for chat creation
# A chat is always tied to a session, and the user provides a question.
# Answer will be generated later, so it's not included here.
class ChatCreate(BaseModel):
    session_id: int
    question: str


# Schema for creating a subject
# Each subject belongs to a user.
class SubjectCreate(BaseModel):
    user_id: int
    subject_name: str


# Schema for creating a study session
# Each session belongs to a subject, and has a title.
class SessionCreate(BaseModel):
    subject_id: int
    title: str



# ---------------------------
# PIPELINE SCHEMAS
# ---------------------------

# When user starts a new job in pipeline (submits a prompt),
# this schema validates the incoming request body.
class JobCreate(BaseModel):
    prompt: str
    user_id: int


# This schema defines what we send back when returning job info.
# Matches pipeline.jobs table fields.
class JobResponse(BaseModel):
    job_id: int
    user_id: int
    prompt: str
    status: str


# Schema for sections inside a study guide.
# Each section has a title and content.
class GuideSection(BaseModel):
    title: str
    content: str


# Schema for the final structured study guide we return.
# It includes metadata + structured content.
class GuideResponse(BaseModel):
    guide_id: int
    job_id: int
    overview: str
    sections: List[GuideSection] = []  # default empty list
    estimated_time_hours: Optional[int] = None
    prerequisites: List[str] = []
    extra_tips: List[str] = []
    sources: List[str] = []
    summary: Optional[str] = None  # optional short summary of guide
