import os
import sqlite3
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import argparse
from src.utils.config_loader import load_config

def load_feedback_data(db_path):
    """Loads and processes feedback data from SQLite."""
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return None

    conn = sqlite3.connect(db_path)
    query = "SELECT npi, action FROM feedback"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Map actions to labels
    # confirm/suspicious -> 1 (Fraud)
    # false_positive/dismiss -> 0 (Normal)
    action_map = {
        'confirm': 1,
        'suspicious': 1,
        'false_positive': 0,
        'dismiss': 0
    }
    
    df['label'] = df['action'].map(action_map)
    
    # Drop rows with unknown actions (if any)
    df = df.dropna(subset=['label'])
    
    # Deduplicate: take the most recent or majority vote? 
    # For now, let's just drop duplicates, keeping the last entry if timestamps were available (but we just did a simple select).
    # In a real system, we'd query by timestamp.
    df = df.drop_duplicates(subset=['npi'], keep='last')
    
    return df

def retrain_model(config_path='config.yaml', threshold=10):
    print("--- Starting Feedback Retraining Workflow ---")
    
    # 1. Load Config
    config = load_config(config_path)
    
    # 2. Load Feedback
    db_path = "../shared-data/databases/feedback.db"
    feedback_df = load_feedback_data(db_path)
    
    if feedback_df is None or len(feedback_df) == 0:
        print("No feedback data found.")
        return

    print(f"Loaded {len(feedback_df)} feedback records.")
    
    if len(feedback_df) < threshold:
        print(f"Feedback count ({len(feedback_df)}) is below threshold ({threshold}). Skipping retraining.")
        return

    # 3. Load Feature Store
    feature_store_path = config['preprocessor']['feature_store_path']
    if not os.path.exists(feature_store_path):
        print(f"Feature store not found at {feature_store_path}. Run build_artifacts.py first.")
        return
        
    feature_store = pd.read_csv(feature_store_path)
    
    # Ensure NPI is correct type for merging
    feature_store['provider_id'] = feature_store['provider_id'].astype(str)
    feedback_df['npi'] = feedback_df['npi'].astype(str)
    
    # 4. Merge Feedback with Features
    # We only want rows that exist in both
    training_data = pd.merge(feedback_df, feature_store, left_on='npi', right_on='provider_id', how='inner')
    
    if len(training_data) == 0:
        print("No matching providers found in feature store for the feedback NPIs.")
        return

    print(f"Matched {len(training_data)} providers with features.")

    # 5. Prepare X and y
    # Load feature names from stats file to ensure correct order
    import json
    with open(config['preprocessor']['specialty_stats_path'], 'r') as f:
        stats = json.load(f)
        feature_cols = stats['final_feature_columns']
        
    X = training_data[feature_cols]
    y = training_data['label'].values
    
    # 6. Scale Features
    scaler_path = config['preprocessor']['scaler_path']
    scaler = joblib.load(scaler_path)
    X_scaled = scaler.transform(X)
    
    # 7. Load Model
    model_path = config['training']['model_path']
    print(f"Loading model from {model_path}...")
    model = tf.keras.models.load_model(model_path)
    
    # 8. Fine-tune
    print("Fine-tuning model on feedback data...")
    
    # Use a lower learning rate for fine-tuning to avoid destroying previous knowledge
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss='binary_crossentropy',
        metrics=['AUC']
    )
    
    history = model.fit(
        X_scaled, y,
        epochs=5, # Few epochs for fine-tuning
        batch_size=4, # Small batch size for small data
        verbose=1
    )
    
    # 9. Save Model
    print(f"Saving updated model to {model_path}...")
    model.save(model_path)
    print("--- Retraining Complete ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrain fraud detection model using human feedback.")
    parser.add_argument("--threshold", type=int, default=5, help="Minimum number of feedback records required to trigger retraining.")
    args = parser.parse_args()
    
    retrain_model(threshold=args.threshold)
