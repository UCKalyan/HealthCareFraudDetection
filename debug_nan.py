import pandas as pd
import numpy as np

def debug_nan_robust():
    print("Debugging Robust NaN replacement...")
    
    # Simulate data with mixed types of NaNs
    data = {
        'Prscrbr_First_Name': [np.nan],
        'Prscrbr_Last_Org_Name': ["NaN"], # String NaN
        'specialty': [float('nan')],
        'cost_per_service': [np.nan],
        'provider_archetype_0': [1.0]
    }
    df = pd.DataFrame(data)
    
    print(f"Original:\n{df.iloc[0].to_dict()}")
    
    # Robust Logic
    df = df.replace(["NaN", "nan"], np.nan)
    
    df = df.fillna({
        'Prscrbr_First_Name': 'N/A',
        'Prscrbr_Last_Org_Name': 'N/A',
        'specialty': 'Unknown',
        'cost_per_service': 0,
        'services_per_bene': 0
    }).fillna(0)
    
    features = df.iloc[0].to_dict()
    
    # Rename logic
    clean_features = {}
    for k, v in features.items():
        if k.startswith('provider_archetype_'):
            new_key = k.replace('provider_archetype_', 'Provider Archetype ').title()
            clean_features[new_key] = v
        else:
            clean_features[k] = v
            
    print(f"Final Cleaned:\n{clean_features}")
    
    # Assertions
    assert clean_features['Prscrbr_Last_Org_Name'] == 'N/A'
    assert 'Provider Archetype 0' in clean_features
    
    print("SUCCESS: Robust fix works.")

if __name__ == "__main__":
    debug_nan_robust()
