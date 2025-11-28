import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.utils.config_loader import load_config

def analyze_thresholds():
    print("Loading assets...")
    config = load_config('config.yaml')
    
    # Load Model and Scaler
    model = tf.keras.models.load_model(config['preprocessor']['model_path'])
    scaler = joblib.load(config['preprocessor']['scaler_path'])
    
    # Load Data
    feature_store = pd.read_csv(config['preprocessor']['feature_store_path']).set_index('provider_id')
    
    # Load Feature Columns
    with open(config['preprocessor']['specialty_stats_path'], 'r') as f:
        stats = json.load(f)
        final_feature_columns = stats['final_feature_columns']
    
    print(f"Calculating risk scores for {len(feature_store)} providers...")
    
    # Prepare data
    full_aligned = feature_store.reindex(columns=final_feature_columns, fill_value=0)
    full_vectors = scaler.transform(full_aligned)
    
    # Predict
    risk_scores = model.predict(full_vectors, verbose=0).flatten()
    
    # Statistics
    print("\n--- Risk Score Statistics ---")
    print(f"Mean: {np.mean(risk_scores):.4f}")
    print(f"Median: {np.median(risk_scores):.4f}")
    print(f"Std Dev: {np.std(risk_scores):.4f}")
    print(f"Min: {np.min(risk_scores):.4f}")
    print(f"Max: {np.max(risk_scores):.4f}")
    
    print("\n--- Percentiles ---")
    percentiles = [50, 75, 90, 95, 99, 99.9]
    results = np.percentile(risk_scores, percentiles)
    for p, val in zip(percentiles, results):
        print(f"{p}th percentile: {val:.4f}")
        
    print("\n--- Proposed Thresholds ---")
    print(f"Medium Risk (> 75th): {results[1]:.4f}")
    print(f"High Risk (> 95th): {results[3]:.4f}")

if __name__ == "__main__":
    analyze_thresholds()
