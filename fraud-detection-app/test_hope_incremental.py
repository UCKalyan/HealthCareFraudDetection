#!/usr/bin/env python
"""
HOPE Incremental Training Demo — Full Pipeline

Shows the complete HOPE lifecycle:
  1. Load BEFORE metrics (both models identical from recovery)
  2. Run incremental training on new labeled data (Fast model gets gradients)
  3. Propagate Fast → Slow via EMA (α=0.99)
  4. Load AFTER metrics and compare divergence

Usage:
    python test_hope_incremental.py
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


def evaluate_model(model, X, y, name):
    """Evaluate a model and return metrics dict."""
    pred_proba = model.predict(X, verbose=0).flatten()
    pred = (pred_proba > 0.5).astype(int)
    n_classes = len(np.unique(y))
    return {
        'name': name,
        'accuracy':  accuracy_score(y, pred),
        'precision': precision_score(y, pred, zero_division=0) if n_classes >= 2 else 0,
        'recall':    recall_score(y, pred, zero_division=0) if n_classes >= 2 else 0,
        'f1':        f1_score(y, pred, zero_division=0) if n_classes >= 2 else 0,
        'auc':       roc_auc_score(y, pred_proba) if n_classes >= 2 else 0,
        'high':      int((pred_proba > 0.7).sum()),
        'med':       int(((pred_proba >= 0.4) & (pred_proba <= 0.7)).sum()),
        'low':       int((pred_proba < 0.4).sum()),
        'mean':      float(np.mean(pred_proba)),
        'preds':     pred_proba,
    }


def print_comparison(before_stable, before_fast, after_stable, after_fast):
    """Print a full before/after comparison table."""
    print("\n" + "=" * 90)
    print(f"{'HOPE INCREMENTAL TRAINING — BEFORE vs AFTER COMPARISON':^90}")
    print("=" * 90)

    metrics = ['accuracy', 'precision', 'recall', 'f1', 'auc']

    # BEFORE
    print(f"\n{'BEFORE Incremental Training (both identical)':^90}")
    print("-" * 90)
    print(f"{'Metric':<15} {'Stable':>15} {'Fast':>15} {'Difference':>15}")
    print("-" * 90)
    for m in metrics:
        diff = before_fast[m] - before_stable[m]
        print(f"{m.upper():<15} {before_stable[m]:>15.4f} {before_fast[m]:>15.4f} {diff:>15.6f}")

    # AFTER
    print(f"\n{'AFTER Incremental Training (models diverged)':^90}")
    print("-" * 90)
    print(f"{'Metric':<15} {'Stable':>15} {'Fast':>15} {'Difference':>15} {'Direction':>15}")
    print("-" * 90)
    for m in metrics:
        diff = after_fast[m] - after_stable[m]
        arrow = "Fast ↑" if diff > 0.0001 else ("Stable ↑" if diff < -0.0001 else "≈ Same")
        print(f"{m.upper():<15} {after_stable[m]:>15.4f} {after_fast[m]:>15.4f} {diff:>+15.6f} {arrow:>15}")

    # Score distribution
    print(f"\n{'Score Distribution — AFTER':^90}")
    print("-" * 90)
    print(f"{'Category':<20} {'Stable':>15} {'Fast':>15} {'Change':>15}")
    print("-" * 90)
    print(f"{'HIGH (>0.7)':<20} {after_stable['high']:>15,} {after_fast['high']:>15,} {after_fast['high']-after_stable['high']:>+15,}")
    print(f"{'MED (0.4-0.7)':<20} {after_stable['med']:>15,} {after_fast['med']:>15,} {after_fast['med']-after_stable['med']:>+15,}")
    print(f"{'LOW (<0.4)':<20} {after_stable['low']:>15,} {after_fast['low']:>15,} {after_fast['low']-after_stable['low']:>+15,}")
    print(f"{'Mean Score':<20} {after_stable['mean']:>15.4f} {after_fast['mean']:>15.4f} {after_fast['mean']-after_stable['mean']:>+15.4f}")

    # Sample divergence
    print(f"\n{'Sample Provider Score Divergence (first 10)':^90}")
    print("-" * 90)
    print(f"{'#':<5} {'Stable':>12} {'Fast':>12} {'Gap':>12} {'Alert':>20}")
    print("-" * 90)
    for i in range(min(10, len(after_stable['preds']))):
        s = after_stable['preds'][i]
        f = after_fast['preds'][i]
        gap = abs(f - s)
        alert = "⚠️ EARLY WARNING" if gap > 0.2 else ""
        print(f"{i+1:<5} {s:>12.4f} {f:>12.4f} {gap:>12.4f} {alert:>20}")

    print("=" * 90)


def main():
    logger.info("=" * 90)
    logger.info("HOPE INCREMENTAL TRAINING DEMO")
    logger.info("=" * 90)

    # ── Load config and feature columns ──
    from src.utils.config_loader import load_config
    config = load_config()

    with open('models/specialty_stats.json') as f:
        stats = json.load(f)
    feature_columns = stats['final_feature_columns']

    # ── Prepare validation set (same split as recovery) ──
    logger.info("Loading feature store for validation...")
    df = pd.read_csv('data/processed/provider_features.csv')

    X_all = df[feature_columns].values
    z_cols = [c for c in df.columns if 'z_tanh' in c]
    combined = df[z_cols].abs().mean(axis=1)
    threshold = combined.quantile(0.95)
    y_all = (combined > threshold).astype(int).values

    scaler = joblib.load('models/robust_scaler.joblib')
    X_scaled = scaler.transform(X_all).astype('float32')

    _, X_val, _, y_val = train_test_split(
        X_scaled, y_all, test_size=0.2, random_state=42, stratify=y_all
    )
    logger.info(f"Validation set: {len(X_val)} providers")

    # ══════════════════════════════════════════════════════
    # STEP 1: BEFORE — Load models and capture metrics
    # ══════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 1: Capturing BEFORE metrics (models should be identical)...")
    stable = tf.keras.models.load_model('models/fraud_detection_model.keras')
    fast = tf.keras.models.load_model('models/fraud_detection_model_fast.keras')

    before_stable = evaluate_model(stable, X_val, y_val, "Stable BEFORE")
    before_fast = evaluate_model(fast, X_val, y_val, "Fast BEFORE")

    max_diff = max(np.max(np.abs(s - f)) for s, f in zip(stable.get_weights(), fast.get_weights()))
    logger.info(f"  Max weight difference BEFORE: {max_diff:.10f}")
    logger.info(f"  Stable: Acc={before_stable['accuracy']:.4f} F1={before_stable['f1']:.4f}")
    logger.info(f"  Fast:   Acc={before_fast['accuracy']:.4f} F1={before_fast['f1']:.4f}")

    # ══════════════════════════════════════════════════════
    # STEP 2: Simulate new labeled data (like feedback from Monitor Agent)
    # ══════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 2: Preparing new labeled data for incremental training...")

    # Take a subset of providers and assign realistic labels
    # Simulate: Monitor Agent confirmed 200 high-risk providers as fraud
    # and 800 providers verified as clean
    np.random.seed(42)
    high_risk_idx = np.where(y_all == 1)[0][:200]   # 200 confirmed fraud
    clean_idx = np.where(y_all == 0)[0][:800]        # 800 confirmed clean
    new_idx = np.concatenate([high_risk_idx, clean_idx])
    np.random.shuffle(new_idx)

    X_new = X_scaled[new_idx]
    y_new = y_all[new_idx].astype('float32')
    logger.info(f"  New data: {len(X_new)} providers ({int(y_new.sum())} fraud, {int(len(y_new)-y_new.sum())} clean)")

    # Split new data into train/val
    X_inc_train, X_inc_val, y_inc_train, y_inc_val = train_test_split(
        X_new, y_new, test_size=0.1, random_state=42
    )

    # ══════════════════════════════════════════════════════
    # STEP 3: INCREMENTAL TRAINING via HOPE (NestedLearningModel)
    # ══════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 3: Running HOPE incremental training...")
    logger.info("  → Fast model gets gradient updates")
    logger.info("  → Slow model updated via EMA (α=0.99)")

    from src.models.nested_learning_model import NestedLearningModel
    from tensorflow.keras.optimizers import Adam
    from imblearn.over_sampling import SMOTE

    # Balance classes
    smote = SMOTE(random_state=42)
    X_inc_train_bal, y_inc_train_bal = smote.fit_resample(X_inc_train, y_inc_train)
    logger.info(f"  After SMOTE: {len(X_inc_train_bal)} ({int(y_inc_train_bal.sum())} fraud)")

    X_inc_train_bal = X_inc_train_bal.astype('float32')
    y_inc_train_bal = y_inc_train_bal.astype('float32')

    # Wrap in HOPE
    alpha = config['training']['nested_learning'].get('alpha', 0.99)
    nested = NestedLearningModel(
        fast_model=fast,
        slow_model=stable,
        alpha=alpha,
        log_frequency=50,
    )

    optimizer = Adam(learning_rate=1e-4)  # Lower LR for incremental
    nested.compile(
        optimizer=optimizer,
        loss_fn=tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0, from_logits=False),
        metrics=[tf.keras.metrics.AUC(name='AUC')],
    )

    # Train for 5 epochs (incremental)
    epochs = 5
    logger.info(f"  Training for {epochs} epochs (batch_size=256)...")
    history = nested.fit(
        X_inc_train_bal, y_inc_train_bal,
        epochs=epochs,
        batch_size=256,
        validation_data=(X_inc_val, y_inc_val),
        verbose=1,
    )

    # ══════════════════════════════════════════════════════
    # STEP 4: Save updated models
    # ══════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 4: Saving updated models...")
    model_path = config['preprocessor']['model_path']
    nested.slow_model.save(model_path)
    nested.fast_model.save(model_path.replace('.keras', '_fast.keras'))
    logger.info(f"  Stable: {model_path}")
    logger.info(f"  Fast:   {model_path.replace('.keras', '_fast.keras')}")

    # ══════════════════════════════════════════════════════
    # STEP 5: AFTER — Evaluate both models and compare
    # ══════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 5: Capturing AFTER metrics...")

    after_stable = evaluate_model(nested.slow_model, X_val, y_val, "Stable AFTER")
    after_fast = evaluate_model(nested.fast_model, X_val, y_val, "Fast AFTER")

    max_diff_after = max(np.max(np.abs(s - f)) for s, f in zip(
        nested.slow_model.get_weights(), nested.fast_model.get_weights()
    ))
    logger.info(f"  Max weight difference AFTER: {max_diff_after:.10f}")
    logger.info(f"  Stable: Acc={after_stable['accuracy']:.4f} F1={after_stable['f1']:.4f}")
    logger.info(f"  Fast:   Acc={after_fast['accuracy']:.4f} F1={after_fast['f1']:.4f}")

    # ══════════════════════════════════════════════════════
    # STEP 6: Print full comparison
    # ══════════════════════════════════════════════════════
    print_comparison(before_stable, before_fast, after_stable, after_fast)

    # Training history
    print(f"\n{'Training History':^90}")
    print("-" * 90)
    for epoch in range(epochs):
        auc_val = history.history.get('AUC', [0])[epoch]
        vloss = history.history.get('val_loss', [0])[epoch]
        print(f"  Epoch {epoch+1}: train_AUC={auc_val:.4f}, val_loss={vloss:.4f}")

    # Update metadata
    from datetime import datetime
    from src.training.incremental_retrain import load_training_metadata, save_training_metadata
    metadata = load_training_metadata(config)
    metadata['last_training_time'] = datetime.now()
    metadata['incremental_updates'] = metadata.get('incremental_updates', 0) + 1
    metadata['samples_trained'] = metadata.get('samples_trained', 0) + len(X_inc_train_bal)
    save_training_metadata(metadata, config)

    print(f"\n✅ Incremental training complete. Models have diverged as expected.")
    print(f"   The Fast model adapted to new data; the Slow model absorbed only {(1-alpha)*100:.0f}% per step.")
    print(f"   Max weight divergence: {max_diff_after:.6f}")


if __name__ == '__main__':
    main()
