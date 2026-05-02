"""
Framingham CHD Risk Prediction - production predictor.
"""

import pandas as pd
import joblib
import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_ARTIFACTS = Path(__file__).resolve().parent.parent / 'artifacts'

class FraminghamPredictor:

    def __init__(self, artifacts_dir=None):
        self.artifacts_dir = Path(artifacts_dir) if artifacts_dir else _DEFAULT_ARTIFACTS

        self.model = joblib.load(self.artifacts_dir / 'best_model.pkl')
        self.preprocessor = joblib.load(self.artifacts_dir / 'preprocessor.pkl')

        try:
            self.explainer = joblib.load(self.artifacts_dir / 'shap_explainer.pkl')
            self.shap_available = True
        except FileNotFoundError:
            self.explainer = None
            self.shap_available = False

        with open(self.artifacts_dir / 'feature_names.json') as f:
            self.feature_names = json.load(f)

        with open(self.artifacts_dir / 'feature_groups.json') as f:
            groups = json.load(f)
            self.continuous_features = groups['continuous']
            self.categorical_features = groups['categorical']

        with open(self.artifacts_dir / 'metrics.json') as f:
            raw = json.load(f)

        self.metrics = {
            'primary_model': raw['primary_model'],
            'optimal_threshold': raw['optimal_threshold'],
            'roc_auc':     raw['at_default_threshold_0.5']['roc_auc'],
            'pr_auc':      raw['at_default_threshold_0.5']['pr_auc'],
            'sensitivity': raw['at_default_threshold_0.5']['sensitivity'],
            'specificity': raw['at_default_threshold_0.5']['specificity'],
            'ppv':         raw['at_default_threshold_0.5']['ppv'],
            'npv':         raw['at_default_threshold_0.5']['npv'],
            'f1':          raw['at_default_threshold_0.5']['f1_binary'],
        }

    def preprocess_input(self, patient_data: Dict) -> pd.DataFrame:
        df = pd.DataFrame([patient_data])

        df['pulse_pressure'] = df['sysBP'] - df['diaBP']

        def _pack_years(row):
            if row.get('currentSmoker', 0) == 1 and pd.notna(row.get('cigsPerDay')):
                return (row['cigsPerDay'] / 20) * max(0, row['age'] - 18)
            return 0.0

        df['pack_years'] = df.apply(_pack_years, axis=1)

        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0

        df = df[self.feature_names]
        X = self.preprocessor.transform(df)
        return pd.DataFrame(X, columns=self.feature_names)

    def predict_risk(self, patient_data: Dict) -> Dict:
        X = self.preprocess_input(patient_data)

        risk_prob = self.model.predict_proba(X)[0, 1]
        risk_pct = risk_prob * 100
        binary_pred = self.model.predict(X)[0]

        if risk_pct < 10:
            category = 'Low'
        elif risk_pct < 20:
            category = 'Moderate'
        elif risk_pct < 30:
            category = 'High'
        else:
            category = 'Very High'

        return {
            'risk_probability': float(risk_prob),
            'risk_percentage':  float(risk_pct),
            'risk_category':    category,
            'binary_prediction': int(binary_pred),
            'confidence': float(abs(risk_prob - 0.5) * 2)
        }

    def explain_prediction(self, patient_data: Dict, top_n: int = 10) -> Optional[Dict]:
        if not self.shap_available:
            return None

        X = self.preprocess_input(patient_data)

        shap_exp_obj = self.explainer(X)
        sv = shap_exp_obj.values[0, :]
        base_val = float(shap_exp_obj.base_values[0])

        contributions = sorted([
            {
                'feature':     feat,
                'contribution': float(val),
                'impact':      'Increases risk' if val > 0 else 'Decreases risk',
                'magnitude':   abs(float(val))
            }
            for feat, val in zip(self.feature_names, sv)
        ], key=lambda x: x['magnitude'], reverse=True)

        return {
            'base_value':   base_val,
            'prediction':   base_val + sum(c['contribution'] for c in contributions),
            'top_features': contributions[:top_n],
            'all_features': contributions
        }

    def get_clinical_recommendations(self, patient_data: Dict, risk_result: Dict) -> List[str]:
        rec = []
        cat = risk_result['risk_category']

        if cat == 'Very High':
            rec.append('VERY HIGH RISK: Immediate cardiology consultation recommended.')
        elif cat == 'High':
            rec.append('HIGH RISK: Cardiology evaluation recommended within 1-3 months.')
        elif cat == 'Moderate':
            rec.append('MODERATE RISK: Regular monitoring and lifestyle modifications advised.')
        else:
            rec.append('LOW RISK: Continue healthy lifestyle and routine screening.')

        if patient_data.get('currentSmoker', 0) == 1:
            rec.append('Smoking cessation is critical (reduces CHD risk by 50% within 1 year).')

        if patient_data.get('sysBP', 0) >= 140 or patient_data.get('diaBP', 0) >= 90:
            rec.append('Blood pressure management required (target <130/80 mmHg).')

        if patient_data.get('totChol', 0) >= 240:
            rec.append('Lipid management needed (target LDL <100 mg/dL).')

        if patient_data.get('BMI', 0) >= 30:
            rec.append('Weight reduction recommended (target BMI <25).')

        if patient_data.get('glucose', 0) >= 126 or patient_data.get('diabetes', 0) == 1:
            rec.append('Glucose control is critical (target HbA1c <7%).')

        rec.append('Regular exercise (150 min/week) and Mediterranean diet are advised.')

        if cat in ('High', 'Very High'):
            rec.append('Discuss aspirin, statins, and ACE inhibitors with your physician.')

        return rec

    def batch_predict(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        results = [self.predict_risk(row.to_dict()) for _, row in patients_df.iterrows()]
        return pd.concat([patients_df.reset_index(drop=True), pd.DataFrame(results)], axis=1)

    def get_model_info(self) -> Dict:
        return {
            'model_type':    self.metrics['primary_model'],
            'features':      self.feature_names,
            'n_features':    len(self.feature_names),
            'metrics':       self.metrics,
            'shap_available': self.shap_available
        }
