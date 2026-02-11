
import sys
import os
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.getcwd())

from src.workflows.fraud_graph import calculate_risk_node, detect_anomalies_node

def verify_fixes():
    print("--- Verifying Workflow Fixes ---")
    
    # Mock State
    mock_assets = {
        'final_feature_columns': ['col1', 'col2'],
        'scaler': MagicMock(),
        'fraud_model': MagicMock(),
        'explainer': MagicMock()
    }
    
    # Mock Scaler
    mock_assets['scaler'].transform.return_value = np.array([[0.1, 0.2]])
    
    # Mock Model
    mock_assets['fraud_model'].predict.return_value = np.array([[0.8]]) # High Risk
    
    # Mock Explainer
    mock_assets['explainer'].shap_values.return_value = [np.array([[0.1, 0.2]]), np.array([[0.1, 0.2]])]
    
    state = {
        'npi': 12345,
        'provider_data': pd.DataFrame([{'col1': 10, 'col2': 20}]),
        'ml_assets': mock_assets,
        'trace': []
    }
    
    # 1. Test calculate_risk_node
    print("\nTesting calculate_risk_node...")
    result_risk = calculate_risk_node(state)
    
    # Check Keys
    if 'analyst_finding' in result_risk:
        print("✅ 'analyst_finding' key present.")
    else:
        print("❌ 'analyst_finding' key MISSING.")
        
    # Check Text
    text = result_risk.get('analyst_finding', '')
    if "Next Step: Initiating network analysis" in text:
        print("✅ Text updated to 'Next Step'.")
    else:
        print(f"❌ Text NOT updated. Found: {text}")
        
    if "Recommendation: Proceed to network analysis" not in text:
        print("✅ Old recommendation removed.")
    else:
        print("❌ Old recommendation still present.")
        
    # 2. Test detect_anomalies_node
    print("\nTesting detect_anomalies_node...")
    
    # Update state with risk result for the next node
    state.update(result_risk)
    state['graph_data'] = {'elements': {'nodes': [1, 2, 3]}} # Mock graph
    
    result_anom = detect_anomalies_node(state)
    
    # Check Keys
    if 'investigator_finding' in result_anom:
        print("✅ 'investigator_finding' key present.")
    else:
        print("❌ 'investigator_finding' key MISSING.")
        
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_fixes()
