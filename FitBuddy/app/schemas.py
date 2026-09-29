from typing import Literal
from pydantic import BaseModel, Field, field_validator

Goal = Literal["weight loss", "muscle gain", "general wellness", "flexibility"]
Intensity = Literal["low", "medium", "high"]

class UserInput(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    user_id: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, lt=300)
    goal: Goal
    intensity: Intensity

    @field_validator("username", "user_id")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=100)
    feedback: str = Field(min_length=3, max_length=1000)

class UserResponse(BaseModel):
    user_id: str
    username: str
    age: int
    weight: float
    goal: str
    intensity: str

class GenerateResponse(BaseModel):
    user: UserResponse
    workout_plan: str
    nutrition_tip: str
    mode: str

class FeedbackResponse(BaseModel):
    user: UserResponse
    workout_plan: str
    nutrition_tip: str
    mode: str
