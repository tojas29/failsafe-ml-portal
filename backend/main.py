import os
import joblib
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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

# 1. Database Configuration & Cloud Mapping Strategy
DATABASE_URL = "postgresql://postgres:Arnavojas2911@db.vsfqobrpybnergybcale.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Security & Token Cryptography Constants
SECRET_KEY = "SUPER_SECRET_FAILSAFE_TOKEN_SIGNING_KEY_CHOOSE_A_RANDOM_HASH_FOR_PROD"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# 3. SQLAlchemy Database Tables
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
    
    # Core 21-Feature input contract tracking payload parameters
    features_payload = Column(JSON, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_band = Column(String, nullable=False)
    prediction = Column(String, nullable=False)
    shap_analysis = Column(JSON, nullable=False)

# Auto-provision relational structures inside Supabase cluster on boot
Base.metadata.create_all(bind=engine)

# 4. Machine Learning Weight Lifecycle Loader
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "failsafe_model.pkl")
SHAP_PATH = os.path.join(BASE_DIR, "models", "shap_explainer.pkl")
CONFIG_PATH = os.path.join(BASE_DIR, "models", "threshold_config.json")

try:
    model = joblib.load(MODEL_PATH)
    explainer = joblib.load(SHAP_PATH)
    with open(CONFIG_PATH, "r") as f:
        threshold_config = json.load(f)
    classification_threshold = threshold_config.get("classification_threshold", 0.5)
    print(f"✅ ML Engine fully operational with 21 features. Optimized Recall Threshold: {classification_threshold}")
except Exception as e:
    print(f"⚠️ Lazy loading model layers: {e}")
    model, explainer, classification_threshold = None, None, 0.5

# 5. Pydantic Request/Response Schema Contracts
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
    G1: int
    G2: int
    absences: int
    failures: int
    studytime: int
    traveltime: int
    famrel: int
    freetime: int
    goout: int
    Dalc: int
    Walc: int
    health: int
    schoolsup: int
    famsup: int
    paid: int
    activities: int
    higher: int
    internet: int
    romantic: int
    Medu: int
    Fedu: int

# 6. Core Framework Initialization
app = FastAPI(title="FAILSAFE Engine Core API")

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

# 7. Helper Cryptography Layer Engines
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate workspace credentials session.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(UserTable).filter(UserTable.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# 8. Authentication Routing System
@app.post("/auth/register", response_model=Token)
async def register_faculty(user_in: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(UserTable).filter(UserTable.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Faculty profile email already registered.")
    
    hashed_pwd = pwd_context.hash(user_in.password)
    new_user = UserTable(email=user_in.email, hashed_password=hashed_pwd, name=user_in.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = jwt.encode({"sub": new_user.email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer", "user_name": new_user.name, "user_email": new_user.email}

@app.post("/auth/login", response_model=Token)
async def login_faculty(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserTable).filter(UserTable.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid account email or password configuration.")
    
    access_token = jwt.encode({"sub": user.email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer", "user_name": user.name, "user_email": user.email}

# 9. Predictive Intelligence Diagnostics Routing Channel
@app.post("/predict")
async def assess_student(payload: StudentAssessmentInput, current_user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)):
    if model is None or explainer is None:
        raise HTTPException(status_code=503, detail="Machine learning binary matrices initializing. Try again shortly.")

    # Sort dictionary properties strictly into order mapping to model arrays configuration
    feature_names = [
        'G1', 'G2', 'failures', 'studytime', 'absences',
        'traveltime', 'famrel', 'freetime', 'goout', 'Dalc', 'Walc', 'health',
        'Medu', 'Fedu', 'schoolsup', 'famsup', 'paid', 'activities', 'higher', 'internet', 'romantic'
    ]
    
    raw_dict = payload.dict()
    ordered_values = [raw_dict[feat] for feat in feature_names]
    input_df = pd.DataFrame([ordered_values], columns=feature_names)
    
    # Execute XGBoost tree evaluation matrix operations
    prob_raw = float(model.predict_proba(input_df)[0][1])
    risk_score = round(prob_raw * 100, 2)
    
    # Evaluate against custom calibrated threshold metrics computed during SMOTE balance
    pred_status = "AT-RISK" if prob_raw >= classification_threshold else "SECURE"
    
    if risk_score < 35.0:
        risk_band = "LOW"
    elif risk_score < 65.0:
        risk_band = "MEDIUM"
    else:
        risk_band = "HIGH"

    # Compute SHAP Root-Cause XAI Vectors
    try:
        shap_values = explainer.shap_values(input_df)
        feature_impacts = shap_values[0].tolist() if hasattr(shap_values, "tolist") else shap_values[0]
        if isinstance(feature_impacts, list) and isinstance(feature_impacts[0], list):
            feature_impacts = feature_impacts[0]
    except Exception:
        feature_impacts = [0.0] * len(feature_names)

    shap_explanation = {name: float(impact) for name, impact in zip(feature_names, feature_impacts)}

    # Static baseline rules (Will be upgraded via Groq LLaMA 3.3 in Phase 3)
    rule_interventions = []
    if payload.absences > 8:
        rule_interventions.append("Attendance Recovery Track & Faculty Counseling Referral.")
    if payload.studytime <= 2:
        rule_interventions.append("Mandatory Peer-Tutoring Sessions (3 hours/week minimum).")
    if payload.failures > 0 or payload.G2 < 10:
        rule_interventions.append("Targeted Academic Boot Camp & Supplemental Assignments.")
    if not rule_interventions:
        rule_interventions.append("None required. Maintain baseline tracking patterns.")

    # Record metrics payload directly into your active Supabase cloud database instance
    new_assessment = AssessmentTable(
        student_id=payload.student_id,
        user_id=current_user.id,
        features_payload=raw_dict,
        risk_score=risk_score,
        risk_band=risk_band,
        prediction=pred_status,
        shap_analysis=shap_explanation
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)

    return {
        "student_id": payload.student_id,
        "risk_score": risk_score,
        "risk_band": risk_band,
        "prediction": pred_status,
        "top_factors": sorted(shap_explanation.items(), key=lambda x: abs(x[1]), reverse=True)[:5],
        "shap_analysis": shap_explanation,
        "rule_interventions": rule_interventions,
        "intervention_plan": " ".join(rule_interventions),
        "plan_source": "rules"
    }

@app.get("/dashboard/history")
async def get_assessment_history(current_user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(AssessmentTable).filter(AssessmentTable.user_id == current_user.id).order_by(AssessmentTable.timestamp.desc()).all()
    
    history_list = []
    for r in rows:
        history_list.append({
            "id": r.id,
            "student_id": r.student_id,
            "timestamp": r.timestamp.isoformat(),
            "study_time": r.features_payload.get("studytime", 2),
            "absences": r.features_payload.get("absences", 0),
            "probability": r.risk_score,
            "prediction": 1 if r.prediction == "AT-RISK" else 0
        })
    return history_list

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}