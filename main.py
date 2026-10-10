from fastapi import FastAPI, HTTPException
from models.planner import PlannerRequest, PlannerResponse
from services.planner import create_plan
from services.rag import search_user_notes
from services.agent import ask_agent
from database import engine, Base
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
import json
from models.plan_db import SavedPlan


app = FastAPI(
    title="AI Productivity Coach"
)
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "AI Productivity Coach is running"
    }


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
def ask_notes(question: str):
    answer = search_user_notes(question)

    return {
        "question": question,
        "answer": answer
    }

@app.get("/agent")
def run_agent(question: str):
    answer = ask_agent(question)

    return {
        "question": question,
        "answer": answer
    }

@app.post("/planner", response_model=PlannerResponse)
def planner(
    request: PlannerRequest,
    db: Session = Depends(get_db)
):
    try:
        plan = create_plan(
            request.goal,
            request.available_hours
        )

        saved_plan = SavedPlan(
            goal=request.goal,
            available_hours=request.available_hours,
            tasks_json=plan.model_dump_json()
        )

        db.add(saved_plan)
        db.commit()
        db.refresh(saved_plan)
        print("Saved plan ID:", saved_plan.id)

        return plan

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
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