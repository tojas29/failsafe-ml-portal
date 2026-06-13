from typing import Dict, Any, List
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware  # <-- ADD THIS IMPORT
import joblib
import pandas as pd
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import our database machinery and models
import models
from database import engine, get_db

# 1. Create the database tables automatically on startup if they don't exist yet
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FAILSAFE Predictive Brain")

# --- ADD CORS MIDDLEWARE CONFIGURATION HERE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any frontend application to connect. Perfect for development!
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allows all security and data headers
)
# ----------------------------------------------

# 2. Load our trained AI model and features
MODEL_PATH = "../models/failsafe_xgb_model.pkl"
FEATURES_PATH = "../models/model_features.pkl"

model = joblib.load(MODEL_PATH)
model_features = joblib.load(FEATURES_PATH)

class StudentData(BaseModel):
    data: Dict[str, Any]

@app.get("/")
def home():
    return {
        "status": "FAILSAFE API is running smoothly!", 
        "total_features_expected": len(model_features)
    }

# 3. Updated prediction route that saves records to the database
@app.post("/predict")
def predict_student_risk(student: StudentData, db: Session = Depends(get_db)):
    input_df = pd.DataFrame([student.data])
    input_encoded = pd.get_dummies(input_df)
    final_features = input_encoded.reindex(columns=model_features, fill_value=0)
    
    # Run the machine learning predictions
    prediction = int(model.predict(final_features)[0])
    probability = float(model.predict_proba(final_features)[0][1])
    
    # Dynamic Intervention Rules
    intervention = "None required. Maintain current tracking."
    if prediction == 1:
        if student.data.get('absences', 0) > 10:
            intervention = "High Priority: Schedule attendance counseling and student review."
        elif student.data.get('studytime', 2) <= 1:
            intervention = "Medium Priority: Enroll in mandatory supervised peer tutoring sessions."
        else:
            intervention = "Medium Priority: Flag for academic mentor check-in."

    # --- DATABASE PERSISTENCE LAYER ---
    # Create a record instance using our SQLAlchemy model mapping
    db_record = models.PredictionRecord(
        student_age=int(student.data.get('age', 18)),
        absences=int(student.data.get('absences', 0)),
        studytime=int(student.data.get('studytime', 2)),
        failure_probability=round(probability * 100, 2),
        at_risk_prediction=prediction,
        suggested_intervention=intervention
    )
    
    # Save it to our SQLite file permanently
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    # ----------------------------------

    return {
        "record_id": db_record.id,
        "at_risk_prediction": prediction,
        "failure_probability": round(probability * 100, 2),
        "suggested_intervention": intervention,
        "timestamp": db_record.created_at
    }

# 4. New route to fetch the history of all processed records
@app.get("/history")
def get_prediction_history(db: Session = Depends(get_db)):
    # Query all records stored inside our table
    records = db.query(models.PredictionRecord).order_by(models.PredictionRecord.id.desc()).all()
    return records