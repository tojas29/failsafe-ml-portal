import os
import joblib
import shap
import numpy as np
import re
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "student_model.joblib")
DB_PATH = os.path.join(BASE_DIR, "failsafe.db")

# Global Active Backup Cache to bypass Render container spin-down limits
GLOBAL_HISTORY_CACHE = []

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                study_time INTEGER,
                absences INTEGER,
                probability REAL,
                prediction INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database setup bypass: {e}")

init_db()

model_data = joblib.load(MODEL_PATH)
base_model = model_data.estimator if hasattr(model_data, 'estimator') else model_data
explainer = shap.TreeExplainer(base_model)

@app.post("/predict")
async def predict_risk(payload: dict):
    def extract_field(aliases, default_val):
        for alias in aliases:
            for k, v in payload.items():
                if k.lower() == alias.lower():
                    if isinstance(v, str):
                        numbers = re.findall(r'\d+', v)
                        if numbers:
                            return int(numbers[0])
                    try:
                        return int(float(v))
                    except:
                        pass
        return default_val

    study_time = extract_field(["study_time", "studytime", "weekly study time", "study"], 2)
    failures = extract_field(["failures", "past class failures", "past_failures"], 0)
    absences = extract_field(["absences", "total semester absences", "total_absences"], 2)
    g1 = extract_field(["g1", "midterm grade 1", "midterm1"], 12)
    g2 = extract_field(["g2", "midterm grade 2", "midterm2"], 12)

    input_features = np.array([[study_time, failures, absences, g1, g2]])
    prob = float(model_data.predict_proba(input_features)[0][1] * 100)
    
    try:
        shap_values = explainer.shap_values(input_features)
        feature_impacts = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
        if hasattr(feature_impacts, "tolist"):
            feature_impacts = feature_impacts.tolist()
        if isinstance(feature_impacts, list) and isinstance(feature_impacts[0], list):
            feature_impacts = feature_impacts[0]
    except:
        feature_impacts = [0.0] * 5

    feature_names = ["Weekly Study Time", "Past Class Failures", "Absences", "Midterm Grade 1", "Midterm Grade 2"]
    shap_explanation = {name: float(impact) for name, impact in zip(feature_names, feature_impacts)}
    
    interventions = []
    if absences > 8:
        interventions.append("Attendance Recovery Track & Faculty Counseling Referral.")
    if study_time <= 2:
        interventions.append("Mandatory Peer-Tutoring Sessions (3 hours/week minimum).")
    if failures > 0 or g2 < 10:
        interventions.append("Targeted Academic Boot Camp & Supplemental Assignments.")
    if not interventions:
        interventions.append("None required. Maintain baseline tracking.")

    pred_val = 1 if prob > 50 else 0
    prob_val = round(prob, 2)

    # Backup to Runtime Memory Cache immediately
    cache_record = {
        "id": len(GLOBAL_HISTORY_CACHE) + 1,
        "study": study_time,
        "study_time": study_time,
        "absences": absences,
        "probability": prob_val,
        "failure_probability": prob_val,
        "prediction": pred_val,
        "at_risk_prediction": pred_val
    }
    GLOBAL_HISTORY_CACHE.insert(0, cache_record)

    # Context managed file logging with timeout safety margins
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions (study_time, absences, probability, prediction)
                VALUES (?, ?, ?, ?)
            ''', (study_time, absences, prob_val, pred_val))
            conn.commit()
    except Exception as e:
        print(f"File log deferred: {e}")

    return {
        "at_risk_prediction": pred_val,
        "failure_probability": prob_val,
        "shap_analysis": shap_explanation,
        "interventions": interventions
    }

@app.get("/history")
async def get_history():
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.conn.cursor() if hasattr(conn, 'conn') else conn.cursor()
            cursor.execute("SELECT id, study_time, absences, probability, prediction FROM predictions ORDER BY id DESC")
            rows = cursor.fetchall()
            
        if not rows and GLOBAL_HISTORY_CACHE:
            return {"history": GLOBAL_HISTORY_CACHE}
            
        parsed_rows = [{
            "id": r[0],
            "study": r[1],
            "study_time": r[1],
            "absences": r[2],
            "probability": r[3],
            "failure_probability": r[3],
            "prediction": r[4],
            "at_risk_prediction": r[4]
        } for r in rows]
        
        return {"history": parsed_rows}
    except Exception as e:
        # If SQLite thread returns locked or uninitialized, serve from memory fallback
        return {"history": GLOBAL_HISTORY_CACHE}