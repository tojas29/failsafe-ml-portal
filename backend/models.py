from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    assessments = relationship("StudentRiskAssessment", back_populates="user")


class StudentRiskAssessment(Base):
    __tablename__ = "student_risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)

#foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    risk_score = Column(Float, nullable=False)
    prediction = Column(String, nullable=False)
    risk_band = Column(String, nullable=True)

    features_payload = Column(JSON, nullable=True)
    shap_analysis = Column(JSON, nullable=True)
    intervention_plan = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="assessments")