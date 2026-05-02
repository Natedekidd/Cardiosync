# CardioSync AI — Framingham CHD Risk Prediction

10-year coronary heart disease (CHD) risk prediction using the Framingham Heart Study dataset, with SHAP explainability and a REST API.

---

## Project Structure

```
cardiosync-ai-framingam/
├── data/
│   └── framingham_heart_study.csv
├── notebooks/
│   ├── 01_data_eda_features.ipynb      # EDA and feature analysis
│   └── 02_model_train_eval.ipynb       # Training, evaluation, SHAP
├── src/
│   ├── model.py                        # FraminghamPredictor class
│   ├── train.py                        # Standalone training script
│   └── api.py                          # FastAPI backend
├── artifacts/                          # Saved model artifacts
├── outputs/                            # Plots from notebooks
├── Makefile
├── Dockerfile
└── pyproject.toml
```

---

## Model Results

| Model | ROC-AUC | PR-AUC | Sensitivity | Specificity |
|-------|---------|--------|-------------|-------------|
| **Logistic Regression** (primary) | 0.699 | **0.305** | 0.597 | 0.673 |
| Ensemble (soft-voting) | 0.687 | 0.301 | 0.504 | 0.705 |
| XGBoost (Optuna-tuned) | 0.684 | 0.294 | 0.612 | 0.658 |
| CatBoost (Optuna-tuned) | 0.691 | 0.288 | 0.605 | 0.663 |
| Random Forest | 0.649 | 0.272 | 0.233 | 0.802 |

Primary metric: **PR-AUC** (best for severely imbalanced data).
Random baseline PR-AUC = 0.152 (15.2% CHD prevalence). Our best model achieves 2x that baseline.

---

## Why Results Are Lower Than Naive Benchmarks

Some published notebooks on this dataset report F1 scores above 90%. These results are artefacts of **data leakage**: they upsample or duplicate minority-class samples *before* splitting into train and test sets, so the test set contains exact copies of training samples. The model effectively memorises the training data and achieves artificially inflated scores.

The honest picture for this dataset:

- **Class imbalance is severe**: 3,596 patients without CHD vs 644 with CHD (5.6:1 ratio).
- **10-year prediction is inherently noisy**: many risk factors are shared between cases and controls; early-stage risk is not always distinguishable.
- **Small dataset**: 4,240 patients total with 9–18% missing values in key variables (glucose, education, BMI, cigarettes per day).
- **No leakage**: data is split *first* (stratified 80/20), imputation and normalisation are fit only on the training set, and evaluation happens on the held-out test set.

A PR-AUC of 0.30 vs a random baseline of 0.15 represents a genuine 2x improvement in detecting true CHD cases. In a screening context, the model catches 60% of CHD cases at a 67% specificity, which is clinically meaningful as a triage tool.

---

## Methodology

| Step | Choice | Reason |
|------|--------|--------|
| Missing values | KNNImputer (k=5, distance-weighted) | Preserves inter-feature relationships |
| Normalisation | PowerTransformer (Yeo-Johnson) | Corrects skewed medical distributions |
| Class imbalance | Class weights (no SMOTE) | Industry standard; avoids synthetic data risk |
| Split | Stratified 80/20, split first | Prevents data leakage |
| Tuning | Optuna (50 trials, XGBoost + CatBoost) | Efficient Bayesian search |
| Ensemble | Soft-voting (LR + RF + XGBoost + CatBoost) | Diverse learners |
| Primary metrics | PR-AUC + Sensitivity | Right choice for severe imbalance |
| Explainability | SHAP LinearExplainer (Logistic Regression) | Exact attribution for the deployed model |

### Feature Engineering

Two derived clinical features are added to the original 15:
- `pulse_pressure = sysBP - diaBP` — marker of arterial stiffness
- `pack_years = (cigsPerDay / 20) * (age - 18)` — cumulative smoking burden

---

## Setup

### Requirements
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker (for containerised deployment)
- `make` (for Makefile commands)

### Install dependencies

```bash
make install
# or: uv sync
```

### Run notebooks

```bash
uv run jupyter notebook
```

Open `notebooks/01_data_eda_features.ipynb` for EDA, then `notebooks/02_model_train_eval.ipynb` for training.

---

## Running the API

All commands run from the **project root** (`cardiosync-ai-framingam/`).

### Start locally

```bash
make api
# or: uv run uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### Makefile commands

```bash
make help          # list all commands

make install       # install dependencies
make api           # start local API on port 8000
make health        # health check (local)

make docker-build  # build Docker image
make docker-run    # run container on port 8000
make docker-stop   # stop and remove container
make docker-logs   # stream container logs
make health-docker # health check (Docker)
```

---

## API Endpoints

All endpoints accept and return JSON. The same patient input schema is used across all prediction endpoints.

### Patient Input Schema

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `age` | int | 20–100 | Age in years |
| `male` | int | 0 or 1 | Sex (1 = male, 0 = female) |
| `education` | int | 1–4 | Education level (1 = lowest, 4 = highest) |
| `currentSmoker` | int | 0 or 1 | Currently smoking |
| `cigsPerDay` | int | 0–100 | Cigarettes per day (0 if non-smoker) |
| `BPMeds` | int | 0 or 1 | On blood pressure medication |
| `prevalentStroke` | int | 0 or 1 | Prior stroke history |
| `prevalentHyp` | int | 0 or 1 | Established hypertension |
| `diabetes` | int | 0 or 1 | Diabetes diagnosis |
| `totChol` | float | 100–600 | Total cholesterol (mg/dL) |
| `sysBP` | float | 80–250 | Systolic blood pressure (mmHg) |
| `diaBP` | float | 40–150 | Diastolic blood pressure (mmHg) |
| `BMI` | float | 15–60 | Body mass index |
| `heartRate` | float | 40–200 | Resting heart rate (bpm) |
| `glucose` | float | 40–400 | Fasting glucose (mg/dL) |

---

### `GET /`
Confirms the server is running.

```bash
curl http://localhost:8000/
# {"message": "Framingham CHD Risk API", "docs": "/docs"}
```

---

### `GET /health`
Confirms the model and SHAP explainer loaded successfully. Call this before sending predictions to verify the service is ready.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "model_loaded": true,
  "shap_available": true
}
```

---

### `GET /model/info`
Returns metadata about the deployed model — type, number of features, and all test-set performance metrics.

```bash
curl http://localhost:8000/model/info
```

```json
{
  "model_type": "Logistic Regression",
  "n_features": 17,
  "roc_auc": 0.699,
  "sensitivity": 0.597,
  "specificity": 0.673,
  "shap_available": true
}
```

---

### `GET /risk-categories`
Returns the four risk tier definitions used to classify predictions.

```bash
curl http://localhost:8000/risk-categories
```

```json
{
  "categories": [
    {"name": "Low",       "range": "< 10%",  "color": "green"},
    {"name": "Moderate",  "range": "10-20%", "color": "yellow"},
    {"name": "High",      "range": "20-30%", "color": "orange"},
    {"name": "Very High", "range": "> 30%",  "color": "red"}
  ]
}
```

---

### `POST /predict`
Core prediction endpoint. Takes a single patient's data and returns a 10-year CHD risk score. Fast and lightweight — no SHAP computation.

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 55, "male": 1, "education": 2,
    "currentSmoker": 1, "cigsPerDay": 20,
    "BPMeds": 0, "prevalentStroke": 0,
    "prevalentHyp": 1, "diabetes": 0,
    "totChol": 250, "sysBP": 145, "diaBP": 92,
    "BMI": 28.5, "heartRate": 80, "glucose": 95
  }'
```

```json
{
  "risk_probability": 0.38,
  "risk_percentage": 38.0,
  "risk_category": "Very High",
  "binary_prediction": 1,
  "confidence": 0.76
}
```

**Response fields:**

| Field | Description |
|-------|-------------|
| `risk_probability` | Model output between 0 and 1 (e.g. 0.38 = 38% risk) |
| `risk_percentage` | Same value expressed as a percentage |
| `risk_category` | Low / Moderate / High / Very High based on risk tiers above |
| `binary_prediction` | 0 (no CHD predicted) or 1 (CHD predicted) at 0.5 threshold |
| `confidence` | How far the prediction is from the decision boundary — 0 = highly uncertain, 1 = highly certain |

---

### `POST /explain?top_n=10`
Runs SHAP on the patient and returns which features drove the prediction up or down. The `top_n` query parameter controls how many features to return (default 10, max 17).

```bash
curl -X POST "http://localhost:8000/explain?top_n=5" \
  -H "Content-Type: application/json" \
  -d '{ ...patient data... }'
```

```json
{
  "base_value": -0.36,
  "prediction": 0.89,
  "top_features": [
    {"feature": "age",        "contribution": 0.42, "impact": "Increases risk", "magnitude": 0.42},
    {"feature": "sysBP",      "contribution": 0.18, "impact": "Increases risk", "magnitude": 0.18},
    {"feature": "pack_years", "contribution": 0.15, "impact": "Increases risk", "magnitude": 0.15},
    {"feature": "diaBP",      "contribution": -0.08, "impact": "Decreases risk", "magnitude": 0.08},
    {"feature": "BMI",        "contribution": 0.06, "impact": "Increases risk", "magnitude": 0.06}
  ]
}
```

**Response fields:**

| Field | Description |
|-------|-------------|
| `base_value` | The model's average prediction across the training set (log-odds scale) |
| `prediction` | This patient's score = `base_value + sum(all contributions)` |
| `top_features` | Features ranked by absolute impact, largest first |
| `feature` | Feature name |
| `contribution` | Positive = pushes toward CHD risk, negative = pushes away from CHD risk |
| `impact` | Human-readable direction: "Increases risk" or "Decreases risk" |
| `magnitude` | Absolute value of contribution — used for ranking |

---

### `POST /assess`
Full pipeline in a single call: runs `/predict` + `/explain` + generates clinical recommendations based on the patient's specific values. This is the most useful endpoint for a complete patient report.

```bash
curl -X POST http://localhost:8000/assess \
  -H "Content-Type: application/json" \
  -d '{ ...patient data... }'
```

```json
{
  "patient_input": { "age": 55, "male": 1, "...": "..." },
  "risk_prediction": {
    "risk_probability": 0.38,
    "risk_percentage": 38.0,
    "risk_category": "Very High",
    "binary_prediction": 1,
    "confidence": 0.76
  },
  "explanation": {
    "base_value": -0.36,
    "prediction": 0.89,
    "top_features": [ "..." ]
  },
  "recommendations": [
    "VERY HIGH RISK: Immediate cardiology consultation recommended.",
    "Smoking cessation is critical (reduces CHD risk by 50% within 1 year).",
    "Blood pressure management required (target <130/80 mmHg).",
    "Lipid management needed (target LDL <100 mg/dL).",
    "Regular exercise (150 min/week) and Mediterranean diet are advised.",
    "Discuss aspirin, statins, and ACE inhibitors with your physician."
  ]
}
```

Recommendations are rule-based and triggered by the patient's specific values — smoking status, blood pressure, cholesterol, glucose, BMI, and overall risk category.

---

### `POST /batch/predict`
Runs `/predict` on a list of patients in a single request. Useful for scoring a cohort at once.

```bash
curl -X POST http://localhost:8000/batch/predict \
  -H "Content-Type: application/json" \
  -d '[
    {"age": 55, "male": 1, "...": "..."},
    {"age": 42, "male": 0, "...": "..."}
  ]'
```

Returns an array of `{"patient": {...}, "prediction": {...}}` objects, one per input patient.

---

### Quick Reference

| Goal | Endpoint |
|------|----------|
| Is the service up? | `GET /health` |
| What model is deployed? | `GET /model/info` |
| Just get a risk score | `POST /predict` |
| Understand why the score is what it is | `POST /explain` |
| Full report (score + SHAP + recommendations) | `POST /assess` |
| Score many patients at once | `POST /batch/predict` |

---

## Docker

### Build and run

```bash
make docker-build
make docker-run

# or manually:
docker build -t cardiosync-ai .
docker run -d --name cardiosync-ai -p 8000:80 cardiosync-ai
```

FastAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Useful Docker commands

```bash
make docker-logs   # stream container logs
make docker-stop   # stop and remove container
make health-docker # health check against container
```

---

## Artifacts

| File | Description |
|------|-------------|
| `best_model.pkl` | Logistic Regression (primary model) |
| `preprocessor.pkl` | KNN imputer + PowerTransformer pipeline |
| `shap_explainer.pkl` | SHAP LinearExplainer (Logistic Regression) |
| `metrics.json` | Performance metrics |
| `feature_names.json` | Ordered feature list |
| `feature_groups.json` | Continuous / categorical split |
| `feature_importance.csv` | SHAP-ranked feature importance |
| `model_comparison.csv` | All models performance comparison |

---


