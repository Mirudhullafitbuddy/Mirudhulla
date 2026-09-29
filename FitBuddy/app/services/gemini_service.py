import json
from typing import Any
from google import genai
from google.genai import types
from ..config import get_settings

settings = get_settings()

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "days": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "string"},
                    "focus": {"type": "string"},
                    "warmup": {"type": "string"},
                    "main_workout": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "exercise": {"type": "string"},
                                "sets": {"type": "string"},
                                "reps_or_duration": {"type": "string"},
                                "rest": {"type": "string"},
                            },
                            "required": ["exercise", "sets", "reps_or_duration", "rest"],
                        },
                    },
                    "cooldown": {"type": "string"},
                },
                "required": ["day", "focus", "warmup", "main_workout", "cooldown"],
            },
        }
    },
    "required": ["days"],
}

def _client():
    return genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

def _json_text(response: Any) -> dict:
    text = (getattr(response, "text", "") or "").strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def _demo_plan(goal: str, intensity: str) -> str:
    days = [
        ("Day 1", "Full body", "5 minutes easy movement", "Bodyweight squats — 2 sets x 8-12; Wall push-ups — 2 sets x 8-12; Bird-dog — 2 sets x 8 each side", "5 minutes gentle stretching"),
        ("Day 2", "Cardio", "5 minutes easy walk", "Brisk walk — 15-25 minutes at a comfortable pace; Standing mobility — 5 minutes", "5 minutes easy walking"),
        ("Day 3", "Lower body + core", "5 minutes mobility", "Glute bridge — 2 sets x 10; Supported split squat — 2 sets x 6-10 each side; Dead bug — 2 sets x 6-10 each side", "Gentle lower-body stretches"),
        ("Day 4", "Recovery", "Gentle mobility", "Easy walk — 15-20 minutes; Light stretching — 5-10 minutes", "Slow breathing and relaxation"),
        ("Day 5", "Upper body + posture", "5 minutes shoulder mobility", "Wall push-ups — 2 sets x 8-12; Band/towel row — 2 sets x 8-12; Shoulder blade squeezes — 2 sets x 10", "Gentle upper-body stretches"),
        ("Day 6", "Enjoyable movement", "5 minutes easy movement", "Choose a safe activity you enjoy — 20-30 minutes; Core balance — 5 minutes", "5 minutes easy movement"),
        ("Day 7", "Rest + reflection", "None required", "Rest, gentle walking if desired, and reflect on how your body feels", "Relaxation and light mobility"),
    ]
    lines = [
        "DEMO MODE — Gemini API key not configured.",
        f"Goal: {goal} | Intensity: {intensity}",
        "",
    ]
    for day, focus, warm, main, cool in days:
        lines += [day, f"Focus: {focus}", f"Warm-up: {warm}", f"Main: {main}", f"Cooldown: {cool}", ""]
    return "\n".join(lines)

def generate_workout_gemini(username: str, age: int, weight: float, goal: str, intensity: str) -> tuple[str, str]:
    client = _client()
    if not client:
        return _demo_plan(goal, intensity), "demo"

    minor_rule = (
        "The user is under 18. Treat this as general wellness only. Do not prescribe weight-loss "
        "or body-composition targets. Avoid calorie restriction, supplements, extreme exercise, or appearance goals."
        if age < 18 else
        "Keep the plan conservative and wellness-oriented. Do not provide medical treatment or dangerous exercise advice."
    )
    prompt = f'''
Create a safe, age-appropriate 7-day fitness/wellness plan for:
Name: {username}
Age: {age}
Weight: {weight} kg
Goal: {goal}
Preferred intensity: {intensity}

{minor_rule}

Requirements:
- Return ONLY valid JSON matching the requested schema.
- Exactly 7 days.
- Include warm-up, main workout, and cooldown/recovery.
- Use simple exercises and clear sets/reps/duration.
- Include rest/recovery days.
- Never recommend exercising through pain, dangerous challenges, dehydration, fasting, restrictive diets, drugs, or supplements.
- For any pain, injury, illness, or concerning symptom, advise stopping and seeking a qualified adult/health professional.
'''
    response = client.models.generate_content(
        model=settings.gemini_workout_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PLAN_SCHEMA,
            temperature=0.4,
            max_output_tokens=3500,
        ),
    )
    data = _json_text(response)
    text_parts = []
    for item in data["days"]:
        text_parts.append(
            f"{item['day']} — {item['focus']}\n"
            f"Warm-up: {item['warmup']}\n"
            + "\n".join(
                f"- {x['exercise']}: {x['sets']}, {x['reps_or_duration']}, rest {x['rest']}"
                for x in item["main_workout"]
            )
            + f"\nCooldown/Recovery: {item['cooldown']}\n"
        )
    return "\n".join(text_parts), "gemini"

def generate_nutrition_tip_with_flash(goal: str, age: int) -> tuple[str, str]:
    client = _client()
    if not client:
        if age < 18:
            return "Prioritize regular balanced meals, water, fruits/vegetables, and protein-containing foods. Avoid restrictive dieting.", "demo"
        return "Prioritize balanced meals, hydration, protein-containing foods, fruits/vegetables, and adequate recovery.", "demo"

    minor_rule = (
        "For a user under 18, give only general healthy-eating and hydration guidance; do not discuss calorie deficits, dieting, weight loss, supplements, or body composition."
        if age < 18 else
        "Give general nutrition/recovery guidance and avoid medical claims or supplement prescriptions."
    )
    prompt = f"Give one concise nutrition or recovery tip for the goal '{goal}'. {minor_rule} Maximum 80 words."
    response = client.models.generate_content(
        model=settings.gemini_tip_model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=150),
    )
    return (response.text or "").strip(), "gemini"

def update_workout_plan(original_plan: str, feedback: str, goal: str, intensity: str, age: int) -> tuple[str, str]:
    client = _client()
    if not client:
        return (
            original_plan + "\n\nDEMO UPDATE\nFeedback received: " + feedback +
            "\nFor a real AI revision, configure GEMINI_API_KEY.",
            "demo",
        )

    minor_rule = (
        "The user is under 18: keep changes general-wellness focused and never add weight-loss/body-composition targets, calorie restriction, supplements, or extreme exercise."
        if age < 18 else
        "Keep changes conservative and wellness-oriented; do not provide medical treatment."
    )
    prompt = f'''
Revise this 7-day wellness plan according to the user's feedback.

Goal: {goal}
Intensity: {intensity}
Age: {age}
Feedback: {feedback}

{minor_rule}

Original plan:
{original_plan}

Return ONLY valid JSON matching the same 7-day plan schema. Preserve useful parts, make reasonable changes,
include recovery, and never recommend exercising through pain or dangerous behavior.
'''
    response = client.models.generate_content(
        model=settings.gemini_workout_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PLAN_SCHEMA,
            temperature=0.4,
            max_output_tokens=3500,
        ),
    )
    data = _json_text(response)
    text_parts = []
    for item in data["days"]:
        text_parts.append(
            f"{item['day']} — {item['focus']}\n"
            f"Warm-up: {item['warmup']}\n"
            + "\n".join(
                f"- {x['exercise']}: {x['sets']}, {x['reps_or_duration']}, rest {x['rest']}"
                for x in item["main_workout"]
            )
            + f"\nCooldown/Recovery: {item['cooldown']}\n"
        )
    return "\n".join(text_parts), "gemini"
