import os
import joblib
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
# from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

import bcrypt

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

from database import Base, engine, get_db
from models import User, StudentRiskAssessment
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# 4. Model Binary Loader (Dynamic Path Fallback to resolve folder mismatches)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path Option A: Inside the backend folder context
MODEL_PATH_A = os.path.join(BASE_DIR, "models", "failsafe_model.pkl")
CONFIG_PATH_A = os.path.join(BASE_DIR, "models", "threshold_config.json")

# Path Option B: Absolute root context fallback
MODEL_PATH_B = os.path.join(os.path.dirname(BASE_DIR), "backend", "models", "failsafe_model.pkl")
CONFIG_PATH_B = os.path.join(os.path.dirname(BASE_DIR), "backend", "models", "threshold_config.json")

# Simple verification switch to select the valid file path location
if os.path.exists(MODEL_PATH_A):
    chosen_model_path, chosen_config_path = MODEL_PATH_A, CONFIG_PATH_A
else:
    chosen_model_path, chosen_config_path = MODEL_PATH_B, CONFIG_PATH_B

try:
    model = joblib.load(chosen_model_path)
    with open(chosen_config_path, "r") as f:
        threshold_config = json.load(f)
    classification_threshold = threshold_config.get("classification_threshold", 0.5)
    print(f"✅ XGBoost Core Operational. Loaded from: {chosen_model_path}. Threshold: {classification_threshold}")
except Exception as e:
    print(f"⚠️ Model startup delay / Path error details: {e}")
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


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    exception = HTTPException(status_code=401, detail="Session expired or invalid.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise exception
    except JWTError:
        raise exception
    user = db.query(User).filter(User.email == email).first()
    if user is None: raise exception
    return user

# 6. Auth Gateways
@app.post("/auth/register", response_model=Token)
async def register_faculty(user_in: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already split registered.")
    # hashed_pwd = pwd_context.hash(user_in.password)
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, hashed_password=hashed_pwd, name=user_in.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # token = jwt.encode({"sub": new_user.email}, SECRET_KEY, algorithm=ALGORITHM)
    token = create_access_token({"sub": new_user.email})
    return {"access_token": token, "token_type": "bearer", "user_name": new_user.name, "user_email": new_user.email}

@app.post("/auth/login", response_model=Token)
async def login_faculty(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credential parameters.")
    # token = jwt.encode({"sub": user.email}, SECRET_KEY, algorithm=ALGORITHM)
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user_name": user.name, "user_email": user.email}

# 7. Lightning Fast Instant Prediction Channel
@app.post("/predict")
async def assess_student(payload: StudentAssessmentInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
    new_assessment = StudentRiskAssessment(
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
async def get_assessment_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(StudentRiskAssessment).filter(StudentRiskAssessment.user_id == current_user.id).order_by(StudentRiskAssessment.created_at.desc()).all()
    return [{
        "id": r.id, "student_id": r.student_id, "timestamp": r.created_at.isoformat(),
        "study_time": r.features_payload.get("studytime", 2), "absences": r.features_payload.get("absences", 0),
        "probability": r.risk_score, "prediction": 1 if r.prediction == "AT-RISK" else 0
    } for r in rows]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}
