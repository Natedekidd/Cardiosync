"""
Framingham CHD Risk Prediction - training pipeline.

Methodology:
- KNN imputation (k=5, distance-weighted)
- PowerTransformer (Yeo-Johnson) normalisation
- Class weights for imbalance (no SMOTE)
- Optuna Bayesian hyperparameter optimisation
- 5-fold stratified cross-validation
- Soft-voting ensemble (LR + RF + XGBoost + CatBoost)
"""

import pandas as pd
import numpy as np
import joblib
import json
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

from sklearn.impute import KNNImputer
from sklearn.preprocessing import PowerTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_val_score
)
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    confusion_matrix, f1_score
)
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
import optuna
import shap

DATA_PATH = 'data/framingham_heart_study.csv'
ARTIFACTS_DIR = Path('artifacts')
RANDOM_STATE = 42
N_TRIALS = 50

def load_data():
    df = pd.read_csv(DATA_PATH)
    X = df.drop('TenYearCHD', axis=1).copy()
    y = df['TenYearCHD']

    X['pulse_pressure'] = X['sysBP'] - X['diaBP']

    def pack_years(row):
        if row['currentSmoker'] == 1 and pd.notna(row['cigsPerDay']):
            return (row['cigsPerDay'] / 20) * max(0, row['age'] - 18)
        return 0.0

    X['pack_years'] = X.apply(pack_years, axis=1)
    return X, y

def build_preprocessor(continuous_features, categorical_features):
    return ColumnTransformer([
        ('cont', Pipeline([
            ('impute', KNNImputer(n_neighbors=5, weights='distance')),
            ('scale',  PowerTransformer(method='yeo-johnson'))
        ]), continuous_features),
        ('cat', Pipeline([
            ('impute', KNNImputer(n_neighbors=5, weights='distance'))
        ]), categorical_features)
    ])

def tune_xgboost(X_train, y_train, pos_weight, cv):
    def objective(trial):
        params = {
            'n_estimators':     trial.suggest_int('n_estimators', 100, 500),
            'max_depth':        trial.suggest_int('max_depth', 3, 8),
            'learning_rate':    trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'subsample':        trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'gamma':            trial.suggest_float('gamma', 0, 5),
            'scale_pos_weight': pos_weight,
            'random_state':     RANDOM_STATE,
            'eval_metric':      'logloss',
        }
        return cross_val_score(
            XGBClassifier(**params), X_train, y_train,
            cv=cv, scoring='roc_auc'
        ).mean()

    study = optuna.create_study(direction='maximize')
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)
    return study.best_params

def tune_catboost(X_train, y_train, cv):
    def objective(trial):
        params = {
            'iterations':         trial.suggest_int('iterations', 100, 500),
            'depth':              trial.suggest_int('depth', 3, 8),
            'learning_rate':      trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'l2_leaf_reg':        trial.suggest_float('l2_leaf_reg', 1e-3, 10, log=True),
            'auto_class_weights': 'Balanced',
            'random_state':       RANDOM_STATE,
            'verbose':            0,
        }
        return cross_val_score(
            CatBoostClassifier(**params), X_train, y_train,
            cv=cv, scoring='roc_auc'
        ).mean()

    study = optuna.create_study(direction='maximize')
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)
    return study.best_params

def run():
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    X, y = load_data()

    continuous_features = [c for c in X.columns if X[c].nunique() >= 10]
    categorical_features = [c for c in X.columns if c not in continuous_features]
    feature_names = continuous_features + categorical_features

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    preprocessor = build_preprocessor(continuous_features, categorical_features)
    X_train_prep = pd.DataFrame(
        preprocessor.fit_transform(X_train), columns=feature_names
    )
    X_test_prep = pd.DataFrame(
        preprocessor.transform(X_test), columns=feature_names
    )

    y_train_r = y_train.reset_index(drop=True)
    y_test_r  = y_test.reset_index(drop=True)

    pos_weight = (y_train_r == 0).sum() / (y_train_r == 1).sum()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    print('Tuning XGBoost ...')
    best_xgb = tune_xgboost(X_train_prep, y_train_r, pos_weight, cv)

    print('Tuning CatBoost ...')
    best_cat = tune_catboost(X_train_prep, y_train_r, cv)
    best_cat.update({'auto_class_weights': 'Balanced',
                     'random_state': RANDOM_STATE, 'verbose': 0})

    xgb_model = XGBClassifier(
        **best_xgb, scale_pos_weight=pos_weight,
        random_state=RANDOM_STATE, eval_metric='logloss'
    )
    cat_model = CatBoostClassifier(**best_cat)
    rf_model  = RandomForestClassifier(
        n_estimators=200, max_depth=10, min_samples_split=5,
        min_samples_leaf=2, class_weight='balanced',
        random_state=RANDOM_STATE
    )
    lr_model  = LogisticRegression(
        max_iter=1000, class_weight='balanced', random_state=RANDOM_STATE
    )
    ensemble  = VotingClassifier(
        estimators=[
            ('lr', lr_model), ('rf', rf_model),
            ('xgb', xgb_model), ('cat', cat_model)
        ],
        voting='soft'
    )

    models = {
        'Logistic Regression': lr_model,
        'Random Forest': rf_model,
        'XGBoost': xgb_model,
        'CatBoost': cat_model,
        'Ensemble': ensemble,
    }

    print('Training all models ...')
    for name, model in models.items():
        model.fit(X_train_prep, y_train_r)
        print(f'  {name}')

    results = {}
    for name, model in models.items():
        proba = model.predict_proba(X_test_prep)[:, 1]
        pred  = model.predict(X_test_prep)
        results[name] = {
            'roc_auc': roc_auc_score(y_test_r, proba),
            'pr_auc':  average_precision_score(y_test_r, proba),
            'f1':      f1_score(y_test_r, pred),
        }
        print(f"  {name:22s}: ROC-AUC={results[name]['roc_auc']:.4f}  PR-AUC={results[name]['pr_auc']:.4f}")

    best_name  = max(results, key=lambda n: results[n]['pr_auc'])
    best_model = models[best_name]
    print(f'\nBest model: {best_name} (PR-AUC={results[best_name]["pr_auc"]:.4f})')

    cm = confusion_matrix(y_test_r, best_model.predict(X_test_prep))
    tn, fp, fn, tp = cm.ravel()
    sensitivity = tp / (tp + fn)
    specificity = tn / (tn + fp)

    background   = shap.sample(X_train_prep, 50, random_state=RANDOM_STATE)
    explainer    = shap.Explainer(xgb_model.predict_proba, background)
    X_shap       = X_test_prep.sample(200, random_state=RANDOM_STATE).reset_index(drop=True)
    shap_exp_obj = explainer(X_shap)
    shap_values  = shap_exp_obj.values[:, :, 1]

    feature_importance = pd.DataFrame({
        'Feature': X_shap.columns,
        'Mean_SHAP': np.abs(shap_values).mean(axis=0)
    }).sort_values('Mean_SHAP', ascending=False).reset_index(drop=True)

    joblib.dump(best_model,  ARTIFACTS_DIR / 'best_model.pkl')
    joblib.dump(preprocessor, ARTIFACTS_DIR / 'preprocessor.pkl')
    joblib.dump(explainer,    ARTIFACTS_DIR / 'shap_explainer.pkl')

    with open(ARTIFACTS_DIR / 'feature_names.json', 'w') as f:
        json.dump(feature_names, f, indent=2)
    with open(ARTIFACTS_DIR / 'feature_groups.json', 'w') as f:
        json.dump({
            'continuous': continuous_features,
            'categorical': categorical_features
        }, f, indent=2)

    best_r = results[best_name]
    metrics_out = {
        'primary_model': best_name,
        'optimal_threshold': 0.5,
        'at_default_threshold_0.5': {
            'sensitivity': float(sensitivity),
            'specificity': float(specificity),
            'ppv': float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0,
            'npv': float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0,
            'roc_auc':   float(best_r['roc_auc']),
            'pr_auc':    float(best_r['pr_auc']),
            'f1_binary': float(best_r['f1']),
        },
    }
    with open(ARTIFACTS_DIR / 'metrics.json', 'w') as f:
        json.dump(metrics_out, f, indent=2)

    feature_importance.to_csv(ARTIFACTS_DIR / 'feature_importance.csv', index=False)
    np.save(ARTIFACTS_DIR / 'shap_values.npy', shap_values)

    print('\nArtifacts saved to artifacts/')

if __name__ == "__main__":
    run()
