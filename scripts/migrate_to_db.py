
import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
import pandas as pd
import numpy as np
import sqlite3
import joblib
import keras
import logging
import json
from dotenv import load_dotenv
from src.utils.config_loader import load_config

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Starting migration to SQLite...")
    
    # Load Config & Env
    load_dotenv()
    config = load_config('config.yaml')
    
    # Paths
    feature_store_path = config['preprocessor']['feature_store_path']
    model_path = config['preprocessor']['model_path']
    scaler_path = config['preprocessor']['scaler_path']
    stats_path = config['preprocessor']['specialty_stats_path']
    db_path = "data/providers.db"
    
    # 1. Load Data
    logger.info(f"Loading CSV from {feature_store_path}...")
    df = pd.read_csv(feature_store_path)
    logger.info(f"Loaded {len(df)} records.")
    
    # 2. Load Model & Scaler for Risk Calculation
    logger.info("Loading Model and Scaler...")
    try:
        model = keras.models.load_model(model_path)
        scaler = joblib.load(scaler_path)
        
        with open(stats_path, 'r') as f:
            stats = json.load(f)
            final_feature_columns = stats['final_feature_columns']
            
        # 3. Calculate Risk Scores
        logger.info("Calculating Risk Scores...")
        # Ensure all columns exist
        for col in final_feature_columns:
            if col not in df.columns:
                df[col] = 0.0
                
        X = df[final_feature_columns]
        X_scaled = scaler.transform(X)
        scores = model.predict(X_scaled, verbose=1).flatten()
        
        df['risk_score'] = scores
        logger.info("Risk scores calculated.")
        
    except Exception as e:
        logger.error(f"Failed to calculate risk scores: {e}")
        logger.warning("Proceeding with default risk scores (0.0)")
        df['risk_score'] = 0.0

    # 4. Create Database
    logger.info(f"Creating database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop table if exists
    cursor.execute("DROP TABLE IF EXISTS providers")
    
    # Create Table
    # We'll infer schema from DataFrame, but explicit types are better.
    # For simplicity, we let pandas handle the schema creation, then add indices.
    
    logger.info("Inserting data...")
    df.to_sql('providers', conn, if_exists='replace', index=False)
    
    # 5. Create Indices
    logger.info("Creating indices...")
    cursor.execute("CREATE INDEX idx_provider_id ON providers (provider_id)")
    cursor.execute("CREATE INDEX idx_risk_score ON providers (risk_score)")
    cursor.execute("CREATE INDEX idx_specialty ON providers (specialty)")
    cursor.execute("CREATE INDEX idx_name ON providers (Prscrbr_Last_Org_Name)")
    
    conn.commit()
    conn.close()
    
    logger.info("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
