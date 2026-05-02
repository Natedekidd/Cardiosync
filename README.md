# CardioSync — Precision Cardiovascular Risk Platform

A full-stack precision medicine platform combining clinical AI, genomic analysis, 
and environmental data to generate personalised 10-year cardiovascular risk scores.

## Architecture
- **Frontend** — React + Vite (cardiosync-ui/)
- **Backend** — FastAPI + SQLite (cardiosync-backend/)
- **AI Model** — Framingham Heart Study ML model (cardiosync-ai-ml/)

## How to Run

### 1. AI Model (port 8000)
cd cardiosync-ai-ml
pip install fastapi uvicorn scikit-learn shap xgboost
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

### 2. Backend (port 8001)
cd cardiosync-backend
pip install fastapi uvicorn httpx python-multipart
uvicorn fastapi_app:app --reload --port 8001

### 3. Frontend (port 5173)
cd cardiosync-ui
npm install
npm run dev
