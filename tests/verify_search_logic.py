import sys
import os
import pandas as pd
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.semantic_search import SemanticSearchEngine

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_search():
    # Create dummy data
    data = {
        'provider_id': [1, 2, 3, 4, 5, 6],
        'Prscrbr_First_Name': ['John', 'Jane', 'Bob', 'Alice', 'Tom', 'Sue'],
        'Prscrbr_Last_Org_Name': ['Doe', 'Smith', 'Jones', 'Brown', 'Wilson', 'Davis'],
        'specialty': ['Anesthesiology', 'Anesthesiology', 'Anesthesiology', 'Cardiology', 'Cardiology', 'Anesthesiology'],
        'risk_score': [0.9, 0.8, 0.2, 0.9, 0.1, 0.5], # 1,2 High; 3 Low; 4 High; 5 Low; 6 Medium
        'cost_per_service': [100, 100, 100, 100, 100, 100],
        'services_per_bene': [10, 10, 10, 10, 10, 10]
    }
    df = pd.DataFrame(data)
    
    engine = SemanticSearchEngine()
    engine.set_data(df)
    engine._ensure_indexed()
    
    print("\n--- Test 1: 'high anesthesiology' ---")
    results = engine.search("high anesthesiology", k=10)
    for r in results:
        print(f"Name: {r['name']}, Specialty: {r['specialty']}, Risk: {r['risk_score']}, Status: {r['risk_status']}")
        
    print("\n--- Test 2: 'low risk anesthesiology' ---")
    results = engine.search("low risk anesthesiology", k=10)
    for r in results:
        print(f"Name: {r['name']}, Specialty: {r['specialty']}, Risk: {r['risk_score']}, Status: {r['risk_status']}")

if __name__ == "__main__":
    test_search()
