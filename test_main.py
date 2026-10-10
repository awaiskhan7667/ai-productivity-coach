from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "AI Productivity Coach is running"
    )

def test_planner_rejects_zero_hours():
    response = client.post(
        "/planner",
        json={
            "goal": "Learn FastAPI",
            "available_hours": 0
        }
    )

    assert response.status_code == 422


def test_notes_endpoint():
    response = client.get(
        "/notes",
        params={
            "question": "What do I study in the morning?"
        }
    )

    assert response.status_code == 200
    assert "answer" in response.json()


def test_get_saved_plans():
    response = client.get("/plans")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_agent_endpoint():
    response = client.get(
        "/agent",
        params={
            "question": "What is 25 multiplied by 4? Use the calculator."
        }
    )

    assert response.status_code == 200
    assert "answer" in response.json()