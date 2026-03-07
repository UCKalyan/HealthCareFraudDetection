#!/usr/bin/env python
"""
Create 2022 Feature Store and Extract Test Batch

Pipeline:
  1. Load 2022 raw CMS data (physician + prescriber + LEIE)
  2. Run full preprocessing to create provider_features_2022.csv
  3. Score all providers with the existing HOPE model
  4. Classify as HIGH / MEDIUM / LOW risk
  5. Extract a mixed batch of 100 providers for incremental training testing

Usage:
    python create_2022_features.py
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
    logger.info("CREATE 2022 FEATURE STORE & TEST BATCH")
    logger.info("=" * 80)

    from src.utils.config_loader import load_config
    config = load_config()

    # ══════════════════════════════════════════════════════════════════
    # STEP 1: Load 2022 raw data via existing pipeline
    # ══════════════════════════════════════════════════════════════════
    logger.info("STEP 1: Loading 2022 raw CMS data...")
    from src.data_processing.loader import load_and_prep_data
    from src.data_processing.preprocessor import create_advanced_features_and_split

    dataframes = load_and_prep_data(config['data'])
    phys_df = dataframes.get('physician')
    presc_df = dataframes.get('prescriber')
    leie_df = dataframes.get('leie')

    if phys_df is None or presc_df is None:
        logger.error("Failed to load physician or prescriber data!")
        sys.exit(1)

    logger.info(f"  Physician: {len(phys_df):,} rows")
    logger.info(f"  Prescriber: {len(presc_df):,} rows")
    logger.info(f"  LEIE: {len(leie_df):,} rows" if leie_df is not None else "  LEIE: Not loaded")

    # ══════════════════════════════════════════════════════════════════
    # STEP 2: Run full feature engineering pipeline
    # ══════════════════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 2: Running feature engineering pipeline...")
    (X_train, X_val, X_test,
     y_train, y_val, y_test,
     feature_columns,
     all_profiles_engineered,
     artifacts) = create_advanced_features_and_split(phys_df, presc_df, leie_df, config)

    logger.info(f"  Feature columns: {feature_columns}")
    logger.info(f"  Total providers: {len(all_profiles_engineered):,}")
    logger.info(f"  Train: {len(X_train):,}, Val: {len(X_val):,}, Test: {len(X_test):,}")

    # Save the 2022 feature store
    feature_store_path = 'data/processed/provider_features_2022.csv'
    all_profiles_engineered.to_csv(feature_store_path, index=False)
    logger.info(f"  ✅ Feature store saved: {feature_store_path}")

    # Save the new scaler and artifacts
    new_scaler = artifacts['scaler']
    joblib.dump(new_scaler, 'models/robust_scaler_2022.joblib')
    logger.info(f"  ✅ Scaler saved: models/robust_scaler_2022.joblib")

    # Save specialty stats for 2022
    stats_2022 = {
        'final_feature_columns': feature_columns,
        'source': '2022 CMS Data',
        'total_providers': len(all_profiles_engineered),
    }
    with open('models/specialty_stats_2022.json', 'w') as f:
        json.dump(stats_2022, f, indent=2)

    # ══════════════════════════════════════════════════════════════════
    # STEP 3: Score all providers using EXISTING model + NEW 2022 scaler
    # ══════════════════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 3: Scoring all providers with existing HOPE model...")

    # Load the backed-up model
    model = tf.keras.models.load_model('models/fraud_detection_model.keras')

    # Extract features from the 2022 feature store and scale with 2022 scaler
    X_all = all_profiles_engineered[feature_columns].values
    X_scaled = new_scaler.transform(X_all).astype('float32')

    # Score
    scores = model.predict(X_scaled, verbose=1, batch_size=4096).flatten()
    all_profiles_engineered = all_profiles_engineered.copy()
    all_profiles_engineered['risk_score'] = scores

    # Classify
    all_profiles_engineered['risk_level'] = np.where(
        scores > 0.7, 'HIGH',
        np.where(scores >= 0.4, 'MEDIUM', 'LOW')
    )

    # ══════════════════════════════════════════════════════════════════
    # STEP 4: Risk breakdown
    # ══════════════════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 4: Risk Level Breakdown")

    n_total = len(all_profiles_engineered)
    for level in ['HIGH', 'MEDIUM', 'LOW']:
        subset = all_profiles_engineered[all_profiles_engineered['risk_level'] == level]
        n = len(subset)
        avg_score = subset['risk_score'].mean() if n > 0 else 0
        emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[level]
        logger.info(f"  {emoji} {level:8s}: {n:>10,} ({n/n_total*100:>6.2f}%)  avg_score={avg_score:.4f}")
    logger.info(f"  {'TOTAL':>11s}: {n_total:>10,}")

    # Score distribution
    logger.info(f"  Score stats: mean={scores.mean():.4f}, median={np.median(scores):.4f}, std={scores.std():.4f}")

    # Top specialties
    high_df = all_profiles_engineered[all_profiles_engineered['risk_level'] == 'HIGH']
    if len(high_df) > 0:
        spec_counts = high_df.groupby('specialty').size().sort_values(ascending=False).head(10)
        logger.info("")
        logger.info("  Top 10 specialties by HIGH risk count:")
        for spec, count in spec_counts.items():
            logger.info(f"    {spec:<45s} {count:>8,}")

    # ══════════════════════════════════════════════════════════════════
    # STEP 5: Extract mixed batch of 100 providers
    # ══════════════════════════════════════════════════════════════════
    logger.info("")
    logger.info("STEP 5: Extracting mixed batch of 100 providers for incremental training...")

    np.random.seed(42)

    high_providers = all_profiles_engineered[all_profiles_engineered['risk_level'] == 'HIGH']
    med_providers = all_profiles_engineered[all_profiles_engineered['risk_level'] == 'MEDIUM']
    low_providers = all_profiles_engineered[all_profiles_engineered['risk_level'] == 'LOW']

    n_high = min(33, len(high_providers))
    n_med = min(34, len(med_providers))
    n_low = min(33, len(low_providers))

    # If medium is scarce, redistribute
    if n_med < 34:
        extra = 34 - n_med
        n_high = min(n_high + extra // 2, len(high_providers))
        n_low = min(n_low + extra - extra // 2, len(low_providers))
        logger.info(f"  Medium providers scarce ({len(med_providers)}). Adjusted: HIGH={n_high}, MED={n_med}, LOW={n_low}")

    batch_parts = []
    if n_high > 0:
        batch_parts.append(high_providers.sample(n=n_high, random_state=42))
    if n_med > 0:
        batch_parts.append(med_providers.sample(n=n_med, random_state=42))
    if n_low > 0:
        batch_parts.append(low_providers.sample(n=n_low, random_state=42))

    batch = pd.concat(batch_parts).sample(frac=1, random_state=42)  # Shuffle

    # Save batch
    os.makedirs('data/test_samples', exist_ok=True)
    batch_path = 'data/test_samples/incremental_test_batch_2022.csv'
    batch.to_csv(batch_path, index=False)

    logger.info(f"  ✅ Batch saved: {batch_path}")
    logger.info(f"  Batch composition:")
    for level in ['HIGH', 'MEDIUM', 'LOW']:
        n = len(batch[batch['risk_level'] == level])
        logger.info(f"    {level}: {n}")

    # Print sample providers from each category
    print("\n" + "=" * 90)
    print(f"{'SAMPLE PROVIDERS FROM TEST BATCH':^90}")
    print("=" * 90)

    for level, emoji in [('HIGH', '🔴'), ('MEDIUM', '🟡'), ('LOW', '🟢')]:
        subset = batch[batch['risk_level'] == level]
        if len(subset) == 0:
            continue
        print(f"\n{emoji} {level} RISK (showing up to 5):")
        print(f"{'NPI':<15} {'Specialty':<35} {'Score':>10} {'Cost/Svc':>12}")
        print("-" * 75)
        for _, row in subset.head(5).iterrows():
            npi = int(row.get('provider_id', 0))
            spec = str(row.get('specialty', 'Unknown'))[:33]
            score = row['risk_score']
            cps = row.get('cost_per_service', 0)
            print(f"{npi:<15} {spec:<35} {score:>10.4f} {cps:>12.2f}")

    print("\n" + "=" * 90)
    print(f"✅ DONE. Mixed batch of {len(batch)} providers saved to: {batch_path}")
    print(f"   This batch can be used for incremental training testing.")
    print("=" * 90)


if __name__ == '__main__':
    main()
