def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text

def test_generate_and_fetch_user(client):
    payload = {
        "username": "Test User",
        "user_id": "test-001",
        "age": 20,
        "weight": 60,
        "goal": "general wellness",
        "intensity": "medium",
    }
    response = client.post("/api/generate-workout", json=payload)
    assert response.status_code == 200
    assert response.json()["user"]["user_id"] == "test-001"
    assert "Day 1" in response.json()["workout_plan"]

    response = client.get("/api/users/test-001")
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "Test User"

def test_feedback_update(client):
    payload = {
        "username": "Test User",
        "user_id": "test-002",
        "age": 20,
        "weight": 60,
        "goal": "flexibility",
        "intensity": "low",
    }
    assert client.post("/api/generate-workout", json=payload).status_code == 200
    response = client.post(
        "/api/submit-feedback",
        json={"user_id": "test-002", "feedback": "Add more flexibility and recovery work."},
    )
    assert response.status_code == 200
    assert "Feedback received" in response.json()["workout_plan"]
