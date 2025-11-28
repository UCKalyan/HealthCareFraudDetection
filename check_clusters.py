import pandas as pd
import sys
import os
from src.utils.config_loader import load_config

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_clusters():
    print("Checking cluster membership...")
    config = load_config('config.yaml')
    feature_store = pd.read_csv(config['preprocessor']['feature_store_path'])
    
    archetype_cols = [c for c in feature_store.columns if 'provider_archetype_' in c]
    print(f"Archetype Columns: {archetype_cols}")
    
    # Check if any row has sum > 1 (overlapping clusters)
    sums = feature_store[archetype_cols].sum(axis=1)
    overlaps = sums[sums > 1.0001] # Tolerance for float
    
    if not overlaps.empty:
        print(f"WARNING: {len(overlaps)} providers have multiple clusters!")
        print(feature_store.loc[overlaps.index, archetype_cols].head())
    else:
        print("CONFIRMED: Providers belong to exactly one cluster (or zero if outliers).")
        
    # Check specific NPI 1134558984
    npi = 1134558984
    if 'provider_id' in feature_store.columns:
        row = feature_store[feature_store['provider_id'] == npi]
    else:
        row = feature_store[feature_store.index == npi] # If index is NPI
        
    if not row.empty:
        print(f"\nNPI {npi} Cluster Values:")
        print(row[archetype_cols].iloc[0].to_dict())
    else:
        print(f"NPI {npi} not found.")

if __name__ == "__main__":
    check_clusters()
