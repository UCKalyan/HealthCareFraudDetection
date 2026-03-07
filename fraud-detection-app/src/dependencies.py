import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import tensorflow as tf
# Force CPU-only to prevent Metal GPU race condition with concurrent predictions
try:
    tf.config.set_visible_devices([], 'GPU')
except Exception:
    pass
import logging
import json
import joblib
import pandas as pd
import warnings
import keras # Direct import to bypass TF lazy loader issues
import shap
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.utils.config_loader import load_config
from src.agents.investigator import InvestigatorAgent
from src.agents.analyst import AnalystAgent
from src.agents.reporter import ReporterAgent
from src.agents.supervisor import SupervisorAgent
from src.agents.monitor import MonitorAgent
from src.services.semantic_search import SemanticSearchEngine

# Configure Logging
logger = logging.getLogger(__name__)

# Global dictionary to store ML assets
ml_assets = {}

def get_ml_assets():
    """Dependency to yield ML assets."""
    if not ml_assets:
        raise RuntimeError("ML Assets not loaded")
    return ml_assets

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup (loading assets) and shutdown (cleaning up).
    """
    logger.info("--- Loading ML assets into memory... ---")
    config = load_config('config.yaml')
    ml_assets['config'] = config
    
    try:
        # Load Model
        # Use direct keras.models.load_model as tf.keras seems broken in this env
        ml_assets['fraud_model'] = keras.models.load_model(config['preprocessor']['model_path'])
        
        # Load Fast Model (for Dual-Score Visualization)
        fast_path = config['preprocessor']['model_path'].replace('.keras', '_fast.keras')
        if os.path.exists(fast_path):
            try:
                ml_assets['fraud_model_fast'] = keras.models.load_model(fast_path)
                logger.info(f"Loaded Fast Model from {fast_path}")
            except Exception as e:
                logger.warning(f"Failed to load Fast Model: {e}")
                ml_assets['fraud_model_fast'] = None
        else:
            ml_assets['fraud_model_fast'] = None
        
        # Load Feature Store (Required for Real-time Inference)
        fs_path = config['preprocessor']['feature_store_path']
        # Fix path if running from inside the app directory
        if fs_path.startswith('fraud-detection-app/'):
            fs_path = fs_path.replace('fraud-detection-app/', '')
            
        logger.info(f"--- Checking Feature Store Path: {fs_path} ---")
        if os.path.exists(fs_path):
            df = pd.read_csv(fs_path)
            ml_assets['feature_store'] = df.set_index('provider_id')
            logger.info(f"--- Loaded Feature Store: {ml_assets['feature_store'].shape} ---")
            logger.info(f"--- Feature Store Index Type: {ml_assets['feature_store'].index.dtype} ---")
            logger.info(f"--- Sample Index: {ml_assets['feature_store'].index[:5].tolist()} ---")
        
        # Load Scaler
        ml_assets['scaler'] = joblib.load(config['preprocessor']['scaler_path'])
        
        # Load Feature Columns
        with open(config['preprocessor']['specialty_stats_path'], 'r') as f:
            stats = json.load(f)
            ml_assets['final_feature_columns'] = stats['final_feature_columns']
        # However, some components (like SHAP explainer and Monitor) still expect a DataFrame or array.
        
        # Load LEIE Exclusions - Handled in DB migration or query time
        
        # Load K-Means and Scaler
        ml_assets['kmeans_model'] = joblib.load(config['preprocessor']['kmeans_model_path'])
        logger.info("--- Loaded K-Means Model ---")
        ml_assets['scaler'] = joblib.load(config['preprocessor']['scaler_path'])
        logger.info("--- Loaded Scaler ---")
        
        # Load Specialty Stats
        with open(config['preprocessor']['specialty_stats_path'], 'r') as f:
            stats = json.load(f)
            ml_assets['cost_stats'] = pd.DataFrame(stats['cost_stats'])
            ml_assets['spb_stats'] = pd.DataFrame(stats['spb_stats'])
            ml_assets['median_pagerank'] = stats['median_pagerank']
            ml_assets['final_feature_columns'] = stats['final_feature_columns']
        logger.info("--- Loaded Specialty Stats ---")
        
        # Initialize SHAP Explainer
        final_feature_columns = ml_assets['final_feature_columns']
        
        # Load background data from DB for SHAP
        from src.database import get_db_connection
        with get_db_connection() as conn:
            # Sample 100 rows for background
            background_df = pd.read_sql_query("SELECT * FROM providers ORDER BY RANDOM() LIMIT 100", conn)
            
        # Ensure columns match
        background_data_raw = background_df[final_feature_columns]
        background_data_scaled = ml_assets['scaler'].transform(background_data_raw)
        
        prediction_function = lambda x: ml_assets['fraud_model'].predict(x).ravel()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Initialize KernelExplainer with SCALED background data
            ml_assets['explainer'] = shap.KernelExplainer(prediction_function, background_data_scaled)
        logger.info("--- Initialized SHAP Explainer ---")

        # Risk Score Pre-calculation is now done in migration script.


        # Initialize Agents
        logger.info("--- Initializing Agents... ---")
        ml_assets['investigator'] = InvestigatorAgent(config)
        logger.info("--- Initialized Investigator ---")
        ml_assets['analyst'] = AnalystAgent(
            config, 
            ml_assets['fraud_model'], 
            ml_assets['explainer'], 
            ml_assets['scaler'], 
            final_feature_columns
        )
        logger.info("--- Initialized Analyst ---")
        ml_assets['reporter'] = ReporterAgent(config)
        logger.info("--- Initialized Reporter ---")
        ml_assets['supervisor'] = SupervisorAgent(config)
        logger.info("--- Initialized Supervisor ---")
        ml_assets['monitor'] = MonitorAgent(
            ml_assets['fraud_model'],
            ml_assets['scaler'],
            None, # feature_store is now in DB
            final_feature_columns,
            config=config,
            ml_assets=ml_assets,  # pass full dict for direct pipeline calls (no HTTP)
        )
        logger.info("--- Initialized Monitor ---")
        ml_assets['investigation_count'] = 0
        
        # Start Background Monitor
        ml_assets['monitor'].start()

        # Initialize Semantic Search
        logger.info("--- Initializing Semantic Search Engine... ---")
        search_engine = SemanticSearchEngine()
        # We need to pass the feature_store (DataFrame) to index it
        # Ensure feature_store has the required columns or map them
        # The engine expects: specialty, risk_score, cost_per_service, services_per_bene, Prscrbr_First_Name, Prscrbr_Last_Org_Name
        # Our feature_store has these (some might be in raw data, but we loaded them into feature_store in main.py usually)
        # Let's check if we need to join with raw data or if feature_store has them.
        # In this refactor, feature_store is loaded from 'data/provider_features.csv'.
        # We might need to ensure string columns are present.
        
        # We might need to ensure string columns are present.
        
        # For development/verification, sample the data to avoid long indexing times
        # For development/verification, sample the data to avoid long indexing times
        from src.database import get_db_connection
        with get_db_connection() as conn:
             search_df = pd.read_sql_query("SELECT * FROM providers LIMIT 1000", conn)
        search_engine.set_data(search_df)
        ml_assets['search_engine'] = search_engine
        logger.info("--- Semantic Search Engine Initialized (Lazy Loading) ---")

        # Start Training Scheduler (if enabled)
        from src.training.scheduler import start_training_scheduler
        scheduler = start_training_scheduler(config)
        if scheduler:
            ml_assets['training_scheduler'] = scheduler

    except Exception as e:
        logger.error(f"CRITICAL ERROR LOADING ASSETS: {e}")
        raise e

    yield
    
    # Shutdown logic
    logger.info("--- Shutting down application ---")
    
    # Stop training scheduler
    if 'training_scheduler' in ml_assets:
        ml_assets['training_scheduler'].stop()
    
    ml_assets.clear()
    logger.info("--- ML assets cleared ---")
