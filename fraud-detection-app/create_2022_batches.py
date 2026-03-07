#!/usr/bin/env python
"""
Generate 25 non-overlapping batches of 100 mixed-risk providers from 2022 data.

Uses the already-created provider_features_2022.csv feature store and the
existing model to score and split providers into 25 batches with a mix of
HIGH, MEDIUM, and LOW risk providers in each.

Usage:
    python create_2022_batches.py
"""
import sys, os, logging
sys.path.insert(0, os.path.abspath('.'))

import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
import json

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NUM_BATCHES = 25
BATCH_SIZE = 100


def main():
    logger.info("=" * 80)
    logger.info(f"GENERATING {NUM_BATCHES} MIXED TEST BATCHES FROM 2022 DATA")
    logger.info("=" * 80)

    # Load the 2022 feature store (already preprocessed)
    logger.info("Loading 2022 feature store...")
    df = pd.read_csv('data/processed/provider_features_2022.csv')
    logger.info(f"  Loaded {len(df):,} providers")

    # Load feature columns
    with open('models/specialty_stats_2022.json') as f:
        stats = json.load(f)
    feature_columns = stats['final_feature_columns']

    # Load model and 2022 scaler
    logger.info("Loading model and 2022 scaler...")
    model = tf.keras.models.load_model('models/fraud_detection_model.keras')
    scaler = joblib.load('models/robust_scaler_2022.joblib')

    # Score all providers
    logger.info("Scoring all providers...")
    X = df[feature_columns].values
    X_scaled = scaler.transform(X).astype('float32')
    scores = model.predict(X_scaled, verbose=0, batch_size=4096).flatten()

    df['risk_score'] = scores
    df['risk_level'] = np.where(scores > 0.7, 'HIGH',
                      np.where(scores >= 0.4, 'MEDIUM', 'LOW'))

    # Split by risk level
    high_df = df[df['risk_level'] == 'HIGH'].copy()
    med_df = df[df['risk_level'] == 'MEDIUM'].copy()
    low_df = df[df['risk_level'] == 'LOW'].copy()

    logger.info(f"  HIGH: {len(high_df):,}, MEDIUM: {len(med_df):,}, LOW: {len(low_df):,}")

    # Shuffle each pool
    high_df = high_df.sample(frac=1, random_state=42).reset_index(drop=True)
    med_df = med_df.sample(frac=1, random_state=42).reset_index(drop=True)
    low_df = low_df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Calculate how many of each risk level per batch
    # Target: 5 HIGH, 5 MEDIUM, 90 LOW per batch (realistic fraud ratio)
    high_per_batch = 5
    med_per_batch = min(5, len(med_df) // NUM_BATCHES)
    low_per_batch = BATCH_SIZE - high_per_batch - med_per_batch

    logger.info(f"  Per batch target: HIGH={high_per_batch}, MEDIUM={med_per_batch}, LOW={low_per_batch}")
    logger.info(f"  MEDIUM available per batch: {len(med_df) // NUM_BATCHES} (total: {len(med_df)})")

    # Create output directory
    output_dir = '../shared-data/test_samples'
    os.makedirs(output_dir, exist_ok=True)

    # Remove old batch files
    for old_file in os.listdir(output_dir):
        if old_file.startswith('batch_') and old_file.endswith('.csv'):
            os.remove(os.path.join(output_dir, old_file))

    # Generate 25 non-overlapping batches
    logger.info("")
    logger.info(f"Generating {NUM_BATCHES} batches...")
    print(f"\n{'Batch':<10} {'HIGH':>8} {'MED':>8} {'LOW':>8} {'Total':>8} {'Avg Score':>12}")
    print("-" * 60)

    high_idx = 0
    med_idx = 0
    low_idx = 0

    for batch_num in range(NUM_BATCHES):
        parts = []

        # HIGH risk slice
        h_end = min(high_idx + high_per_batch, len(high_df))
        if high_idx < h_end:
            parts.append(high_df.iloc[high_idx:h_end])
        n_high = h_end - high_idx
        high_idx = h_end

        # MEDIUM risk slice
        m_end = min(med_idx + med_per_batch, len(med_df))
        if med_idx < m_end:
            parts.append(med_df.iloc[med_idx:m_end])
        n_med = m_end - med_idx
        med_idx = m_end

        # LOW risk slice (fill remaining to reach BATCH_SIZE)
        n_remaining = BATCH_SIZE - n_high - n_med
        l_end = min(low_idx + n_remaining, len(low_df))
        if low_idx < l_end:
            parts.append(low_df.iloc[low_idx:l_end])
        n_low = l_end - low_idx
        low_idx = l_end

        # Combine and shuffle
        batch = pd.concat(parts).sample(frac=1, random_state=batch_num)
        total = len(batch)
        avg = batch['risk_score'].mean()

        # Save
        batch_path = os.path.join(output_dir, f'batch_{batch_num}.csv')
        batch.to_csv(batch_path, index=False)

        print(f"batch_{batch_num:<4d} {n_high:>8d} {n_med:>8d} {n_low:>8d} {total:>8d} {avg:>12.4f}")

    # Summary
    print("\n" + "=" * 80)
    total_providers_used = high_idx + med_idx + low_idx
    print(f"✅ Created {NUM_BATCHES} batches in {output_dir}/")
    print(f"   Total providers used: {total_providers_used:,}")
    print(f"   Each batch: ~{BATCH_SIZE} providers with mix of HIGH/MEDIUM/LOW")
    print(f"   All batches are NON-OVERLAPPING (different providers in each)")
    print("=" * 80)

    # Also save a summary CSV
    summary_path = os.path.join(output_dir, 'batch_summary.csv')
    summary_data = []
    for batch_num in range(NUM_BATCHES):
        bp = os.path.join(output_dir, f'batch_{batch_num}.csv')
        b = pd.read_csv(bp)
        summary_data.append({
            'batch': f'batch_{batch_num}',
            'total': len(b),
            'high': len(b[b['risk_level'] == 'HIGH']),
            'medium': len(b[b['risk_level'] == 'MEDIUM']),
            'low': len(b[b['risk_level'] == 'LOW']),
            'avg_score': b['risk_score'].mean(),
        })
    pd.DataFrame(summary_data).to_csv(summary_path, index=False)
    logger.info(f"  Batch summary saved: {summary_path}")


if __name__ == '__main__':
    main()
