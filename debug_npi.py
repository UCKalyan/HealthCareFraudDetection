import pandas as pd
import tensorflow as tf
import joblib
import json
import numpy as np
from src.utils.config_loader import load_config

def debug_provider(npi):
    print(f"--- Debugging NPI: {npi} ---")
    config = load_config('config.yaml')
    
    # Load Assets
    print("Loading assets...")
    feature_store = pd.read_csv(config['preprocessor']['feature_store_path']).set_index('provider_id')
    model = tf.keras.models.load_model(config['training']['model_path'])
    scaler = joblib.load(config['preprocessor']['scaler_path'])
    
    with open(config['preprocessor']['specialty_stats_path'], 'r') as f:
        stats = json.load(f)
        feature_cols = stats['final_feature_columns']
        
    print(f"Feature Columns: {feature_cols}")
    
    try:
        provider = feature_store.loc[npi]
        print("\nRaw Provider Data:")
        print(provider)
        
        # Prepare for prediction
        # Note: We must convert to DataFrame to keep column names for reindexing if needed
        provider_df = pd.DataFrame([provider])
        provider_aligned = provider_df.reindex(columns=feature_cols, fill_value=0)
        
        print("\nAligned Data (Before Scaling):")
        print(provider_aligned.iloc[0])
        
        # Scale
        feature_vector = scaler.transform(provider_aligned)
        print("\nScaled Feature Vector:")
        print(feature_vector[0])
        
        # Predict
        score = model.predict(feature_vector)[0][0]
        print(f"\nPrediction Score: {score}")
        
        # Check Pagerank contribution manually (heuristic)
        pr_idx = feature_cols.index('pagerank_centrality')
        print(f"\nPagerank Index: {pr_idx}")
        print(f"Pagerank Raw: {provider_aligned.iloc[0]['pagerank_centrality']}")
        print(f"Pagerank Scaled: {feature_vector[0][pr_idx]}")
        
    except KeyError:
        print(f"NPI {npi} not found in feature store.")

if __name__ == "__main__":
    debug_provider(1003000126)
