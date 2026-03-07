#!/usr/bin/env python
"""
Evaluate both HOPE models (Stable + Fast) independently.
Shows side-by-side metrics and sample prediction comparison.
"""
import sys, os, logging
sys.path.insert(0, os.path.abspath('.'))

import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
import json

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def evaluate_model(model, X_val, y_val, name):
    """Evaluate a single model and return metrics dict."""
    y_pred_proba = model.predict(X_val, verbose=0).flatten()
    y_pred = (y_pred_proba > 0.5).astype(int)

    acc  = accuracy_score(y_val, y_pred)
    prec = precision_score(y_val, y_pred, zero_division=0)
    rec  = recall_score(y_val, y_pred, zero_division=0)
    f1   = f1_score(y_val, y_pred, zero_division=0)
    auc  = roc_auc_score(y_val, y_pred_proba)
    cm   = confusion_matrix(y_val, y_pred)

    return {
        'name': name,
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1': f1,
        'auc': auc,
        'confusion_matrix': cm,
        'sample_preds': y_pred_proba[:10],
    }


def main():
    logger.info("=" * 70)
    logger.info("HOPE MODEL EVALUATION — Stable vs Fast")
    logger.info("=" * 70)

    # Load feature columns
    with open('models/specialty_stats.json') as f:
        stats = json.load(f)
    feature_columns = stats['final_feature_columns']

    # Load feature store
    logger.info("Loading feature store...")
    df = pd.read_csv('data/processed/provider_features.csv')
    logger.info(f"Loaded {len(df)} providers")

    X = df[feature_columns].values

    # Generate same labels as recovery script
    z_cols = [c for c in df.columns if 'z_tanh' in c]
    if z_cols:
        combined = df[z_cols].abs().mean(axis=1)
        threshold = combined.quantile(0.95)
        y = (combined > threshold).astype(int).values
    else:
        mean_cps = df['cost_per_service'].mean()
        std_cps = df['cost_per_service'].std()
        z_scores = (df['cost_per_service'] - mean_cps) / std_cps
        y = (z_scores.abs() > 3.0).astype(int).values

    logger.info(f"Labels: {y.sum()} fraud ({y.mean()*100:.2f}%), {len(y)-y.sum()} clean")

    # Scale
    scaler = joblib.load('models/robust_scaler.joblib')
    X_scaled = scaler.transform(X).astype('float32')

    # Same validation split as recovery
    _, X_val, _, y_val = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"Validation set: {len(X_val)} samples")

    # Load both models
    logger.info("Loading models...")
    stable_model = tf.keras.models.load_model('models/fraud_detection_model.keras')
    fast_model   = tf.keras.models.load_model('models/fraud_detection_model_fast.keras')
    logger.info("Both models loaded.")

    # Evaluate each
    stable_metrics = evaluate_model(stable_model, X_val, y_val, "Stable (Slow)")
    fast_metrics   = evaluate_model(fast_model,   X_val, y_val, "Fast (Adaptive)")

    # Print comparison table
    print("\n" + "=" * 70)
    print(f"{'HOPE MODEL COMPARISON':^70}")
    print("=" * 70)
    print(f"{'Metric':<20} {'Stable (Slow)':>20} {'Fast (Adaptive)':>20}")
    print("-" * 70)
    for key in ['accuracy', 'precision', 'recall', 'f1', 'auc']:
        sv = stable_metrics[key]
        fv = fast_metrics[key]
        diff = fv - sv
        arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "=")
        print(f"{key.upper():<20} {sv:>20.4f} {fv:>20.4f}  {arrow} {abs(diff):.4f}")
    print("=" * 70)

    # Confusion matrices
    for m in [stable_metrics, fast_metrics]:
        cm = m['confusion_matrix']
        print(f"\n{m['name']} Confusion Matrix:")
        print(f"  TN={cm[0][0]:>8,}  FP={cm[0][1]:>8,}")
        print(f"  FN={cm[1][0]:>8,}  TP={cm[1][1]:>8,}")

    # Sample predictions comparison
    print(f"\n{'Sample Predictions (first 10 val providers)':^70}")
    print("-" * 70)
    print(f"{'Provider':<12} {'Actual':<10} {'Stable':>12} {'Fast':>12} {'Divergence':>12}")
    print("-" * 70)
    for i in range(10):
        s = stable_metrics['sample_preds'][i]
        f = fast_metrics['sample_preds'][i]
        actual = int(y_val[i])
        div = abs(f - s)
        alert = " ⚠️ EARLY WARNING" if div > 0.3 else ""
        print(f"{'#' + str(i+1):<12} {actual:<10} {s:>12.4f} {f:>12.4f} {div:>12.4f}{alert}")

    print("=" * 70)

    # Score distribution summary
    s_preds = stable_model.predict(X_val, verbose=0).flatten()
    f_preds = fast_model.predict(X_val, verbose=0).flatten()

    print(f"\n{'Score Distribution Summary':^70}")
    print("-" * 70)
    print(f"{'Statistic':<20} {'Stable':>20} {'Fast':>20}")
    print("-" * 70)
    print(f"{'Mean':.<20} {np.mean(s_preds):>20.4f} {np.mean(f_preds):>20.4f}")
    print(f"{'Median':.<20} {np.median(s_preds):>20.4f} {np.median(f_preds):>20.4f}")
    print(f"{'Std Dev':.<20} {np.std(s_preds):>20.4f} {np.std(f_preds):>20.4f}")
    print(f"{'Min':.<20} {np.min(s_preds):>20.4f} {np.min(f_preds):>20.4f}")
    print(f"{'Max':.<20} {np.max(s_preds):>20.4f} {np.max(f_preds):>20.4f}")
    print(f"{'> 0.7 (HIGH)':.<20} {(s_preds > 0.7).sum():>20,} {(f_preds > 0.7).sum():>20,}")
    print(f"{'0.4-0.7 (MED)':.<20} {((s_preds >= 0.4) & (s_preds <= 0.7)).sum():>20,} {((f_preds >= 0.4) & (f_preds <= 0.7)).sum():>20,}")
    print(f"{'< 0.4 (LOW)':.<20} {(s_preds < 0.4).sum():>20,} {(f_preds < 0.4).sum():>20,}")
    print("=" * 70)


if __name__ == '__main__':
    main()
