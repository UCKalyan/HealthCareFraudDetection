"""
Test script to verify database integration for batch uploads.
Run after uploading a batch file to verify providers are in database.
"""

import sqlite3
from pathlib import Path

def check_batch_providers_in_db(batch_file: str = "data/test_samples/batch_0.csv"):
    """Check if providers from batch file are in database."""
    
    import pandas as pd
    
    # Load batch file
    batch_df = pd.read_csv(batch_file)
    sample_npis = batch_df['provider_id'].head(10).tolist()
    
    print(f"Checking database for {len(sample_npis)} sample providers from {batch_file}...")
    print("=" * 70)
    
    # Connect to database
    db_path = Path("fraud_detection.db")
    if not db_path.exists():
        print("❌ Database not found: fraud_detection.db")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check each provider
    found_count = 0
    for npi in sample_npis:
        cursor.execute("""
            SELECT provider_id, risk_score, Prscrbr_Type 
            FROM providers 
            WHERE provider_id = ?
        """, (str(int(npi)),))
        
        result = cursor.fetchone()
        if result:
            found_count += 1
            print(f"✅ NPI {result[0]:>12} | Risk: {result[1]:.4f} | Specialty: {result[2]}")
        else:
            print(f"❌ NPI {int(npi):>12} | NOT FOUND in database")
    
    conn.close()
    
    print("=" * 70)
    print(f"Found {found_count}/{len(sample_npis)} providers in database")
    
    if found_count == len(sample_npis):
        print("\n✅ SUCCESS: All sample providers found in database!")
        print("   Providers are searchable via UI and ready for agent analysis.")
    else:
        print(f"\n⚠️  Only {found_count}/{len(sample_npis)} providers found.")
        print("   Make sure to upload the batch file via the API first.")

if __name__ == "__main__":
    check_batch_providers_in_db()
