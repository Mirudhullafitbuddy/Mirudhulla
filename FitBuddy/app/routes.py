from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import User, Plan
from .schemas import UserInput, FeedbackRequest, GenerateResponse, FeedbackResponse, UserResponse
from .services.gemini_service import generate_workout_gemini, generate_nutrition_tip_with_flash, update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()

def user_to_schema(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id, username=user.username, age=user.age,
        weight=user.weight, goal=user.goal, intensity=user.intensity
    )

def find_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id))

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_form(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        data = UserInput(username=username, user_id=user_id, age=age, weight=weight, goal=goal, intensity=intensity)
    except Exception as exc:
        return templates.TemplateResponse(
            request=request, name="index.html",
            context={"error": str(exc), "form": locals()},
            status_code=422,
        )

    user = find_user(db, data.user_id)
    if user:
        for key, value in data.model_dump().items():
            setattr(user, key, value)
    else:
        user = User(**data.model_dump())
        db.add(user)
    db.flush()

    workout, mode = generate_workout_gemini(data.username, data.age, data.weight, data.goal, data.intensity)
    tip, _ = generate_nutrition_tip_with_flash(data.goal, data.age)

    plan = db.scalar(select(Plan).where(Plan.user_id == data.user_id))
    if plan:
        plan.original_plan = workout
        plan.updated_plan = None
        plan.feedback = None
        plan.nutrition_tip = tip
        plan.updated_at = None
    else:
        db.add(Plan(user_id=data.user_id, original_plan=workout, nutrition_tip=tip))
    db.commit()

    return templates.TemplateResponse(
        request=request, name="result.html",
        context={"user": user, "workout_plan": workout, "nutrition_tip": tip, "mode": mode, "message": None},
    )

@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(
    request: Request, user_id: str = Form(...), feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    payload = FeedbackRequest(user_id=user_id, feedback=feedback)
    user = find_user(db, payload.user_id)
    plan = db.scalar(select(Plan).where(Plan.user_id == payload.user_id))
    if not user or not plan:
        raise HTTPException(status_code=404, detail="User or plan not found.")

    updated, mode = update_workout_plan(plan.original_plan, payload.feedback, user.goal, user.intensity, user.age)
    tip, _ = generate_nutrition_tip_with_flash(user.goal, user.age)
    plan.updated_plan = updated
    plan.feedback = payload.feedback
    plan.nutrition_tip = tip
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()

    return templates.TemplateResponse(
        request=request, name="result.html",
        context={"user": user, "workout_plan": updated, "nutrition_tip": tip, "mode": mode,
                 "message": "Your plan was updated from your feedback."},
    )

@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, admin_key: str = "", db: Session = Depends(get_db)):
    if admin_key != settings.admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key.")
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    plans = {p.user_id: p for p in db.scalars(select(Plan)).all()}
    return templates.TemplateResponse(request=request, name="all_users.html", context={"users": users, "plans": plans})

@router.get("/api/users/{user_id}")
def get_user_api(user_id: str, db: Session = Depends(get_db)):
    user = find_user(db, user_id)
    plan = db.scalar(select(Plan).where(Plan.user_id == user_id))
    if not user or not plan:
        raise HTTPException(status_code=404, detail="User or plan not found.")
    return {
        "user": user_to_schema(user),
        "original_plan": plan.original_plan,
        "updated_plan": plan.updated_plan,
        "nutrition_tip": plan.nutrition_tip,
        "feedback": plan.feedback,
    }

@router.post("/api/generate-workout", response_model=GenerateResponse)
def generate_workout_api(payload: UserInput, db: Session = Depends(get_db)):
    user = find_user(db, payload.user_id)
    if user:
        for key, value in payload.model_dump().items():
            setattr(user, key, value)
    else:
        user = User(**payload.model_dump())
        db.add(user)
    db.flush()

    workout, mode = generate_workout_gemini(payload.username, payload.age, payload.weight, payload.goal, payload.intensity)
    tip, _ = generate_nutrition_tip_with_flash(payload.goal, payload.age)

    plan = db.scalar(select(Plan).where(Plan.user_id == payload.user_id))
    if plan:
        plan.original_plan = workout
        plan.updated_plan = None
        plan.feedback = None
        plan.nutrition_tip = tip
    else:
        db.add(Plan(user_id=payload.user_id, original_plan=workout, nutrition_tip=tip))
    db.commit()

    return GenerateResponse(user=user_to_schema(user), workout_plan=workout, nutrition_tip=tip, mode=mode)

@router.post("/api/submit-feedback", response_model=FeedbackResponse)
def submit_feedback_api(payload: FeedbackRequest, db: Session = Depends(get_db)):
    user = find_user(db, payload.user_id)
    plan = db.scalar(select(Plan).where(Plan.user_id == payload.user_id))
    if not user or not plan:
        raise HTTPException(status_code=404, detail="User or plan not found.")

    updated, mode = update_workout_plan(plan.original_plan, payload.feedback, user.goal, user.intensity, user.age)
    tip, _ = generate_nutrition_tip_with_flash(user.goal, user.age)
    plan.updated_plan = updated
    plan.feedback = payload.feedback
    plan.nutrition_tip = tip
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()

    return FeedbackResponse(user=user_to_schema(user), workout_plan=updated, nutrition_tip=tip, mode=mode)
