from pydantic import BaseModel, Field


class PlannerRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=300)
    available_hours: float = Field(gt=0, le=24)


class Task(BaseModel):
    task: str
    duration_minutes: int = Field(gt=0)
    priority: str


class PlannerResponse(BaseModel):
    tasks: list[Task]
