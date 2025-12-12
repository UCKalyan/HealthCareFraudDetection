import os
import pandas as pd
import numpy as np
import json
import joblib
from sklearn.cluster import KMeans
import warnings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.utils.config_loader import load_config
from src.data_processing.loader import load_and_prep_data
from src.data_processing.preprocessor import create_advanced_features_and_split

def main():
    """
    This script runs the full data processing pipeline ONCE to generate all
    necessary artifacts for the real-time API server, including the final feature names.
    """
    print("--- Starting Training Artifact Generation ---")
    
    config = load_config('config.yaml')
    
    dataframes = load_and_prep_data(config['data'])
    phys_df = dataframes.get('physician')
    presc_df = dataframes.get('prescriber')
    leie_df = dataframes.get('leie')
    
    if phys_df is None or presc_df is None:
        print("Halting: Core datasets not found.")
        return

    (
        _, _, _, _, _, _, 
        final_feature_columns, # <-- We get the ground truth list here
        provider_profiles_with_features, 
        artifacts
    ) = create_advanced_features_and_split(phys_df, presc_df, leie_df, config)
    
    # 1. Save the Feature Store
    output_path = config['preprocessor']['feature_store_path']
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    provider_profiles_with_features.to_csv(output_path, index=False)
    print(f"\n1. Feature Store created successfully at: {output_path}")

    # 2. Save the Specialty Statistics AND the final feature names
    stats_path = config['preprocessor']['specialty_stats_path']
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)
    
    serializable_stats = {
        'cost_stats': artifacts['cost_stats'].to_dict(orient='records'),
        'spb_stats': artifacts['spb_stats'].to_dict(orient='records'),
        'median_pagerank': artifacts['median_pagerank'],
        'final_feature_columns': list(final_feature_columns) # <-- THE DEFINITIVE FIX
    }
    with open(stats_path, 'w') as f:
        json.dump(serializable_stats, f, indent=4)
    print(f"2. Specialty statistics & feature names saved successfully to: {stats_path}")

    # 3. Save the K-Means Model and the Scaler
    joblib.dump(artifacts['kmeans_model'], config['preprocessor']['kmeans_model_path'])
    joblib.dump(artifacts['scaler'], config['preprocessor']['scaler_path'])
    print(f"3. K-Means model and Scaler saved successfully.")

    print("\n--- All training artifacts generated successfully. The API server is ready to be launched. ---")

if __name__ == "__main__":
    main()

