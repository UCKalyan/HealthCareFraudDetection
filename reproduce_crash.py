
import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
import pandas as pd
import numpy as np
import keras
import joblib
import yaml
import logging
from dotenv import load_dotenv
from src.utils.config_loader import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model_loading():
    logger.info("Loading environment variables...")
    load_dotenv()
    
    logger.info("Loading config...")
    config = load_config('config.yaml')
    
    model_path = config['preprocessor']['model_path']
    scaler_path = config['preprocessor']['scaler_path']
    feature_store_path = config['preprocessor']['feature_store_path']
    
    logger.info(f"Model path: {model_path}")
    
    try:
        logger.info("Loading model...")
        model = keras.models.load_model(model_path)
        logger.info("Model loaded successfully.")
        
        logger.info("Loading scaler...")
        scaler = joblib.load(scaler_path)
        logger.info("Scaler loaded successfully.")
        
        logger.info("Loading feature store sample...")
        df = pd.read_csv(feature_store_path).head(10)
        logger.info(f"Loaded {len(df)} rows.")
        
        # Prepare data for prediction
        stats_path = config['preprocessor']['specialty_stats_path']
        import json
        with open(stats_path, 'r') as f:
            stats = json.load(f)
            final_feature_columns = stats['final_feature_columns']
            
        logger.info(f"Feature columns: {final_feature_columns}")
        
        # Select and scale
        # Ensure columns exist
        missing_cols = [c for c in final_feature_columns if c not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns in feature store: {missing_cols}")
            # Add dummy columns for testing
            for c in missing_cols:
                df[c] = 0.0
        
        X = df[final_feature_columns]
        X_scaled = scaler.transform(X)
        
        logger.info("Running prediction...")
        preds = model.predict(X_scaled)
        logger.info(f"Predictions: {preds.flatten()}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_loading()
