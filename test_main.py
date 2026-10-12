
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app, verify_api_key
from database import get_db
from models.planner import PlannerResponse


@pytest.fixture
def client():
    app.dependency_overrides[verify_api_key] = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(verify_api_key, None)

def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "AI Productivity Coach is running"
    )


def test_planner_rejects_zero_hours(client):
    response = client.post(
        "/planner",
        json={
            "goal": "Learn FastAPI",
            "available_hours": 0
        }
    )

    assert response.status_code == 422


@patch("main.search_user_notes")
def test_notes_endpoint(mock_rag, client):
    mock_rag.return_value = "Study Python every morning."

    response = client.get(
        "/notes",
        params={
            "question": "What do I study in the morning?"
        }
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Study Python every morning."

def test_get_saved_plans(client):
    response = client.get("/plans")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

@patch("main.ask_agent")
def test_agent_endpoint(mock_agent, client):
    mock_agent.return_value = "Test answer"

    response = client.get(
        "/agent",
        params={"question": "Make a study plan"}
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Test answer"

def test_update_nonexistent_plan(client):
    response = client.put(
        "/plans/999999",
        json={
            "goal": "Learn AI",
            "available_hours": 3
        }
    )

    assert response.status_code == 404

def test_get_nonexistent_plan(client):
    response = client.get("/plans/999999")

    assert response.status_code == 404

@patch("main.create_plan")
def test_planner_handles_ai_failure(mock_create_plan, client):
    mock_create_plan.side_effect = RuntimeError("AI service unavailable")

    response = client.post(
        "/planner",
        json={
            "goal": "Learn AI",
            "available_hours": 3
        }
    )

    assert response.status_code == 500

@patch("main.create_plan")
def test_failed_planner_does_not_save_plan(mock_create_plan, client):
    mock_create_plan.side_effect = RuntimeError("AI service unavailable")

    response = client.post(
        "/planner",
        json={
            "goal": "Learn AI",
            "available_hours": 3
        }
    )

    assert response.status_code == 500

    plans_response = client.get("/plans")
    assert plans_response.status_code == 200
    assert all(
        plan["goal"] != "Learn AI"
        for plan in plans_response.json()
    )

@patch("main.create_plan")
def test_planner_handles_database_failure(mock_create_plan, client):
    mock_create_plan.return_value = PlannerResponse(tasks=[])

    mock_db = MagicMock()
    mock_db.commit.side_effect = RuntimeError("Database unavailable")

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/planner",
            json={
                "goal": "Learn AI",
                "available_hours": 3
            }
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    mock_db.rollback.assert_called()

@patch("main.create_plan")
def test_planner_rejects_zero_hours_without_calling_ai(
    mock_create_plan, client
):
    response = client.post(
        "/planner",
        json={
            "goal": "Learn AI",
            "available_hours": 0
        }
    )

    assert response.status_code == 422
    mock_create_plan.assert_not_called()


@patch("main.create_plan")
def test_planner_rejects_missing_goal(mock_create_plan, client):
    response = client.post(
        "/planner",
        json={
            "available_hours": 3
        }
    )

    assert response.status_code == 422
    mock_create_plan.assert_not_called()

