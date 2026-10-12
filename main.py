from fastapi import FastAPI, HTTPException, Request, Query, Depends, Security
import secrets
from fastapi.security import APIKeyHeader
from config import settings
from models.planner import PlannerRequest, PlannerResponse
from services.planner import create_plan
from services.rag import search_user_notes
from services.agent import ask_agent
from database import engine, Base
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import json
import logging
import time
from models.plan_db import SavedPlan


app = FastAPI(
    title="AI Productivity Coach"
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = round(time.time() - start_time, 3)

    logger.info(
        "%s %s - Status: %s - Duration: %ss",
        request.method,
        request.url.path,
        response.status_code,
        duration
    )

    return response


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


api_key_header = APIKeyHeader(
    name="API-Key",
    auto_error=False
)

def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or not secrets.compare_digest(
        api_key, settings.app_api_key
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )


Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
def home():
    return {
        "message": "AI Productivity Coach is running"
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )

# @app.post(
#     "/planner",
#     response_model=PlannerResponse
# )
# def planner(request: PlannerRequest):
    
#     try:
#         return create_plan(
#             request.goal,
#             request.available_hours
#         )

#     except ValueError as e:
#         raise HTTPException(
#             status_code=400,
#             detail=str(e)
#         )


@app.get("/notes")
@limiter.limit("10/minute")
def ask_notes(request: Request, question: str = Query(min_length=1), 
              _: None = Depends(verify_api_key)):
    answer = search_user_notes(question)

    return {
        "question": question,
        "answer": answer
    }



@app.get("/agent")
@limiter.limit("10/minute")
def run_agent(request: Request, question: str = Query(min_length=1),  
              _: None = Depends(verify_api_key)):
    try:
        answer = ask_agent(question)
        return {
            "question": question,
            "answer": answer
        }
    except Exception:
        logger.exception("AI agent request failed")
        raise HTTPException(
            status_code=500,
            detail="The AI service failed. Please try again."
        )

@app.post("/planner", response_model=PlannerResponse)
@limiter.limit("5/minute")
def planner(
    request: Request,
    planner_request: PlannerRequest,
    db: Session = Depends(get_db),
        _: None = Depends(verify_api_key)
):
    try:
        plan = create_plan(
            planner_request.goal,
            planner_request.available_hours
        )

        saved_plan = SavedPlan(
            goal=planner_request.goal,
            available_hours=planner_request.available_hours,
            tasks_json=plan.model_dump_json()
        )

        
        db.add(saved_plan)
        db.commit()
        db.refresh(saved_plan)

        return plan

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:
        db.rollback()
        logger.exception("Planner request failed")
        raise HTTPException(
            status_code=500,
            detail="The planner service failed. Please try again."
        )

@app.get("/plans")
def get_saved_plans(db: Session = Depends(get_db)):
    plans = db.query(SavedPlan).all()

    return [
        {
            "id": plan.id,
            "goal": plan.goal,
            "available_hours": plan.available_hours,
            "tasks": json.loads(plan.tasks_json)["tasks"]
        }
        for plan in plans
    ]

@app.get("/plans/{plan_id}")
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    plan = (
        db.query(SavedPlan)
        .filter(SavedPlan.id == plan_id)
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    return {
        "id": plan.id,
        "goal": plan.goal,
        "available_hours": plan.available_hours,
        "tasks": json.loads(plan.tasks_json)["tasks"]
    }

@app.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    plan = (
        db.query(SavedPlan)
        .filter(SavedPlan.id == plan_id)
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    db.delete(plan)
    db.commit()

    return {
        "message": "Plan deleted successfully",
        "id": plan_id
    }

@app.put("/plans/{plan_id}")
def update_plan(
    plan_id: int,
    request: PlannerRequest,
    db: Session = Depends(get_db)
):
    plan = (
        db.query(SavedPlan)
        .filter(SavedPlan.id == plan_id)
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    plan.goal = request.goal
    plan.available_hours = request.available_hours

    db.commit()
    db.refresh(plan)

    return {
        "message": "Plan updated successfully",
        "id": plan.id,
        "goal": plan.goal,
        "available_hours": plan.available_hours
    }