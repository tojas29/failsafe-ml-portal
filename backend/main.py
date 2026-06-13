# backend/main.py (Updated Endpoint)
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import shap
import numpy as np

app = FastAPI()

# Load model and prepare SHAP explainer
model_data = joblib.load("student_model.joblib")
# Extract the base tree model if you wrapped it in a classifier wrapper
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
    # Form input array mapped exactly to dataset training layout
    input_features = np.array([[student.study_time, student.failures, student.absences, student.g1, student.g2]])
    
    # 1. Compute stable calibrated probability
    prob = model_data.predict_proba(input_features)[0][1] * 100
    
    # 2. Compute local SHAP values for this specific inference
    shap_values = explainer.shap_values(input_features)
    
    # Handle array differences between binary/multi-output tree arrays
    feature_impacts = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
    
    feature_names = ["Weekly Study Time", "Past Class Failures", "Absences", "Midterm Grade 1", "Midterm Grade 2"]
    shap_explanation = {name: float(impact) for name, impact in zip(feature_names, feature_impacts)}
    
    # 3. Auto-generate personalized interventions based on driving features
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