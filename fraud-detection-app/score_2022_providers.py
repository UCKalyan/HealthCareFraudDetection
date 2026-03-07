#!/usr/bin/env python
"""
Score 2022 CMS Providers — Identify HIGH, MEDIUM, LOW risk providers.

Loads the 2022 physician + prescriber data, engineers features using the
existing pipeline, scores all providers with the current HOPE model,
and outputs a breakdown by risk level with sample providers from each.

Usage:
    python score_2022_providers.py
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


def main():
    logger.info("=" * 80)
    logger.info("SCORING 2022 CMS PROVIDERS — Risk Level Classification")
    logger.info("=" * 80)

    # Load config
    from src.utils.config_loader import load_config
    config = load_config()

    # Load feature columns and scaler
    with open('models/specialty_stats.json') as f:
        stats = json.load(f)
    feature_columns = stats['final_feature_columns']
    scaler = joblib.load('models/robust_scaler.joblib')
    logger.info(f"Feature columns: {feature_columns}")

    # Load the HOPE Stable model (production inference model)
    logger.info("Loading HOPE Stable model...")
    model = tf.keras.models.load_model('models/fraud_detection_model.keras')

    # ── Load 2022 raw data and engineer features ─────────────────────
    logger.info("Loading 2022 raw CMS data...")
    from src.data_processing.loader import load_and_prep_data
    from src.data_processing.preprocessor import create_advanced_features_and_split

    dataframes = load_and_prep_data(config['data'])
    phys_df = dataframes.get('physician')
    presc_df = dataframes.get('prescriber')
    leie_df = dataframes.get('leie')

    logger.info("Engineering features...")
    (X_train, X_val, X_test,
     y_train, y_val, y_test,
     feature_names, provider_ids_train, _) = create_advanced_features_and_split(
        phys_df, presc_df, leie_df, config
    )

    # Combine all splits back together for full scoring
    X_all = np.vstack([X_train, X_val, X_test])
    y_all = np.concatenate([y_train, y_val, y_test])
    logger.info(f"Total providers to score: {len(X_all):,}")

    # Scale and predict
    X_scaled = scaler.transform(X_all).astype('float32')
    scores = model.predict(X_scaled, verbose=1, batch_size=4096).flatten()

    # ── Classify risk levels ─────────────────────────────────────────
    high_mask = scores > 0.7
    med_mask = (scores >= 0.4) & (scores <= 0.7)
    low_mask = scores < 0.4

    n_high = high_mask.sum()
    n_med = med_mask.sum()
    n_low = low_mask.sum()
    n_total = len(scores)

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"{'RISK LEVEL BREAKDOWN':^80}")
    logger.info("=" * 80)

    print(f"\n{'Category':<25} {'Count':>12} {'Percentage':>15} {'Avg Score':>12}")
    print("-" * 70)
    print(f"{'🔴 HIGH RISK (>0.7)':<25} {n_high:>12,} {n_high/n_total*100:>14.2f}% {scores[high_mask].mean():>12.4f}" if n_high > 0 else f"{'🔴 HIGH RISK (>0.7)':<25} {0:>12,} {'0.00':>14}% {'N/A':>12}")
    print(f"{'🟡 MEDIUM (0.4-0.7)':<25} {n_med:>12,} {n_med/n_total*100:>14.2f}% {scores[med_mask].mean():>12.4f}" if n_med > 0 else f"{'🟡 MEDIUM (0.4-0.7)':<25} {0:>12,} {'0.00':>14}% {'N/A':>12}")
    print(f"{'🟢 LOW RISK (<0.4)':<25} {n_low:>12,} {n_low/n_total*100:>14.2f}% {scores[low_mask].mean():>12.4f}" if n_low > 0 else f"{'🟢 LOW RISK (<0.4)':<25} {0:>12,} {'0.00':>14}% {'N/A':>12}")
    print("-" * 70)
    print(f"{'TOTAL':<25} {n_total:>12,}")

    # ── Score distribution stats ─────────────────────────────────────
    print(f"\n{'Score Distribution':^70}")
    print("-" * 70)
    print(f"  Mean:   {np.mean(scores):.4f}")
    print(f"  Median: {np.median(scores):.4f}")
    print(f"  Std:    {np.std(scores):.4f}")
    print(f"  Min:    {np.min(scores):.4f}")
    print(f"  Max:    {np.max(scores):.4f}")

    # ── Try to get provider details from the feature store ───────────
    # Load the preprocessor's intermediate data to get provider IDs + specialties
    try:
        feat_df = pd.read_csv('data/processed/provider_features.csv')
        # match by index if same length, otherwise skip
        if len(feat_df) >= len(scores):
            feat_df = feat_df.iloc[:len(scores)].copy()
            feat_df['risk_score'] = scores
            feat_df['risk_level'] = np.where(scores > 0.7, 'HIGH',
                                   np.where(scores >= 0.4, 'MEDIUM', 'LOW'))
            has_details = True
        else:
            has_details = False
    except Exception:
        has_details = False

    if has_details:
        # ── Sample HIGH risk providers ───────────────────────────────
        high_df = feat_df[feat_df['risk_level'] == 'HIGH'].sort_values('risk_score', ascending=False)
        print(f"\n{'TOP 15 HIGH RISK PROVIDERS':^80}")
        print("-" * 80)
        print(f"{'NPI':<15} {'Specialty':<35} {'Score':>10} {'Cost/Svc':>12}")
        print("-" * 80)
        for _, row in high_df.head(15).iterrows():
            npi = int(row.get('provider_id', 0))
            spec = str(row.get('specialty', 'Unknown'))[:33]
            score = row['risk_score']
            cps = row.get('cost_per_service', 0)
            print(f"{npi:<15} {spec:<35} {score:>10.4f} {cps:>12.2f}")

        # ── Sample MEDIUM risk providers ─────────────────────────────
        med_df = feat_df[feat_df['risk_level'] == 'MEDIUM'].sort_values('risk_score', ascending=False)
        print(f"\n{'TOP 15 MEDIUM RISK PROVIDERS':^80}")
        print("-" * 80)
        print(f"{'NPI':<15} {'Specialty':<35} {'Score':>10} {'Cost/Svc':>12}")
        print("-" * 80)
        for _, row in med_df.head(15).iterrows():
            npi = int(row.get('provider_id', 0))
            spec = str(row.get('specialty', 'Unknown'))[:33]
            score = row['risk_score']
            cps = row.get('cost_per_service', 0)
            print(f"{npi:<15} {spec:<35} {score:>10.4f} {cps:>12.2f}")

        # ── Sample LOW risk providers ────────────────────────────────
        low_df = feat_df[feat_df['risk_level'] == 'LOW'].sample(n=min(15, len(feat_df[feat_df['risk_level']=='LOW'])), random_state=42)
        print(f"\n{'SAMPLE 15 LOW RISK PROVIDERS':^80}")
        print("-" * 80)
        print(f"{'NPI':<15} {'Specialty':<35} {'Score':>10} {'Cost/Svc':>12}")
        print("-" * 80)
        for _, row in low_df.iterrows():
            npi = int(row.get('provider_id', 0))
            spec = str(row.get('specialty', 'Unknown'))[:33]
            score = row['risk_score']
            cps = row.get('cost_per_service', 0)
            print(f"{npi:<15} {spec:<35} {score:>10.4f} {cps:>12.2f}")

        # ── Specialty breakdown ──────────────────────────────────────
        print(f"\n{'TOP 10 SPECIALTIES BY HIGH-RISK PROVIDER COUNT':^80}")
        print("-" * 80)
        spec_counts = high_df.groupby('specialty').size().sort_values(ascending=False).head(10)
        print(f"{'Specialty':<45} {'High-Risk Count':>15} {'% of High':>15}")
        print("-" * 80)
        for spec, count in spec_counts.items():
            pct = count / n_high * 100
            print(f"{str(spec)[:43]:<45} {count:>15,} {pct:>14.2f}%")

    print("\n" + "=" * 80)
    print(f"✅ Scoring complete. {n_total:,} providers classified.")
    print("=" * 80)


if __name__ == '__main__':
    main()
