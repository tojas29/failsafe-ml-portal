<div align="center">

# 🛡️ FAILSAFE
### Early Student Risk Detection & Intervention Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=white)](https://react.dev/)
[![XGBoost](https://img.shields.io/badge/XGBoost-EB6C00?style=flat&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/Explainable_AI-SHAP-8A2BE2?style=flat)](https://shap.readthedocs.io/)
[![Deploy](https://img.shields.io/badge/Backend-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://render.com/)
[![Deploy](https://img.shields.io/badge/Frontend-Vercel-000000?style=flat&logo=vercel&logoColor=white)](https://vercel.com/)

An AI-powered web platform that helps faculty identify at-risk students early, understand the root causes of their struggles using explainable AI, and take targeted action before it's too late.

**[🌐 Live Demo](https://failsafe-ml-portal.vercel.app)** · **[⚙️ API Base](https://failsafe-ml-portal-e6dd.onrender.com)**

</div>

---

> ⚠️ The backend runs on Render's free tier and may take 30-60s to wake up on first request after inactivity.

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Machine Learning Pipeline](#-machine-learning-pipeline)
- [Backend API](#-backend-api)
- [Frontend](#-frontend)
- [Local Setup](#-local-setup)
- [Deployment](#-deployment)
- [API Reference](#-api-reference)
- [Dataset](#-dataset)
- [Environment Variables](#-environment-variables)

## 🎯 Overview

In educational institutions, student failure often goes undetected until end-of-semester results — leaving no room for meaningful intervention. Faculty lack a proactive, data-driven tool to identify at-risk students early and understand the root causes behind their struggles.

**FAILSAFE** addresses this by providing a web-based system where faculty can:

- Enter a student's academic, behavioral, and household data
- Get a **failure risk score (0-100%)** powered by a trained XGBoost model
- Understand **why** a student is flagged, via SHAP explainability
- Receive a **personalized intervention plan** written by a Groq LLM, with a deterministic rule-based fallback
- Track a running history of assessments per faculty account

## ✨ Features

### Machine Learning
- XGBoost classifier trained on the UCI Student Performance dataset
- SMOTE oversampling on the training set to correct class imbalance
- Configurable classification threshold (`threshold_config.json`) instead of a fixed 0.5 cutoff
- SHAP TreeExplainer for real per-prediction feature attributions
- Global feature-importance fallback if the SHAP explainer fails to load

### Intervention Engine
- **LLM-first**: sends the student's top SHAP factors and risk band to Groq to generate a natural-language intervention plan
- **Silent fallback**: if the Groq call fails (rate limit, timeout, missing key), the backend automatically falls back to a rule-based intervention derived from the top SHAP factors — no error surfaced to the faculty user
- Response includes a `plan_source` field so it's always clear which path generated the plan

### Backend (FastAPI)
- JWT-based faculty authentication (register/login) with bcrypt password hashing
- Single-student risk assessment endpoint
- Every assessment persisted to PostgreSQL with the full feature payload, SHAP values, and risk outcome
- Per-user assessment history endpoint
- Health check endpoint reporting model and explainer load status

### Frontend (React)
- Single-page app with view-state routing (LOGIN / SIGNUP / DASHBOARD)
- JWT and user data persisted in `localStorage`, with crash-proof parsing
- Quick-load preset student profiles for fast demo testing
- Live SHAP top-factor and intervention plan display per prediction
- Assessment history table synced from the backend on dashboard load

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Machine Learning** | Python, XGBoost, scikit-learn, SHAP, imbalanced-learn, Pandas, NumPy, SciPy |
| **LLM** | Groq API |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy, PostgreSQL, python-jose (JWT), bcrypt, Pydantic |
| **Frontend** | React, Vite, Axios |
| **Deployment** | Render (backend) · Vercel (frontend) · Supabase (database) |

## 📁 Project Structure

```
failsafe-ml-portal/
│
├── backend/
│   ├── data/processed/
│   │   └── features.json
│   ├── models/                     ← production model artifacts
│   ├── config.py                   ← env-driven settings
│   ├── database.py                 ← SQLAlchemy engine, session, Base
│   ├── main.py                     ← FastAPI app, routes, CORS, model loading
│   ├── models.py                   ← ORM models (User, StudentRiskAssessment)
│   ├── requirements.txt
│   └── student_model.joblib
│
├── data/
│   └── student-mat.csv             ← raw UCI dataset
│
├── frontend/                       ← React + Vite app
│
├── models/                         ← model artifacts (repo root copy)
│
├── notebooks/
│   ├── 01_EDA.ipynb                 ← exploratory data analysis
│   ├── 02_preprocessing.ipynb       ← cleaning, encoding, train/test split, SMOTE
│   ├── 03_model_training.ipynb      ← XGBoost training, threshold tuning, SHAP
│   └── 04_intervention_engine.ipynb ← Groq LLM + rule-based fallback logic
│
├── .gitignore
└── requirements.txt
```

## 🧠 Machine Learning Pipeline

### Dataset
UCI Student Performance Dataset — Math course (`student-mat.csv`), 395 students, 33 raw columns reduced to 21 model features.

### Target
```python
at_risk = 1  if G3 < 10   # failing
at_risk = 0  if G3 >= 10  # passing
```

### Features Used (21 total)

| Category | Features |
|---|---|
| **Academic** | `G1`, `G2`, `failures`, `studytime`, `absences` |
| **Behavioural** | `Dalc`, `Walc`, `goout`, `freetime`, `traveltime` |
| **Support** | `schoolsup`, `famsup`, `paid`, `activities`, `internet`, `higher` |
| **Background** | `Medu`, `Fedu`, `famrel`, `health`, `romantic` |

### Dropped Columns
```
school, sex, age, address, famsize, Pstatus, guardian, reason, nursery, Mjob, Fjob, G3
```

### Model

| Step | Detail |
|---|---|
| Algorithm | XGBoost Classifier |
| Imbalance handling | SMOTE, applied only on the training split |
| Split | 80/20 stratified, `random_state=42` |
| Explainability | SHAP TreeExplainer, with global-importance fallback |
| Threshold | Tuned and stored in `threshold_config.json` |

### Risk Bands

| Band | Probability |
|---|---|
| 🟢 LOW | < 35% |
| 🟡 MEDIUM | 35% – 65% |
| 🔴 HIGH | ≥ 65% |

## 🔌 Backend API

All endpoints except `/auth/register`, `/auth/login`, and `/health` require a `Bearer <token>` in the `Authorization` header.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | No | Create a faculty account, returns JWT |
| `POST` | `/auth/login` | No | Login (OAuth2 form), returns JWT |
| `POST` | `/predict` | Yes | Assess a single student, saves result to DB |
| `GET` | `/dashboard/history` | Yes | Get this faculty user's past assessments |
| `GET` | `/health` | No | Backend + model + explainer load status |

### Student Input Fields

| Field | Type | Range | Description |
|---|---|---|---|
| `G1` | int | 0–20 | First period grade |
| `G2` | int | 0–20 | Second period grade |
| `absences` | int | 0–93 | Number of absences |
| `failures` | int | 0–3 | Past class failures |
| `studytime` | int | 1–4 | Weekly study time |
| `traveltime` | int | 1–4 | Travel time to school |
| `famrel` | int | 1–5 | Family relationship quality |
| `freetime` | int | 1–5 | Free time after school |
| `goout` | int | 1–5 | Going out with friends |
| `Dalc` | int | 1–5 | Weekday alcohol consumption |
| `Walc` | int | 1–5 | Weekend alcohol consumption |
| `health` | int | 1–5 | Current health status |
| `Medu` | int | 0–4 | Mother's education level |
| `Fedu` | int | 0–4 | Father's education level |
| `schoolsup` | 0/1 | — | Receiving school support |
| `famsup` | 0/1 | — | Family study support |
| `paid` | 0/1 | — | Extra paid classes |
| `activities` | 0/1 | — | Extracurricular activities |
| `higher` | 0/1 | — | Wants higher education |
| `internet` | 0/1 | — | Internet access at home |
| `romantic` | 0/1 | — | In a romantic relationship |

## 💻 Frontend

Single React component handling:

- **Auth view** — login/signup forms, posts to `/auth/login` or `/auth/register`
- **Dashboard view** — 21-field assessment form + preset loaders, prediction result panel (risk score, band, top SHAP factors, intervention plan), and a history table
- **Session handling** — token and user persisted in `localStorage`, auto-restored on reload, cleared on logout or corruption

## ⚙️ Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (or a Supabase project)

### 1. Clone the repo
```bash
git clone https://github.com/tojas29/failsafe-ml-portal.git
cd failsafe-ml-portal
```

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create `backend/.env`:
```env
DATABASE_URL=your_postgres_or_supabase_url
SECRET_KEY=your_jwt_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
GROQ_API_KEY=your_groq_key
```

Ensure `backend/models/` contains the trained model, SHAP explainer, and `threshold_config.json`.

```bash
uvicorn main:app --reload
```
API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🚀 Deployment

| Service | Purpose | Tier |
|---|---|---|
| [Supabase](https://supabase.com/) | PostgreSQL database | Free |
| [Render](https://render.com/) | FastAPI backend hosting | Free |
| [Vercel](https://vercel.com/) | React frontend hosting | Free |
| [Groq](https://console.groq.com/) | LLM inference | Free |

### Backend → Render
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Env vars: `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `GROQ_API_KEY`

### Frontend → Vercel
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`
- `API_BASE` in the frontend points directly to the Render backend URL

### CORS
Backend `ALLOWED_ORIGINS` must include the exact Vercel production domain for the JWT `Authorization` header to work cross-origin.

## 📡 API Reference

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=faculty@example.com&password=yourpassword
```

### Single Student Assessment
```http
POST /predict
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": "STU-001",
  "G1": 9, "G2": 8, "absences": 12, "failures": 1,
  "studytime": 1, "traveltime": 2, "famrel": 3,
  "freetime": 4, "goout": 4, "Dalc": 2, "Walc": 3,
  "health": 3, "Medu": 2, "Fedu": 1,
  "schoolsup": 0, "famsup": 1, "paid": 0,
  "activities": 0, "higher": 1, "internet": 1, "romantic": 0
}
```

**Response:**
```json
{
  "student_id": "STU-001",
  "risk_score": 78.4,
  "risk_band": "HIGH",
  "prediction": "AT-RISK",
  "top_factors": [["G2", 3.27], ["absences", 1.84]],
  "shap_analysis": { "...": "..." },
  "rule_interventions": ["..."],
  "intervention_plan": "...",
  "plan_source": "llm"
}
```

## 📊 Dataset

**UCI Student Performance Dataset** — Paulo Cortez, University of Minho, Portugal.
Available on [Kaggle](https://www.kaggle.com/datasets/uciml/student-alcohol-consumption).
FAILSAFE uses the Math dataset (`student-mat.csv`, 395 students).

## 🔐 Environment Variables

### Backend

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres/Supabase connection string |
| `SECRET_KEY` | Secret for signing JWTs |
| `ALGORITHM` | JWT signing algorithm (`HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `GROQ_API_KEY` | Groq API key for the LLM intervention engine |

## 🙏 Acknowledgements

- [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/Student+Performance) — dataset
- [Groq](https://groq.com/) — LLM inference
- [SHAP](https://shap.readthedocs.io/) — model explainability
- [XGBoost](https://xgboost.readthedocs.io/) — gradient boosting framework

---

<div align="center">

Built by **[Ojas Thete](https://github.com/tojas29)**

</div>
