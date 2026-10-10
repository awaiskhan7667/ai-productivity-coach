from sqlalchemy import Column, Integer, String, Float, Text
from database import Base


class SavedPlan(Base):
    __tablename__ = "saved_plans"

    id = Column(Integer, primary_key=True, index=True)
    goal = Column(String, nullable=False)
    available_hours = Column(Float, nullable=False)
    tasks_json = Column(Text, nullable=False)