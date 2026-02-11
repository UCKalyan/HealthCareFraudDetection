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
import sqlite3
import httpx
from src.utils.config_loader import load_config

# Initialize FastMCP Server
mcp = FastMCP("Healthcare Fraud Detection")

# Load Assets (Similar to API Server but for MCP context)
# Redirect all stdout to stderr during loading to prevent polluting MCP stream
with contextlib.redirect_stdout(sys.stderr):
    print("--- Loading MCP Assets... ---", file=sys.stderr)
    config = load_config('config.yaml')
    feature_store = pd.read_csv(config['preprocessor']['feature_store_path']).set_index('provider_id')
    model = tf.keras.models.load_model(config['preprocessor']['model_path'])
    
    # Load Fast Model (if exists) for Dual-Score Visualization
    fast_model_path = config['preprocessor']['model_path'].replace('.keras', '_fast.keras')
    model_fast = None
    if os.path.exists(fast_model_path):
        try:
            model_fast = tf.keras.models.load_model(fast_model_path)
            print(f"--- Loaded Fast Model from {fast_model_path} ---", file=sys.stderr)
        except Exception as e:
            print(f"--- Failed to load Fast Model: {e} ---", file=sys.stderr)
            
    scaler = joblib.load(config['preprocessor']['scaler_path'])

    # Load Transaction Model
    transaction_model = None
    transaction_scaler = None
    try:
        tx_model_path = "models/transaction_fraud_model.keras"
        tx_scaler_path = "models/transaction_scaler.joblib"
        if os.path.exists(tx_model_path):
             transaction_model = tf.keras.models.load_model(tx_model_path)
             transaction_scaler = joblib.load(tx_scaler_path)
             print(f"--- Loaded Transaction Model from {tx_model_path} ---", file=sys.stderr)
    except Exception as e:
        print(f"--- Failed to load Transaction Model: {e} ---", file=sys.stderr)

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
def predict_fraud_risk(npi: int) -> str:
    """
    Calculates the fraud risk score for a provider using the Dual-Speed Nested Learning model.
    Returns both the Stable Score (Slow Model) and Early Warning Score (Fast Model).
    
    Args:
        npi: The National Provider Identifier.
    """
    print(f"--- Tool Call: predict_fraud_risk(npi={npi}) ---", file=sys.stderr)
    try:
        provider_data = feature_store.loc[[npi]]
        provider_data_aligned = provider_data.reindex(columns=final_feature_columns, fill_value=0)
        feature_vector = scaler.transform(provider_data_aligned)
        
        # 1. Stable Score (Slow Model)
        stable_score = float(model.predict(feature_vector, verbose=0)[0][0])
        
        # 2. Early Warning Score (Fast Model)
        fast_score = -1.0
        if model_fast:
            fast_score = float(model_fast.predict(feature_vector, verbose=0)[0][0])
            
        result = {
            "npi": npi,
            "risk_score": stable_score,
            "early_warning_score": fast_score if fast_score != -1.0 else None,
            "status": "High Risk" if stable_score > 0.7 else "Medium Risk" if stable_score > 0.3 else "Low Risk"
        }
        
        # Add "Emerging Threat" flag
        if fast_score > 0.8 and stable_score < 0.5:
            result["alert"] = "⚠️ EMERGING THREAT: Recent behavior deviates significantly from history."
            
        return json.dumps(result, indent=2)
        
    except KeyError:
        return json.dumps({"error": "Provider not found."})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def explain_fraud_risk(npi: int) -> str:
    """
    Generates a SHAP explanation for the fraud risk score.
    Returns a text summary of the top contributing features.
    Args:
        npi: The National Provider Identifier.
    """
    print(f"--- Tool Call: explain_fraud_risk(npi={npi}) ---", file=sys.stderr)
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
        return explanation
    except KeyError:
        return "Provider not found."

@mcp.tool()
def approve_provider(npi: int, reason: str) -> str:
    """
    Approves/Verifies a provider, setting their risk score to 0 and status to 'verified'.
    IMPORTANT: This is a high-stakes action. Ensure you have user confirmation before proceeding.
    
    Args:
        npi: The National Provider Identifier.
        reason: The justification for approval.
    """
    print(f"--- Tool Call: approve_provider(npi={npi}, reason='{reason}') ---", file=sys.stderr)
    from src.services.action_service import ActionService
    service = ActionService(
        providers_db_path="../shared-data/databases/providers.db",
        finance_db_path="../shared-data/databases/finance.db",
        finance_api_url="http://localhost:8001"
    )
    result = service.approve_provider(npi, reason)
    
    # Update In-Memory Store if successful
    if result["success"] and npi in feature_store.index:
        feature_store.at[npi, 'risk_score'] = 0.0
        
    return result["message"]

@mcp.tool()
def flag_transaction(transaction_id: str, reason: str) -> str:
    """
    Flags a suspicious transaction by placing a payment hold on it.
    IMPORTANT: This affects financial processing.
    
    Args:
        transaction_id: The ID of the transaction to flag.
        reason: The reason for flagging this transaction.
    """
    print(f"--- Tool Call: flag_transaction(id={transaction_id}, reason='{reason}') ---", file=sys.stderr)
    from src.services.action_service import ActionService
    service = ActionService(
        providers_db_path="../shared-data/databases/providers.db",
        finance_db_path="../shared-data/databases/finance.db",
        finance_api_url="http://localhost:8001"
    )
    result = service.flag_transaction(transaction_id, reason)
    result = service.flag_transaction(transaction_id, reason)
    return result["message"]

@mcp.tool()
def analyze_transaction_risk(amount: float, avg_amount: float, is_weekend: int, amount_deviation: float) -> str:
    """
    Analyzes a specific transaction using the DNN model to predict fraud risk.
        is_weekend: 1 if weekend, 0 otherwise.
        amount_deviation: amount / avg_amount.
    """
    print(f"--- Tool Call: analyze_transaction_risk(amount={amount}, weekend={is_weekend}) ---", file=sys.stderr)
    if not transaction_model:
        return "Transaction model not loaded. Please ensure the model is trained."
    
    try:
        features = np.array([[amount, avg_amount, is_weekend, amount_deviation]])
        features_scaled = transaction_scaler.transform(features)
        score = float(transaction_model.predict(features_scaled, verbose=0)[0][0])
        
        risk_level = "High" if score > 0.8 else "Medium" if score > 0.5 else "Low"
        return json.dumps({
            "fraud_risk_score": score,
            "risk_level": risk_level,
            "analysis": "Suspicious pattern detected (High Amount/Weekend)" if score > 0.8 else "Normal transaction pattern"
        })
    except Exception as e:
        return f"Error analyzing transaction: {str(e)}"

if __name__ == "__main__":
    mcp.run()
