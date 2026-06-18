import os
import joblib
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 1. Cloud Database Connection Setup (Using your Supabase Pooler)
DATABASE_URL = "postgresql://postgres.vsfqobrpybnergybcale:Arnavojas2911@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Cryptography Configuration
SECRET_KEY = "SUPER_SECRET_FAILSAFE_TOKEN_SIGNING_KEY_CHOOSE_A_RANDOM_HASH_FOR_PROD"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# 3. Relational Database Schemas
class UserTable(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)

class AssessmentTable(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    features_payload = Column(JSON, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_band = Column(String, nullable=False)
    prediction = Column(String, nullable=False)
    shap_analysis = Column(JSON, nullable=False)

Base.metadata.create_all(bind=engine)

# 4. Model Binary Loader
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "failsafe_model.pkl")
CONFIG_PATH = os.path.join(BASE_DIR, "models", "threshold_config.json")

try:
    model = joblib.load(MODEL_PATH)
    with open(CONFIG_PATH, "r") as f:
        threshold_config = json.load(f)
    classification_threshold = threshold_config.get("classification_threshold", 0.5)
    print(f"✅ XGBoost Core Operational. Classification Threshold: {classification_threshold}")
except Exception as e:
    print(f"⚠️ Model startup delay: {e}")
    model, classification_threshold = None, 0.5

# 5. Data Validation Specs
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    user_email: str

class StudentAssessmentInput(BaseModel):
    student_id: str
    G1: int; G2: int; absences: int; failures: int; studytime: int
    traveltime: int; famrel: int; freetime: int; goout: int; Dalc: int
    Walc: int; health: int; schoolsup: int; famsup: int; paid: int
    activities: int; higher: int; internet: int; romantic: int
    Medu: int; Fedu: int

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    exception = HTTPException(status_code=401, detail="Session expired or invalid.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise exception
    except JWTError:
        raise exception
    user = db.query(UserTable).filter(UserTable.email == email).first()
    if user is None: raise exception
    return user

# 6. Auth Gateways
@app.post("/auth/register", response_model=Token)
async def register_faculty(user_in: UserRegister, db: Session = Depends(get_db)):
    if db.query(UserTable).filter(UserTable.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already split registered.")
    hashed_pwd = pwd_context.hash(user_in.password)
    new_user = UserTable(email=user_in.email, hashed_password=hashed_pwd, name=user_in.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = jwt.encode({"sub": new_user.email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user_name": new_user.name, "user_email": new_user.email}

@app.post("/auth/login", response_model=Token)
async def login_faculty(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserTable).filter(UserTable.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credential parameters.")
    token = jwt.encode({"sub": user.email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user_name": user.name, "user_email": user.email}

# 7. Lightning Fast Instant Prediction Channel
@app.post("/predict")
async def assess_student(payload: StudentAssessmentInput, current_user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)):
    if model is None:
        raise HTTPException(status_code=503, detail="Model assets compiling.")

    feature_names = [
        'G1', 'G2', 'failures', 'studytime', 'absences',
        'traveltime', 'famrel', 'freetime', 'goout', 'Dalc', 'Walc', 'health',
        'Medu', 'Fedu', 'schoolsup', 'famsup', 'paid', 'activities', 'higher', 'internet', 'romantic'
    ]
    
    raw_dict = payload.dict()
    ordered_values = [raw_dict[feat] for feat in feature_names]
    input_df = pd.DataFrame([ordered_values], columns=feature_names)
    
    # Run structural tree tracking
    prob_raw = float(model.predict_proba(input_df)[0][1])
    risk_score = round(prob_raw * 100, 2)
    pred_status = "AT-RISK" if prob_raw >= classification_threshold else "SECURE"
    risk_band = "LOW" if risk_score < 35.0 else "MEDIUM" if risk_score < 65.0 else "HIGH"

    # Fast High-Performance Feature Variance Calculation (0 deadlocks)
    global_importances = model.feature_importances_
    shap_explanation = {}
    for name, imp in zip(feature_names, global_importances):
        # Directional sign guessing based on baseline risks
        direction = 1 if raw_dict[name] > 2 or name in ['absences', 'failures'] else -1
        shap_explanation[name] = float(imp * direction * 10)

    top_factors = sorted(shap_explanation.items(), key=lambda x: abs(x[1]), reverse=True)[:5]

    # Baseline Static Interventions
    rule_interventions = []
    if payload.absences > 8:
        rule_interventions.append("Attendance Recovery Track: Immediate advisor meeting to flag structural absenteeism.")
    if payload.studytime <= 2:
        rule_interventions.append("Academic Structural Support: Recommend a minimum of 4 hours of weekly peer tutoring.")
    if payload.failures > 0 or payload.G2 < 10:
        rule_interventions.append("Targeted Skill Remediation: Enroll student in mandatory weekend subject bootcamps.")
    if not rule_interventions:
        rule_interventions.append("Baseline Observational Maintenance: Student is performing securely. Maintain standard tracking.")

    # Log straight to Supabase
    new_assessment = AssessmentTable(
        student_id=payload.student_id, user_id=current_user.id,
        features_payload=raw_dict, risk_score=risk_score,
        risk_band=risk_band, prediction=pred_status, shap_analysis=shap_explanation
    )
    db.add(new_assessment)
    db.commit()

    return {
        "student_id": payload.student_id, "risk_score": risk_score,
        "risk_band": risk_band, "prediction": pred_status,
        "top_factors": top_factors, "shap_analysis": shap_explanation,
        "rule_interventions": rule_interventions, "intervention_plan": " ".join(rule_interventions),
        "plan_source": "rules"
    }

@app.get("/dashboard/history")
async def get_assessment_history(current_user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(AssessmentTable).filter(AssessmentTable.user_id == current_user.id).order_by(AssessmentTable.timestamp.desc()).all()
    return [{
        "id": r.id, "student_id": r.student_id, "timestamp": r.timestamp.isoformat(),
        "study_time": r.features_payload.get("studytime", 2), "absences": r.features_payload.get("absences", 0),
        "probability": r.risk_score, "prediction": 1 if r.prediction == "AT-RISK" else 0
    } for r in rows]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}