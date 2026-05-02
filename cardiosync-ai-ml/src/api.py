"""
Framingham CHD Risk Prediction - FastAPI backend.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
import uvicorn

from model import FraminghamPredictor

class PatientInput(BaseModel):
    age: int = Field(..., ge=20, le=100)
    male: int = Field(..., ge=0, le=1)
    education: int = Field(2, ge=1, le=4)
    currentSmoker: int = Field(..., ge=0, le=1)
    cigsPerDay: int = Field(0, ge=0, le=100)
    BPMeds: int = Field(0, ge=0, le=1)
    prevalentStroke: int = Field(0, ge=0, le=1)
    prevalentHyp: int = Field(0, ge=0, le=1)
    diabetes: int = Field(0, ge=0, le=1)
    totChol: float = Field(..., ge=100, le=600)
    sysBP: float = Field(..., ge=80, le=250)
    diaBP: float = Field(..., ge=40, le=150)
    BMI: float = Field(..., ge=15, le=60)
    heartRate: float = Field(..., ge=40, le=200)
    glucose: float = Field(..., ge=40, le=400)

    @validator('diaBP')
    def validate_bp(cls, v, values):
        if 'sysBP' in values and v >= values['sysBP']:
            raise ValueError('Diastolic BP must be less than systolic BP')
        return v

    @validator('cigsPerDay')
    def validate_smoking(cls, v, values):
        if (
            'currentSmoker' in values
            and values['currentSmoker'] == 0
            and v > 0
        ):
            raise ValueError('Non-smokers should have 0 cigarettes per day')
        return v

    class Config:
        schema_extra = {
            "example": {
                "age": 55, "male": 1, "education": 2,
                "currentSmoker": 1, "cigsPerDay": 20,
                "BPMeds": 0, "prevalentStroke": 0,
                "prevalentHyp": 1, "diabetes": 0,
                "totChol": 250, "sysBP": 145, "diaBP": 92,
                "BMI": 28.5, "heartRate": 80, "glucose": 95
            }
        }

class RiskPrediction(BaseModel):
    risk_probability: float
    risk_percentage: float
    risk_category: str
    binary_prediction: int
    confidence: float

class ExplanationResponse(BaseModel):
    base_value: float
    prediction: float
    top_features: List[Dict]

class FullAssessmentResponse(BaseModel):
    patient_input: Dict
    risk_prediction: RiskPrediction
    explanation: Optional[ExplanationResponse]
    recommendations: List[str]

class ModelInfo(BaseModel):
    model_type: str
    n_features: int
    roc_auc: float
    sensitivity: float
    specificity: float
    shap_available: bool

app = FastAPI(
    title="Framingham CHD Risk API",
    description=(
        "10-year coronary heart disease risk prediction "
        "with SHAP explanations"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = None

@app.on_event("startup")
async def startup_event():
    global predictor
    predictor = FraminghamPredictor(artifacts_dir='artifacts')

@app.get("/")
async def root():
    return {"message": "Framingham CHD Risk API", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": predictor is not None,
        "shap_available": (
            predictor.shap_available if predictor else False
        ),
    }

@app.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    info = predictor.get_model_info()
    m = info['metrics']
    return ModelInfo(
        model_type=info['model_type'],
        n_features=info['n_features'],
        roc_auc=m['roc_auc'],
        sensitivity=m['sensitivity'],
        specificity=m['specificity'],
        shap_available=info['shap_available']
    )

@app.post("/predict", response_model=RiskPrediction)
async def predict_risk(patient: PatientInput):
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        return RiskPrediction(**predictor.predict_risk(patient.dict()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain")
async def explain_prediction(patient: PatientInput, top_n: int = 10):
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if not predictor.shap_available:
        raise HTTPException(
            status_code=404, detail="SHAP explainer not available"
        )
    try:
        return predictor.explain_prediction(patient.dict(), top_n=top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assess", response_model=FullAssessmentResponse)
async def full_assessment(patient: PatientInput):
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        patient_dict = patient.dict()
        prediction = predictor.predict_risk(patient_dict)
        explanation = (
            predictor.explain_prediction(patient_dict, top_n=10)
            if predictor.shap_available else None
        )
        recommendations = predictor.get_clinical_recommendations(
            patient_dict, prediction
        )
        return FullAssessmentResponse(
            patient_input=patient_dict,
            risk_prediction=RiskPrediction(**prediction),
            explanation=(
                ExplanationResponse(**explanation) if explanation else None
            ),
            recommendations=recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch/predict")
async def batch_predict(patients: List[PatientInput]):
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        return [
            {"patient": p.dict(), "prediction": predictor.predict_risk(p.dict())}
            for p in patients
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk-categories")
async def get_risk_categories():
    return {
        "categories": [
            {"name": "Low",       "range": "< 10%",  "color": "green"},
            {"name": "Moderate",  "range": "10-20%", "color": "yellow"},
            {"name": "High",      "range": "20-30%", "color": "orange"},
            {"name": "Very High", "range": "> 30%",  "color": "red"},
        ]
    }

def main():
    uvicorn.run(
        "api:app", host="0.0.0.0", port=80,
        reload=False, log_level="info"
    )

if __name__ == "__main__":
    main()
