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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from groq import Groq

import bcrypt

from database import Base, engine, get_db
from models import User, StudentRiskAssessment
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Password helpers ──────────────────────────────────────────────────────
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ── Model loader ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH     = os.path.join(BASE_DIR, "models", "failsafe_model.pkl")
EXPLAINER_PATH = os.path.join(BASE_DIR, "models", "shap_explainer.pkl")
CONFIG_PATH    = os.path.join(BASE_DIR, "models", "threshold_config.json")

model = None
explainer = None
classification_threshold = 0.5

try:
    model = joblib.load(MODEL_PATH)
    with open(CONFIG_PATH, "r") as f:
        threshold_config = json.load(f)
    classification_threshold = threshold_config.get("classification_threshold", 0.5)
    print(f"✅ Model loaded. Threshold: {classification_threshold}")
except Exception as e:
    print(f"⚠️ Failed to load model: {e}")

try:
    explainer = joblib.load(EXPLAINER_PATH)
    print(f"✅ SHAP explainer loaded.")
except Exception as e:
    print(f"⚠️ Failed to load SHAP explainer: {e}")


# ── SHAP Intervention Map (module-level constant — correct) ───────────────
SHAP_INTERVENTION_MAP = {
    "absences":  {"positive": "Attendance Recovery Track: Student shows high absenteeism as a key risk driver. Schedule immediate advisor check-in and implement weekly attendance monitoring.", "negative": None},
    "failures":  {"positive": "Academic Remediation: Prior course failures are a top risk signal. Enroll student in subject-specific bootcamps and assign a dedicated peer tutor.", "negative": None},
    "G2":        {"positive": None, "negative": "Grade Improvement Plan: Recent period grade is dragging risk up. Set bi-weekly faculty review meetings to track grade trajectory."},
    "G1":        {"positive": None, "negative": "Early Academic Support: First period grade indicates foundational gaps. Recommend diagnostic assessment and foundational skill workshops."},
    "studytime": {"positive": None, "negative": "Study Habit Intervention: Low weekly study hours are a primary risk factor. Mandate structured study sessions with a minimum of 5 hours/week."},
    "goout":     {"positive": "Social Balance Counseling: High social activity is contributing to risk. Recommend time-management counseling to rebalance priorities.", "negative": None},
    "Walc":      {"positive": "Wellness Referral: Weekend alcohol consumption is flagged as a risk driver. Refer student to campus wellness and counseling services.", "negative": None},
    "Dalc":      {"positive": "Wellness Referral: Weekday alcohol consumption is a significant risk contributor. Immediate referral to student support and wellness program.", "negative": None},
    "health":    {"positive": None, "negative": "Health Support: Poor self-reported health is elevating risk. Connect student with campus health services and reduce academic overload."},
    "famrel":    {"positive": None, "negative": "Family Engagement: Poor family relationship quality is a risk signal. Involve family in a structured support meeting with a school counselor."},
    "Medu":      {"positive": None, "negative": "Parental Education Gap: Low mother education level correlates with reduced home academic support. Provide additional faculty-led office hours."},
    "Fedu":      {"positive": None, "negative": "Parental Education Gap: Low father education level correlates with reduced home academic support. Provide additional faculty-led office hours."},
    "higher":    {"positive": None, "negative": "Motivation Intervention: Student does not aspire to higher education — a key risk driver. Schedule career counseling and goal-setting sessions."},
    "internet":  {"positive": None, "negative": "Resource Access: Lack of home internet access is contributing to risk. Provide access to campus digital labs and offline study materials."},
    "traveltime":{"positive": "Commute Burden: Long travel time is flagging as a risk factor. Explore on-campus housing options or schedule adjustments to reduce fatigue.", "negative": None},
    "freetime":  {"positive": "Time Management: Excess free time is a risk signal. Channel into structured extracurricular or supervised study programs.", "negative": None},
    "romantic":  {"positive": "Wellbeing Check-in: Romantic relationship is flagged as a distraction risk. Schedule a confidential wellbeing session with a student counselor.", "negative": None},
    "schoolsup": {"positive": None, "negative": "School Support Enrollment: Student is not receiving extra school support despite risk signals. Enroll in after-school academic support program."},
    "famsup":    {"positive": None, "negative": "Family Support Gap: Absence of family academic support is a risk driver. Arrange parent-teacher meeting to establish a home support structure."},
    "activities":{"positive": None, "negative": "Extracurricular Engagement: Lack of activities correlates with disengagement risk. Recommend joining at least one structured school club or sport."},
    "paid":      {"positive": None, "negative": "Tutoring Access: Student is not attending paid classes despite academic risk. Explore subsidized tutoring options through the institution."},
}


# ── Pydantic schemas ──────────────────────────────────────────────────────
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


# ── App + CORS ────────────────────────────────────────────────────────────
app = FastAPI()

Base.metadata.create_all(bind=engine)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth helpers ──────────────────────────────────────────────────────────
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
        if email is None:
            raise exception
    except JWTError:
        raise exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise exception
    return user


# ── Routes ────────────────────────────────────────────────────────────────
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

def generate_llm_intervention(student_data: dict, top_factors: list, risk_band: str, pred_status: str) -> str:
    try:
        factors_text = "\n".join(
            [f"- {name}: SHAP value {val:+.3f} ({'increases' if val > 0 else 'decreases'} risk)"
             for name, val in top_factors]
        )
        prompt = f"""You are an academic counselor AI. A student has been assessed as {pred_status} (Risk Band: {risk_band}).

Top SHAP risk factors for this student:
{factors_text}

Student profile summary:
- G1 (Period 1 grade): {student_data.get('G1')}/20
- G2 (Period 2 grade): {student_data.get('G2')}/20
- Absences: {student_data.get('absences')} days
- Study time per week: {student_data.get('studytime')} (1=<2hrs, 2=2-5hrs, 3=5-10hrs, 4=>10hrs)
- Past failures: {student_data.get('failures')}
- Goes out with friends: {student_data.get('goout')}/5
- Alcohol (weekday/weekend): {student_data.get('Dalc')}/{student_data.get('Walc')} out of 5

Write exactly 3 specific, actionable intervention recommendations for this student. 
Be concise. Each recommendation should be 1-2 sentences. Number them 1, 2, 3."""

        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Groq API failed: {e}")
        return None


@app.post("/predict")
async def assess_student(
    payload: StudentAssessmentInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if model is None:
        raise HTTPException(status_code=503, detail="Model assets compiling.")

    feature_names = [
        "G1", "G2", "failures", "studytime", "absences",
        "traveltime", "famrel", "freetime", "goout", "Dalc", "Walc", "health",
        "Medu", "Fedu", "schoolsup", "famsup", "paid", "activities", "higher", "internet", "romantic",
    ]

    raw_dict = payload.model_dump()
    ordered_values = [raw_dict[feat] for feat in feature_names]
    input_df = pd.DataFrame([ordered_values], columns=feature_names)

    prob_raw = float(model.predict_proba(input_df)[0][1])
    risk_score = round(prob_raw * 100, 2)
    pred_status = "AT-RISK" if prob_raw >= classification_threshold else "SECURE"
    risk_band = "LOW" if risk_score < 35.0 else "MEDIUM" if risk_score < 65.0 else "HIGH"

    # SHAP values
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
            direction = 1 if raw_dict[name] > 2 or name in ["absences", "failures"] else -1
            shap_explanation[name] = float(imp * direction * 10)

    top_factors = sorted(shap_explanation.items(), key=lambda x: abs(x[1]), reverse=True)[:5]

    # ── Intervention: LLM first, SHAP map fallback ────────────────────────
    llm_plan = generate_llm_intervention(raw_dict, top_factors, risk_band, pred_status)

    if llm_plan:
        rule_interventions = [llm_plan]
        plan_source = "llm"
    else:
        rule_interventions = []
        for feature_name, shap_val in top_factors:
            direction = "positive" if shap_val > 0 else "negative"
            message = SHAP_INTERVENTION_MAP.get(feature_name, {}).get(direction)
            if message and message not in rule_interventions:
                rule_interventions.append(message)
            if len(rule_interventions) == 3:
                break
        if not rule_interventions:
            rule_interventions.append(
                "Baseline Observational Maintenance: Continue standard monitoring "
                "with a scheduled monthly faculty check-in."
            )
        plan_source = "shap"

    # ── Save to DB ────────────────────────────────────────────────────────
    new_assessment = StudentRiskAssessment(
        student_id=payload.student_id,
        user_id=current_user.id,
        features_payload=raw_dict,
        risk_score=risk_score,
        risk_band=risk_band,
        prediction=pred_status,
        shap_analysis=shap_explanation,
    )
    db.add(new_assessment)
    db.commit()

    return {
        "student_id": payload.student_id,
        "risk_score": risk_score,
        "risk_band": risk_band,
        "prediction": pred_status,
        "top_factors": top_factors,
        "shap_analysis": shap_explanation,
        "rule_interventions": rule_interventions,
        "intervention_plan": " ".join(rule_interventions),
        "plan_source": plan_source,
    }


@app.get("/dashboard/history")
async def get_assessment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(StudentRiskAssessment)
        .filter(StudentRiskAssessment.user_id == current_user.id)
        .order_by(StudentRiskAssessment.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "timestamp": r.created_at.isoformat(),
            "study_time": r.features_payload.get("studytime", 2),
            "absences": r.features_payload.get("absences", 0),
            "probability": r.risk_score,
            "prediction": 1 if r.prediction == "AT-RISK" else 0,
        }
        for r in rows
    ]


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "explainer_loaded": explainer is not None,
    }