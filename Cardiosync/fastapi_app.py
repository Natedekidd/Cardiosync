"""
CardioSync - FastAPI Backend
Bridges the React UI with all backend services:
- Auth (SQLite via auth_system.py)
- AI Risk Prediction (AI guy's Framingham model)
- Genomics (vcf_parser.py + gene_database.py)
- Environment (api_client.py)
- Messaging (messaging_client.py)
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import httpx
import secrets
import json
from datetime import datetime

# ── Import your existing modules ──────────────────────────────────────────────
from auth_system import AuthSystem
from api_client import get_air_quality, calculate_environmental_risk

try:
    from vcf_parser import VCFParser
    from gene_database import GeneDatabase
    VCF_AVAILABLE = True
except ImportError:
    VCF_AVAILABLE = False

try:
    from messaging_client import (
        send_whatsapp_message,
        send_sms_message,
        create_whatsapp_report_summary,
        create_sms_report_summary,
        is_twilio_configured,
        validate_phone_number,
    )
    MESSAGING_AVAILABLE = True
except ImportError:
    MESSAGING_AVAILABLE = False

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CardioSync API",
    description="Precision Digital Twin for Cardiovascular Care",
    version="0.1.0",
)

# Allow React dev server to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://cardiosync.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_system = AuthSystem()
security = HTTPBearer()

# ── AI model endpoint (your AI guy's FastAPI) ─────────────────────────────────
# Change this URL if he deploys it online
AI_API_URL = "http://127.0.0.1:8000"

# ── Simple in-memory session store (replace with Redis for production) ────────
active_sessions: dict[str, dict] = {}


# ── Pydantic models (request/response shapes) ─────────────────────────────────

class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str
    consent_given: bool

class LoginRequest(BaseModel):
    email: str
    password: str

class PatientDataRequest(BaseModel):
    name: str
    age: int
    sex: str                          # "Male" | "Female"
    bp_systolic: int
    bp_diastolic: int
    total_cholesterol: int
    hdl: int
    ldl: int
    smoking: str                      # "Never" | "Former" | "Current"
    exercise_days: int
    diet_quality: str                 # "Poor" | "Fair" | "Good" | "Excellent"
    location: Optional[str] = None
    bmi: Optional[float] = None
    heart_rate: Optional[float] = None
    glucose: Optional[float] = None
    cigs_per_day: Optional[int] = 0
    bp_meds: Optional[int] = 0
    prevalent_stroke: Optional[int] = 0
    prevalent_hyp: Optional[int] = 0
    diabetes: Optional[int] = 0
    education: Optional[int] = 2

class SendMessageRequest(BaseModel):
    phone_number: str
    channel: str                      # "whatsapp" | "sms"
    patient_name: str
    total_risk: float
    risk_category: str
    recommendations: list[str]

class SimulationRequest(BaseModel):
    # Current patient values
    age: int
    sex: str
    bp_systolic: int
    bp_diastolic: int
    ldl: int
    total_cholesterol: int
    smoking: str
    exercise_days: int
    diet_quality: str
    bmi: Optional[float] = None
    heart_rate: Optional[float] = None
    glucose: Optional[float] = None
    cigs_per_day: Optional[int] = 0
    bp_meds: Optional[int] = 0
    prevalent_stroke: Optional[int] = 0
    prevalent_hyp: Optional[int] = 0
    diabetes: Optional[int] = 0
    education: Optional[int] = 2
    # Intervention values
    new_exercise_days: int
    new_diet_quality: str
    on_statin: bool = False
    quit_smoking: bool = False


# ── Auth helpers ───────────────────────────────────────────────────────────────

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = active_sessions.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "CardioSync API is running", "version": "0.1.0"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "vcf_available": VCF_AVAILABLE,
        "messaging_available": MESSAGING_AVAILABLE,
    }


# ══════════════════════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/auth/signup")
def signup(body: SignupRequest):
    if not body.consent_given:
        raise HTTPException(status_code=400, detail="Consent is required")

    success, message, user_id = auth_system.register_user(
        body.email, body.password, body.full_name
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@app.post("/auth/login")
def login(body: LoginRequest):
    success, message, user_data = auth_system.login_user(body.email, body.password)
    if not success:
        raise HTTPException(status_code=401, detail=message)

    # Create a session token
    token = secrets.token_hex(32)
    active_sessions[token] = user_data

    return {
        "success": True,
        "token": token,
        "user": {
            "user_id": user_data["user_id"],
            "full_name": user_data["full_name"],
            "email": user_data["email"],
        },
    }


@app.post("/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    active_sessions.pop(token, None)
    return {"success": True, "message": "Logged out"}


@app.delete("/auth/account")
def delete_account(user=Depends(get_current_user)):
    success, message = auth_system.delete_user_account(user["user_id"])
    if not success:
        raise HTTPException(status_code=400, detail=message)
    # Remove session
    for token, u in list(active_sessions.items()):
        if u["user_id"] == user["user_id"]:
            del active_sessions[token]
    return {"success": True, "message": message}


# ══════════════════════════════════════════════════════════════════════════════
# PATIENT DATA ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/patient")
def save_patient(body: PatientDataRequest, user=Depends(get_current_user)):
    success, message = auth_system.save_patient_data(user["user_id"], body.dict())
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"success": True, "message": message}


@app.get("/patient")
def get_patient(user=Depends(get_current_user)):
    data = auth_system.get_patient_data(user["user_id"])
    if not data:
        return {"patient": None}
    return {"patient": data}


# ══════════════════════════════════════════════════════════════════════════════
# RISK ANALYSIS ENDPOINT
# Calls the AI guy's /assess endpoint and enriches with genomics + environment
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/risk/assess")
async def assess_risk(body: PatientDataRequest, user=Depends(get_current_user)):

    # 1. ── Environmental risk ──────────────────────────────────────────────
    environmental_factor = 0
    air_quality_data = None
    if body.location:
        air_quality_data = get_air_quality(body.location)
        if air_quality_data:
            environmental_factor = calculate_environmental_risk(air_quality_data)
    
    # 1b. ── Genomic risk (from stored VCF data) ───────────────────────
    genomic_risk_percent = 0
    patient_data = auth_system.get_patient_data(user["user_id"])
    if patient_data and patient_data.get("genomic_risk"):
        genomic_risk_percent = float(patient_data["genomic_risk"])

    # 2. ── Build payload for AI guy's model ───────────────────────────────
    # Map our fields to Framingham schema
    ai_payload = {
    "age": max(20, int(body.age)),
    "male": 1 if body.sex == "Male" else 0,
    "education": int(body.education) if body.education else 2,
    "currentSmoker": 1 if body.smoking == "Current" else 0,
    "cigsPerDay": int(body.cigs_per_day) if body.cigs_per_day else (20 if body.smoking == "Current" else 0),
    "BPMeds": int(body.bp_meds) if body.bp_meds else 0,
    "prevalentStroke": int(body.prevalent_stroke) if body.prevalent_stroke else 0,
    "prevalentHyp": int(body.prevalent_hyp) if body.prevalent_hyp else (1 if body.bp_systolic >= 140 else 0),
    "diabetes": int(body.diabetes) if body.diabetes else 0,
    "totChol": float(body.total_cholesterol),
    "sysBP": float(body.bp_systolic),
    "diaBP": float(body.bp_diastolic),
    "BMI": float(body.bmi) if body.bmi else 26.0,
    "heartRate": float(body.heart_rate) if body.heart_rate else 75.0,
    "glucose": float(body.glucose) if body.glucose else 85.0,
}

    # 3. ── Call AI model ───────────────────────────────────────────────────
    ai_result = None
    ai_error = None
    try:
        print("AI PAYLOAD:", ai_payload)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{AI_API_URL}/assess", json=ai_payload)
            resp.raise_for_status()
            ai_result = resp.json()
    except Exception as e:
        # If AI model is offline, fall back to formula-based calculation
        ai_error = str(e)
        ai_result = _fallback_risk_calculation(body, environmental_factor)

    # 4. ── Add environmental layer on top of AI score ─────────────────────
    base_risk = ai_result["risk_prediction"]["risk_percentage"]
    total_risk = min(base_risk + environmental_factor + genomic_risk_percent, 99.0)

    # Update risk category based on adjusted total
    if total_risk < 10:
        risk_category = "Low"
    elif total_risk < 20:
        risk_category = "Moderate"
    elif total_risk < 30:
        risk_category = "High"
    else:
        risk_category = "Very High"

    # 5. ── Save to DB ──────────────────────────────────────────────────────
    auth_system.save_risk_assessment(
        user["user_id"],
        total_risk,
        base_risk,
        0,                    # genomic risk added separately via VCF
        environmental_factor,
    )

    return {
        "total_risk": round(total_risk, 1),
        "base_risk": round(base_risk, 1),
        "genomic_risk": round(genomic_risk_percent, 1),
        "environmental_factor": round(environmental_factor, 1),
        "risk_category": risk_category,
        "ai_explanation": ai_result.get("explanation"),
        "recommendations": ai_result.get("recommendations", []),
        "ai_model_used": ai_error is None,
        "fallback_used": ai_error is not None,
        "air_quality": air_quality_data,
    }


def _fallback_risk_calculation(body: PatientDataRequest, environmental_factor: float) -> dict:
    """Calibrated fallback to match Framingham AI model output range."""
    
    # Base score calibrated to Framingham model
    score = 0.0

    # Age contribution (strongest factor)
    if body.age < 35:
        score += 2.0
    elif body.age < 45:
        score += 8.0
    elif body.age < 55:
        score += 18.0
    elif body.age < 65:
        score += 30.0
    else:
        score += 45.0

    # Sex
    if body.sex == "Male":
        score += 5.0

    # Blood pressure
    if body.bp_systolic >= 160:
        score += 20.0
    elif body.bp_systolic >= 140:
        score += 12.0
    elif body.bp_systolic >= 130:
        score += 6.0
    elif body.bp_systolic >= 120:
        score += 2.0

    # Smoking
    if body.smoking == "Current":
        score += 20.0
        if (body.cigs_per_day or 0) >= 20:
            score += 8.0
    elif body.smoking == "Former":
        score += 4.0

    # Cholesterol
    if body.total_cholesterol >= 260:
        score += 8.0
    elif body.total_cholesterol >= 240:
        score += 5.0
    elif body.total_cholesterol >= 200:
        score += 2.0

    # Diabetes
    if body.diabetes:
        score += 15.0

    # Hypertension history
    if body.prevalent_hyp or body.bp_systolic >= 140:
        score += 8.0

    # Stroke history
    if body.prevalent_stroke:
        score += 20.0

    # BP meds
    if body.bp_meds:
        score += 10.0

    # BMI
    bmi = body.bmi or 26.0
    if bmi >= 35:
        score += 6.0
    elif bmi >= 30:
        score += 3.0

    # Glucose
    glucose = body.glucose or 85.0
    if glucose >= 180:
        score += 8.0
    elif glucose >= 126:
        score += 4.0

    # Exercise reduces risk
    score -= body.exercise_days * 1.5

    # Diet reduces risk
    diet_map = {"Poor": 3, "Fair": 1, "Good": -1, "Excellent": -3}
    score += diet_map.get(body.diet_quality, 0)

    # Clamp to realistic range
    total = max(1.0, min(score, 99.0))

    # Generate recommendations
    recommendations = []
    if body.smoking == "Current":
        recommendations.append("Smoking cessation is critical (reduces CHD risk by 50% within 1 year).")
    if body.bp_systolic >= 140:
        recommendations.append("Blood pressure management required (target <130/80 mmHg).")
    if body.total_cholesterol >= 240:
        recommendations.append("Lipid management needed (target LDL <100 mg/dL).")
    if body.diabetes:
        recommendations.append("Glucose control is critical (target HbA1c <7%).")
    if body.exercise_days < 3:
        recommendations.append("Regular exercise (150 min/week) and Mediterranean diet are advised.")
    if body.prevalent_stroke:
        recommendations.append("VERY HIGH RISK: Immediate cardiology consultation recommended.")
    if not recommendations:
        recommendations.append("Continue healthy lifestyle and routine screening.")

    return {
        "risk_prediction": {
            "risk_percentage": total,
            "risk_category": "Low" if total < 10 else "Moderate" if total < 20 else "High" if total < 30 else "Very High"
        },
        "explanation": None,
        "recommendations": recommendations,
    }

# ══════════════════════════════════════════════════════════════════════════════
# SIMULATION ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/risk/simulate")
async def simulate(body: SimulationRequest, user=Depends(get_current_user)):

    # Build current patient payload
    current_payload = {
        "age": body.age, "male": 1 if body.sex == "Male" else 0,
        "education": body.education, "currentSmoker": 1 if body.smoking == "Current" else 0,
        "cigsPerDay": body.cigs_per_day, "BPMeds": body.bp_meds,
        "prevalentStroke": body.prevalent_stroke, "prevalentHyp": body.prevalent_hyp,
        "diabetes": body.diabetes, "totChol": body.total_cholesterol,
        "sysBP": body.bp_systolic, "diaBP": body.bp_diastolic,
        "BMI": body.bmi or 26.0, "heartRate": body.heart_rate or 75,
        "glucose": body.glucose or 85,
    }

    # Build intervention payload
    intervention_payload = {**current_payload}
    intervention_payload["currentSmoker"] = 0 if body.quit_smoking else current_payload["currentSmoker"]
    intervention_payload["cigsPerDay"] = 0 if body.quit_smoking else body.cigs_per_day

    # Adjust BP slightly for statin effect
    if body.on_statin:
        intervention_payload["totChol"] = max(150, body.total_cholesterol - 40)

    async def get_risk(payload):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{AI_API_URL}/assess", json=payload)
                resp.raise_for_status()
                return resp.json()["risk_percentage"]
        except:
            # Fallback
            smoking = "Current" if payload["currentSmoker"] else "Never"
            exercise = body.new_exercise_days
            diet = body.new_diet_quality
            base = 10 + (body.age - 40) * 0.5
            base += (body.bp_systolic - 120) * 0.2
            base += (body.ldl - 100) * 0.05
            base += {"Never": 0, "Former": 3, "Current": 8}.get(smoking, 0)
            base += -1 * exercise
            base += {"Poor": 5, "Fair": 2, "Good": -1, "Excellent": -3}.get(diet, 0)
            if body.on_statin:
                base -= 5
            return max(1, min(base, 50))

    current_risk = await get_risk(current_payload)
    intervention_risk = await get_risk(intervention_payload)

    # Also apply lifestyle changes to intervention risk
    lifestyle_delta = 0
    lifestyle_delta += -1 * (body.new_exercise_days - body.exercise_days)
    diet_map = {"Poor": 5, "Fair": 2, "Good": -1, "Excellent": -3}
    lifestyle_delta += diet_map.get(body.new_diet_quality, 0) - diet_map.get(body.diet_quality, 0)

    intervention_risk = max(1, min(intervention_risk + lifestyle_delta, 99))

    # Generate 10-year trajectories
    years = list(range(0, 11))
    current_trajectory = [round(current_risk * (1 + 0.03 * y), 1) for y in years]
    intervention_trajectory = [round(intervention_risk * (1 + 0.02 * y), 1) for y in years]

    reduction = ((current_risk - intervention_risk) / current_risk * 100) if current_risk > 0 else 0

    return {
        "current_risk": round(current_risk, 1),
        "intervention_risk": round(intervention_risk, 1),
        "risk_reduction_percent": round(reduction, 1),
        "years": years,
        "current_trajectory": current_trajectory,
        "intervention_trajectory": intervention_trajectory,
    }


# ══════════════════════════════════════════════════════════════════════════════
# GENOMICS ENDPOINT (VCF upload - optional)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/genomics/analyze")
async def analyze_vcf(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not VCF_AVAILABLE:
        raise HTTPException(status_code=503, detail="Genomics module not available")

    contents = await file.read()
    vcf_text = contents.decode("utf-8")

    try:
        parser = VCFParser()
        gene_db = GeneDatabase()

        # Parse VCF
        genotypes = parser.parse_vcf_file(vcf_text)
        summary = parser.generate_summary_report(genotypes)

        # Calculate polygenic risk score
        prs_score, risk_variants, protective_variants = gene_db.calculate_polygenic_risk_score(genotypes)

        # Convert PRS to risk percentage addition
        # PRS 1.0 = average = 0% addition
        # PRS 2.0 = 2x risk = +15% addition
        # PRS 3.0+ = 3x risk = +28% addition
        genomic_risk_percent = max(0, (prs_score - 1.0) * 15)

        # Store genomic risk + genotypes in patient data
        import json
        auth_system.update_genomic_data(
            user["user_id"],
            genomic_risk_percent,
            json.dumps(genotypes)
        )

        return {
            "success": True,
            "total_variants_found": summary["total_variants_found"],
            "genes_covered": len(summary["genes_covered"]),
            "genomic_risk_score": round(prs_score, 2),
            "genomic_risk_percent": round(genomic_risk_percent, 1),
            "high_risk_variants": summary["high_risk_variants"][:10],
            "protective_variants": summary["protective_variants"][:5],
            "pharmacogenomic_variants": summary["pharmacogenomic_variants"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VCF parsing failed: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# PHARMACOGENOMICS ENDPOINT
# Returns drug recommendations — real if VCF uploaded, general if not
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/pharmacogenomics")
def get_pharmacogenomics(user=Depends(get_current_user)):
    import json
    patient_data = auth_system.get_patient_data(user["user_id"])
    
    # Check if VCF was uploaded
    if patient_data and patient_data.get("vcf_uploaded") and patient_data.get("genomic_genotypes"):
        try:
            genotypes = json.loads(patient_data["genomic_genotypes"])
            gene_db = GeneDatabase()
            drug_recs = gene_db.get_drug_recommendations(genotypes)
            prs, risk_variants, protective_variants = gene_db.calculate_polygenic_risk_score(genotypes)
            
            recommendations = []
            for drug in drug_recs['safe']:
                recommendations.append({
                    "drug": drug['drug'],
                    "recommendation": "Recommended",
                    "reason": drug['reason'],
                    "gene": None,
                    "absolute_benefit": "—",
                    "relative_benefit": "—",
                })
            for drug in drug_recs['caution']:
                recommendations.append({
                    "drug": drug['drug'],
                    "recommendation": "Caution",
                    "reason": drug['reason'],
                    "gene": None,
                    "absolute_benefit": "—",
                    "relative_benefit": "—",
                })
            for drug in drug_recs['avoid']:
                recommendations.append({
                    "drug": drug['drug'],
                    "recommendation": "Avoid",
                    "reason": drug['reason'],
                    "gene": None,
                    "absolute_benefit": "—",
                    "relative_benefit": "—",
                })
            
            return {
                "vcf_based": True,
                "recommendations": recommendations,
                "prs_score": round(prs, 2),
                "risk_variants": risk_variants[:5],
                "protective_variants": protective_variants[:5],
            }
        except Exception as e:
            print(f"Pharmacogenomics error: {e}")
    
    # No VCF — return general recommendations
    return {
        "vcf_based": False,
        "recommendations": [],
        "message": "Upload VCF for personalised recommendations",
    }

@app.post("/pharmacogenomics/personalized")
def get_personalized_pharmacogenomics(genomic_summary: dict, user=Depends(get_current_user)):
    """Personalised recommendations after VCF upload."""
    pharma_variants = genomic_summary.get("pharmacogenomic_variants", [])

    recommended = []
    caution = []
    avoid = []

    # Example logic — expand based on your gene_database data
    variant_genes = [v.get("gene") for v in pharma_variants]

    if "CYP2C19" in variant_genes:
        avoid.append({
            "drug": "Clopidogrel",
            "drug_class": "Antiplatelet",
            "reason": "CYP2C19 poor metabolizer — reduced efficacy",
            "alternative": "Use Prasugrel or Ticagrelor instead",
        })
        recommended.append({
            "drug": "Prasugrel",
            "drug_class": "Antiplatelet",
            "reason": "Preferred for CYP2C19 poor metabolizers",
            "note": "Does not require CYP2C19 for activation",
        })
    else:
        recommended.append({
            "drug": "Clopidogrel",
            "drug_class": "Antiplatelet",
            "reason": "Normal CYP2C19 metabolism detected",
            "note": "Standard dosing applies",
        })

    if "CYP2C9" in variant_genes or "VKORC1" in variant_genes:
        caution.append({
            "drug": "Warfarin",
            "drug_class": "Anticoagulant",
            "reason": "Genetic variant detected — requires dose adjustment",
            "note": "Start low, monitor INR closely",
        })

    recommended.append({
        "drug": "Atorvastatin",
        "drug_class": "Statin",
        "reason": "No SLCO1B1 risk variants detected" if "SLCO1B1" not in variant_genes else "SLCO1B1 variant — consider lower dose",
        "note": "Low risk of muscle-related side effects",
    })

    return {
        "has_genomic_data": True,
        "recommended": recommended,
        "caution": caution,
        "avoid": avoid,
    }


# ══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENTAL DATA ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/environment")
def get_environment(location: str):
    air_quality = get_air_quality(location)
    if not air_quality:
        return {"available": False, "location": location}

    risk_contribution = calculate_environmental_risk(air_quality)
    return {
        "available": True,
        "location": location,
        "air_quality": air_quality,
        "risk_contribution": risk_contribution,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MESSAGING ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/messaging/send")
def send_message(body: SendMessageRequest, user=Depends(get_current_user)):
    if not MESSAGING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Messaging module not available")

    if not is_twilio_configured():
        raise HTTPException(status_code=503, detail="Twilio not configured")

    is_valid, error_msg = validate_phone_number(body.phone_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    patient_mock = {"name": body.patient_name}

    if body.channel == "whatsapp":
        msg = create_whatsapp_report_summary(
            patient_mock, body.total_risk, 0, body.recommendations
        )
        success, message = send_whatsapp_message(body.phone_number, msg)
    elif body.channel == "sms":
        msg = create_sms_report_summary(patient_mock, body.total_risk)
        success, message = send_sms_message(body.phone_number, msg)
    else:
        raise HTTPException(status_code=400, detail="Channel must be 'whatsapp' or 'sms'")

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return {"success": True, "message": "Message sent successfully"}


# ══════════════════════════════════════════════════════════════════════════════
# RISK HISTORY ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/risk/history")
def get_risk_history(user=Depends(get_current_user)):
    history = auth_system.get_risk_history(user["user_id"])
    return {"history": history}


# ══════════════════════════════════════════════════════════════════════════════
# USER PROFILE ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/profile")
def get_profile(user=Depends(get_current_user)):
    profile = auth_system.get_user_profile(user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile}