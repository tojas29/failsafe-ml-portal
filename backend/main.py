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
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

import bcrypt

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

from database import Base, engine, get_db
from models import User, StudentRiskAssessment
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Model + SHAP explainer loader — layout is fixed: backend/models/*
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "failsafe_model.pkl")
EXPLAINER_PATH = os.path.join(BASE_DIR, "models", "shap_explainer.pkl")
CONFIG_PATH = os.path.join(BASE_DIR, "models", "threshold_config.json")

model = None
explainer = None
classification_threshold = 0.5

try:
    model = joblib.load(MODEL_PATH)
    with open(CONFIG_PATH, "r") as f:
        threshold_config = json.load(f)
    classification_threshold = threshold_config.get("classification_threshold", 0.5)
    print(f"✅ Model loaded from {MODEL_PATH}. Threshold: {classification_threshold}")
except Exception as e:
    print(f"⚠️ Failed to load model: {e}")

try:
    explainer = joblib.load(EXPLAINER_PATH)
    print(f"✅ SHAP explainer loaded from {EXPLAINER_PATH}")
except Exception as e:
    print(f"⚠️ Failed to load SHAP explainer: {e}")

# Data Validation Specs
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

# Tables are created if they don't already exist. Safe to call every startup —
# create_all() no-ops on tables that are already present (e.g. your Supabase ones).
Base.metadata.create_all(bind=engine)

# Wildcard origins ("*") cannot be combined with allow_credentials=True — browsers
# will reject the response. List real frontend origins here (add your deployed
# frontend URL once it exists).
ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

@app.post("/auth/register", response_model=Token)
async def register_faculty(user_in: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, hashed_password=hashed_pwd, name=user_in.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_access_token({"sub": new_user.email})
    return {"access_token": token, "token_type": "bearer", "user_name": new_user.name, "user_email": new_user.email}

@app.post("/auth/login", response_model=Token)
async def login_faculty(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password.")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user_name": user.name, "user_email": user.email}

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

    prob_raw = float(model.predict_proba(input_df)[0][1])
    risk_score = round(prob_raw * 100, 2)
    pred_status = "AT-RISK" if prob_raw >= classification_threshold else "SECURE"
    risk_band = "LOW" if risk_score < 35.0 else "MEDIUM" if risk_score < 65.0 else "HIGH"

    # Real per-prediction SHAP values from the pickled TreeExplainer.
    # Falls back to a rough global-importance heuristic only if the explainer
    # failed to load, so /predict never hard-fails on this step.
    shap_explanation = {}
    if explainer is not None:
        try:
            raw_shap = explainer.shap_values(input_df)
            if isinstance(raw_shap, list):
                raw_shap = raw_shap[1] if len(raw_shap) > 1 else raw_shap[0]
            raw_shap = np.asarray(raw_shap)
            if raw_shap.ndim == 2:
                raw_shap = raw_shap[0]
            shap_explanation = {name: float(val) for name, val in zip(feature_names, raw_shap)}
        except Exception as e:
            print(f"⚠️ SHAP explainer call failed, using importance fallback: {e}")

    if not shap_explanation:
        global_importances = model.feature_importances_
        for name, imp in zip(feature_names, global_importances):
            direction = 1 if raw_dict[name] > 2 or name in ['absences', 'failures'] else -1
            shap_explanation[name] = float(imp * direction * 10)

    top_factors = sorted(shap_explanation.items(), key=lambda x: abs(x[1]), reverse=True)[:5]

    rule_interventions = []
    if payload.absences > 8:
        rule_interventions.append("Attendance Recovery Track: Immediate advisor meeting to flag structural absenteeism.")
    if payload.studytime <= 2:
        rule_interventions.append("Academic Structural Support: Recommend a minimum of 4 hours of weekly peer tutoring.")
    if payload.failures > 0 or payload.G2 < 10:
        rule_interventions.append("Targeted Skill Remediation: Enroll student in mandatory weekend subject bootcamps.")
    if not rule_interventions:
        rule_interventions.append("Baseline Observational Maintenance: Student is performing securely. Maintain standard tracking.")

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
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "explainer_loaded": explainer is not None,
    }