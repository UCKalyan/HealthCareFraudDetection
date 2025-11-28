import sys
import os
import contextlib

# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from mcp.server.fastmcp import FastMCP
import pandas as pd
import tensorflow as tf
import joblib
import json
import shap
import numpy as np
import warnings
from src.utils.config_loader import load_config

# Initialize FastMCP Server
mcp = FastMCP("Healthcare Fraud Detection")

# Load Assets (Similar to API Server but for MCP context)
# Redirect all stdout to stderr during loading to prevent polluting MCP stream
with contextlib.redirect_stdout(sys.stderr):
    print("--- Loading MCP Assets... ---", file=sys.stderr)
    config = load_config('config.yaml')
    feature_store = pd.read_csv(config['preprocessor']['feature_store_path']).set_index('provider_id')
    model = tf.keras.models.load_model(config['training']['model_path'])
    scaler = joblib.load(config['preprocessor']['scaler_path'])

    with open(config['preprocessor']['specialty_stats_path'], 'r') as f:
        stats = json.load(f)
        final_feature_columns = stats['final_feature_columns']

    background_data = shap.sample(feature_store[final_feature_columns], 100)
    # IMPORTANT: verbose=0 is crucial to prevent Keras progress bars from breaking MCP JSON-RPC
    prediction_function = lambda x: model.predict(x, verbose=0).ravel()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        explainer = shap.KernelExplainer(prediction_function, background_data)

    print("--- MCP Server Ready ---", file=sys.stderr)

@mcp.resource("fraud://providers/list")
def list_high_risk_providers() -> str:
    """Returns a list of providers with high cost metrics."""
    # Simple filter for demo purposes
    high_risk = feature_store[feature_store['cost_per_service'] > 200].head(10)
    return high_risk[['Prscrbr_First_Name', 'Prscrbr_Last_Org_Name', 'specialty']].to_markdown()

@mcp.resource("fraud://providers/{npi}")
def get_provider_resource(npi: str) -> str:
    """Get full details for a specific provider by NPI."""
    try:
        npi_int = int(npi)
        provider = feature_store.loc[npi_int]
        return provider.to_markdown()
    except KeyError:
        return f"Provider {npi} not found."
    except ValueError:
        return "Invalid NPI format."

@mcp.tool()
def get_provider_data(npi: int) -> str:
    """
    Fetches raw feature data for a provider.
    Args:
        npi: The National Provider Identifier (10 digits).
    """
    try:
        provider = feature_store.loc[npi]
        return provider.to_json()
    except KeyError:
        return "Provider not found."

@mcp.tool()
def predict_fraud_risk(npi: int) -> float:
    """
    Calculates the fraud risk score (0.0 to 1.0) for a provider using the Deep Learning model.
    Args:
        npi: The National Provider Identifier.
    """
    try:
        provider_data = feature_store.loc[[npi]]
        provider_data_aligned = provider_data.reindex(columns=final_feature_columns, fill_value=0)
        feature_vector = scaler.transform(provider_data_aligned)
        score = model.predict(feature_vector, verbose=0)[0][0]
        return float(score)
    except KeyError:
        return -1.0
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

@mcp.tool()
def explain_fraud_risk(npi: int) -> str:
    """
    Generates a SHAP explanation for the fraud risk score.
    Returns a text summary of the top contributing features.
    Args:
        npi: The National Provider Identifier.
    """
    try:
        provider_data = feature_store.loc[[npi]]
        provider_data_aligned = provider_data.reindex(columns=final_feature_columns, fill_value=0)
        feature_vector = scaler.transform(provider_data_aligned)
        
        shap_values = explainer.shap_values(feature_vector)
        shap_values_flat = np.array(shap_values).flatten()
        
        # Get top 3 features
        top_indices = np.argsort(np.abs(shap_values_flat))[-3:][::-1]
        explanation = "Top Risk Factors:\n"
        for idx in top_indices:
            feature_name = final_feature_columns[idx]
            impact = shap_values_flat[idx]
            explanation += f"- {feature_name}: {impact:+.4f}\n"
            
        return explanation
    except KeyError:
        return "Provider not found."

if __name__ == "__main__":
    mcp.run()
