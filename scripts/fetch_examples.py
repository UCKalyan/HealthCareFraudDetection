import sqlite3
import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_db_connection

def fetch_examples():
    conn = sqlite3.connect('data/providers.db')
    
    # We need to find providers that fit the risk profiles.
    # Since we don't have pre-calculated risk scores in the DB (they are calculated on the fly),
    # we will look for providers with characteristics that MATCH the risk profiles.
    
    # High Risk: High Cost AND High Volume
    high_risk_query = """
    SELECT * FROM providers 
    WHERE cost_per_service > 500 AND services_per_bene > 15
    LIMIT 1
    """
    
    # Medium Risk: High Cost OR High Volume (but not both extreme)
    medium_risk_query = """
    SELECT * FROM providers 
    WHERE (cost_per_service > 300 AND services_per_bene < 10)
       OR (cost_per_service < 100 AND services_per_bene > 20)
    LIMIT 1
    """
    
    # Low Risk: Low Cost AND Low Volume
    low_risk_query = """
    SELECT * FROM providers 
    WHERE cost_per_service < 100 AND services_per_bene < 5
    LIMIT 1
    """
    
    print("--- High Risk Example ---")
    high = pd.read_sql_query(high_risk_query, conn)
    if not high.empty:
        print(high.iloc[0][['provider_id', 'Prscrbr_First_Name', 'Prscrbr_Last_Org_Name', 'specialty', 'cost_per_service', 'services_per_bene']])
    else:
        print("None found")

    print("\n--- Medium Risk Example ---")
    med = pd.read_sql_query(medium_risk_query, conn)
    if not med.empty:
        print(med.iloc[0][['provider_id', 'Prscrbr_First_Name', 'Prscrbr_Last_Org_Name', 'specialty', 'cost_per_service', 'services_per_bene']])
    else:
        print("None found")

    print("\n--- Low Risk Example ---")
    low = pd.read_sql_query(low_risk_query, conn)
    if not low.empty:
        print(low.iloc[0][['provider_id', 'Prscrbr_First_Name', 'Prscrbr_Last_Org_Name', 'specialty', 'cost_per_service', 'services_per_bene']])
    else:
        print("None found")

    conn.close()

if __name__ == "__main__":
    fetch_examples()
