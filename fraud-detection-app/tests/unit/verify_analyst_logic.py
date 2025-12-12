import pandas as pd
from src.workflows.fraud_graph import detect_anomalies_node

def test_analyst():
    print("Testing Analyst Logic...")
    
    # Case 1: High Volume, Risk Driver (SHAP > 0)
    state1 = {
        'provider_data': pd.DataFrame([{
            'cost_per_service': 100,
            'services_per_bene': 15, # High
            'total_services': 100
        }]),
        'risk_score': 0.9,
        'shap_values': [{'name': 'services_per_bene', 'value': 0.5}], # Positive impact
        'trace': [],
        'graph_data': {'elements': {'nodes': [{}, {}]}}
    }
    
    res1 = detect_anomalies_node(state1)
    print("\nCase 1 (High Vol, Risk Driver):")
    print(res1['trace'][-1])
    # We can't easily see the 'analyst_finding' return value because the node modifies state in place or returns updates.
    # Wait, the node returns a dict of updates.
    # Let's check the return value of the function.
    # The function returns `{"analyst_finding": analyst_finding, "trace": trace}` (I need to check the file content again to be sure of the return keys).
    
    # Case 2: High Volume, Benign (SHAP < 0)
    state2 = {
        'provider_data': pd.DataFrame([{
            'cost_per_service': 100,
            'services_per_bene': 15, # High
            'total_services': 100
        }]),
        'risk_score': 0.2,
        'shap_values': [{'name': 'services_per_bene', 'value': -0.5}], # Negative impact
        'trace': [],
        'graph_data': {'elements': {'nodes': [{}, {}]}}
    }
    
    res2 = detect_anomalies_node(state2)
    print("\nCase 2 (High Vol, Benign):")
    print(res2['trace'][-1])
    
    print("\n--- FINDING OUTPUTS ---")
    print("Case 1 Finding (Investigator/Rules):")
    print(res1['investigator_finding'])
    print("\nCase 2 Finding (Investigator/Rules):")
    print(res2['investigator_finding'])
    
if __name__ == "__main__":
    test_analyst()
