import os
import joblib
import shap
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable Global Permissive CORS Handshakes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "student_model.joblib")
model_data = joblib.load(MODEL_PATH)
base_model = model_data.estimator if hasattr(model_data, 'estimator') else model_data
explainer = shap.TreeExplainer(base_model)

class StudentData(BaseModel):
    study_time: int
    failures: int
    absences: int
    g1: int
    g2: int

@app.post("/predict")
async def predict_risk(student: StudentData):
    input_features = np.array([[student.study_time, student.failures, student.absences, student.g1, student.g2]])
    prob = model_data.predict_proba(input_features)[0][1] * 100
    shap_values = explainer.shap_values(input_features)
    feature_impacts = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
    feature_names = ["Weekly Study Time", "Past Class Failures", "Absences", "Midterm Grade 1", "Midterm Grade 2"]
    shap_explanation = {name: float(impact) for name, impact in zip(feature_names, feature_impacts)}
    
    interventions = []
    if student.absences > 8:
        interventions.append("Attendance Recovery Track & Faculty Counseling Referral.")
    if student.study_time <= 2:
        interventions.append("Mandatory Peer-Tutoring Sessions (3 hours/week minimum).")
    if student.failures > 0 or student.g2 < 10:
        interventions.append("Targeted Academic Boot Camp & Supplemental Assignments.")
    if not interventions:
        interventions.append("None required. Maintain baseline tracking.")

    return {
        "probability": round(prob, 2),
        "status": "Risk" if prob > 50 else "Safe",
        "shap_analysis": shap_explanation,
        "interventions": interventions
    }

@app.get("/history")
async def get_history():
    return []
