# FitBuddy – AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite application that generates a structured 7-day wellness/workout plan and a concise nutrition/recovery tip with Google's Gemini API. Users can submit feedback to regenerate a plan, and a local admin dashboard can inspect stored records.

## Implementation note

The supplied project document describes the older `google-generativeai` package and Gemini 1.5 Pro/Flash. Google's current documentation recommends the newer `google-genai` SDK. This implementation therefore uses `google-genai` and configurable model names so the project remains maintainable.

The app also includes a safe fallback mode: if `GEMINI_API_KEY` is empty, it generates a clearly labeled local demo plan instead of crashing.

## Features

- Home page for name, user ID, age, weight, goal and intensity
- AI-generated 7-day plan
- AI nutrition/recovery tip
- Feedback-based plan revision
- SQLite persistence with SQLAlchemy
- Admin dashboard
- JSON REST API
- Swagger/OpenAPI docs at `/docs`
- Health endpoint at `/health`
- Automated tests
- Responsive frontend
- Environment-variable configuration

## Project structure

```text
FitBuddy/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes.py
│   └── services/
│       ├── __init__.py
│       └── gemini_service.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   └── all_users.html
├── static/
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   ├── conftest.py
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## VS Code setup

### 1. Open the project

Extract the ZIP and open the `FitBuddy` folder in VS Code.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Gemini

Copy `.env.example` to `.env` and set `GEMINI_API_KEY=your_key_here`.

You can leave it empty for local demo/fallback mode.

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`, `/docs`, and `/health`.

The local admin page is:
`/view-all-users?admin_key=change-this-for-local-admin`

## Testing

```bash
pytest -q
```

The tests use a temporary SQLite database and do not require a Gemini API key.

## API

`POST /api/generate-workout`

```json
{
  "username": "Demo User",
  "user_id": "demo-001",
  "age": 20,
  "weight": 60,
  "goal": "general wellness",
  "intensity": "medium"
}
```

`POST /api/submit-feedback`

```json
{
  "user_id": "demo-001",
  "feedback": "Include more flexibility and recovery work."
}
```

`GET /api/users/{user_id}` returns the stored user and plan.

## Safety behavior

FitBuddy is a wellness-planning demo, not a medical diagnostic or treatment system. The AI prompt asks for age-appropriate, conservative recommendations and avoids dangerous challenges, extreme exercise, restrictive eating, supplements/drugs, or medical claims.

For users under 18, the app treats the request as general wellness rather than weight-loss/body-composition coaching. For pain, injury, illness, or other health concerns, users should stop and involve a parent/guardian and qualified health professional.

## Admin note

The dashboard uses an `ADMIN_KEY` query parameter because the supplied specification only asks for a local admin/coach view. Do not deploy this dashboard publicly without real authentication and authorization.
