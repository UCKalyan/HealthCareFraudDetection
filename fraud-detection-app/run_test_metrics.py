import sys
import os
import pandas as pd
import numpy as np

# Setup paths
sys.path.insert(0, os.path.abspath('.'))

from src.utils.config_loader import load_config
from src.training.incremental_retrain import incremental_retrain

def main():
    config = load_config()
    
    # Load recently uploaded batch data and inject fake labels
    df = pd.read_csv('data/processed/20260221_155121_batch_5.csv')
    
    # Drop existing fake is_fraud if it exists but is broken
    if 'is_fraud' in df.columns:
        df = df.drop(columns=['is_fraud'])
        
    np.random.seed(42)
    df['is_fraud'] = np.random.choice([0, 1], size=len(df), p=[0.9, 0.1])
    
    print(f"Loaded {len(df)} rows. Fraud cases: {df['is_fraud'].sum()}")
    
    # Run the retrain directly
    results = incremental_retrain(config, new_data=df, mode='incremental')
    
    print("\n" + "="*60)
    print("FINISHED!")
    for k, v in results.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")
    print("="*60)

if __name__ == '__main__':
    main()
