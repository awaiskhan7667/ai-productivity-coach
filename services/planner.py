from openai import OpenAI
from config import settings
from models.planner import PlannerResponse

client = OpenAI(
    api_key=settings.openai_api_key
)


def create_plan(goal: str, available_hours: float):

    prompt = f"""
    Create a realistic productivity plan.

    Goal:
    {goal}

    Available hours:
    {available_hours}

    Create tasks that fit within the available hours.
    """

    response = client.responses.parse(
        model="gpt-5-mini",
        input=prompt,
        text_format=PlannerResponse
    )

    total_minutes = sum(
        task.duration_minutes
        for task in response.output_parsed.tasks
    )

    max_minutes = available_hours * 60

    if total_minutes > max_minutes:
        raise ValueError("Generated plan exceeds available time.")

    return response.output_parsed