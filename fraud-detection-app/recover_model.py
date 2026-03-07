#!/usr/bin/env python
"""
Model Recovery Script — Correct HOPE Initialization

Trains a SINGLE model on the full feature store, then clones it to
both Stable and Fast so they start IDENTICAL. Divergence only happens
during subsequent incremental retraining with new labeled data.

Usage:
    python recover_model.py
"""
import sys, os, logging
sys.path.insert(0, os.path.abspath('.'))

import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
import json

from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight
from imblearn.over_sampling import SMOTE
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 70)
    logger.info("MODEL RECOVERY — Correct HOPE Initialization")
    logger.info("Step 1: Train ONE model on all data")
    logger.info("Step 2: Clone it → Stable = Fast (identical)")
    logger.info("=" * 70)

    # Load config
    from src.utils.config_loader import load_config
    config = load_config()

    # Load feature columns
    with open('models/specialty_stats.json') as f:
        stats = json.load(f)
    feature_columns = stats['final_feature_columns']
    logger.info(f"Feature columns ({len(feature_columns)}): {feature_columns}")

    # Load feature store
    logger.info("Loading feature store...")
    df = pd.read_csv('data/processed/provider_features.csv')
    logger.info(f"Loaded {len(df)} providers")

    X = df[feature_columns].values

    # Generate labels using z-score method (top 5% as anomalous)
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

    # Scale features
    scaler = joblib.load('models/robust_scaler.joblib')
    X_scaled = scaler.transform(X)

    # Split
    X_train, X_val, y_train, y_val = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}")

    # SMOTE
    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)
    logger.info(f"After SMOTE: {len(X_train)} ({y_train.sum()} fraud)")

    # Class weights
    weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
    class_weights_dict = dict(enumerate(weights))

    # Convert to float32
    X_train = X_train.astype('float32')
    y_train = y_train.astype('float32')
    X_val = X_val.astype('float32')
    y_val = y_val.astype('float32')

    # ================================================================
    # STEP 1: Train a SINGLE standard model (no HOPE wrapper)
    # ================================================================
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 1: Training single base model (20 epochs)...")
    logger.info("=" * 70)

    from src.models.adaptive_deep_model import build_deep_learning_model
    model_config = {'learning_rate': 0.001, 'l2_regularization_factor': 0.001}
    base_model = build_deep_learning_model(input_shape=(X_train.shape[1],), config=model_config)

    # Add EarlyStopping to prevent overfitting
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=5, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.2, patience=3
        ),
    ]

    history = base_model.fit(
        X_train, y_train,
        epochs=20,
        batch_size=2048,
        validation_data=(X_val, y_val),
        class_weight=class_weights_dict,
        callbacks=callbacks,
        verbose=1,
    )

    # ================================================================
    # STEP 2: Clone to BOTH Stable and Fast (identical weights)
    # ================================================================
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 2: Cloning base model → Stable = Fast (identical)")
    logger.info("=" * 70)

    model_path = config['preprocessor']['model_path']
    fast_path = model_path.replace('.keras', '_fast.keras')

    # Save the SAME model as both Stable and Fast
    base_model.save(model_path)
    base_model.save(fast_path)
    logger.info(f"Stable model saved: {model_path}")
    logger.info(f"Fast model saved:   {fast_path}")

    # ================================================================
    # STEP 3: Evaluate — metrics should be IDENTICAL
    # ================================================================
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 3: Evaluating (both models should show identical metrics)")
    logger.info("=" * 70)

    # Load both back to prove they're identical
    stable_model = tf.keras.models.load_model(model_path)
    fast_model = tf.keras.models.load_model(fast_path)

    for name, model in [("Stable", stable_model), ("Fast", fast_model)]:
        y_pred_proba = model.predict(X_val, verbose=0).flatten()
        y_pred = (y_pred_proba > 0.5).astype(int)

        acc  = accuracy_score(y_val, y_pred)
        prec = precision_score(y_val, y_pred, zero_division=0)
        rec  = recall_score(y_val, y_pred, zero_division=0)
        f1   = f1_score(y_val, y_pred, zero_division=0)
        auc  = roc_auc_score(y_val, y_pred_proba)
        cm   = confusion_matrix(y_val, y_pred)

        logger.info(f"")
        logger.info(f"--- {name} Model ---")
        logger.info(f"  Accuracy:  {acc:.4f}")
        logger.info(f"  Precision: {prec:.4f}")
        logger.info(f"  Recall:    {rec:.4f}")
        logger.info(f"  F1 Score:  {f1:.4f}")
        logger.info(f"  AUC:       {auc:.4f}")
        logger.info(f"  Confusion: TN={cm[0][0]:,} FP={cm[0][1]:,} FN={cm[1][0]:,} TP={cm[1][1]:,}")

    # Score distribution
    s_preds = stable_model.predict(X_val, verbose=0).flatten()
    f_preds = fast_model.predict(X_val, verbose=0).flatten()

    logger.info("")
    logger.info("Score Distribution (both should be identical):")
    logger.info(f"  Stable — Mean={np.mean(s_preds):.4f}, HIGH={int((s_preds>0.7).sum()):,}, MED={int(((s_preds>=0.4)&(s_preds<=0.7)).sum()):,}, LOW={int((s_preds<0.4).sum()):,}")
    logger.info(f"  Fast   — Mean={np.mean(f_preds):.4f}, HIGH={int((f_preds>0.7).sum()):,}, MED={int(((f_preds>=0.4)&(f_preds<=0.7)).sum()):,}, LOW={int((f_preds<0.4).sum()):,}")

    # Verify weights are identical
    s_weights = stable_model.get_weights()
    f_weights = fast_model.get_weights()
    max_diff = max(np.max(np.abs(s - f)) for s, f in zip(s_weights, f_weights))
    logger.info(f"  Max weight difference: {max_diff:.10f} (should be 0.0)")

    # Sample predictions
    logger.info("")
    logger.info("Sample predictions (first 5):")
    for i in range(5):
        logger.info(f"  Provider #{i+1}: Stable={s_preds[i]:.4f}, Fast={f_preds[i]:.4f}, Actual={int(y_val[i])}")

    # Update training metadata
    from datetime import datetime
    from src.training.incremental_retrain import load_training_metadata, save_training_metadata
    metadata = load_training_metadata(config)
    metadata['last_training_time'] = datetime.now()
    metadata['last_full_retrain'] = datetime.now()
    metadata['samples_trained'] = len(X_train)
    save_training_metadata(metadata, config)

    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ RECOVERY COMPLETE — Both models are identical.")
    logger.info("   They will diverge ONLY during incremental retraining")
    logger.info("   when the Monitor Agent confirms new fraud cases.")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
