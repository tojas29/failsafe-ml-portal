from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_age = Column(Integer)
    absences = Column(Integer)
    studytime = Column(Integer)
    failure_probability = Column(Float)
    at_risk_prediction = Column(Integer)
    suggested_intervention = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)