"""
Clean Provider Features Dataset
Removes outlier providers and prepares cleaned dataset for retraining
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import PowerTransformer, QuantileTransformer
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path("data")
ANALYSIS_DIR = Path("analysis_output")
OUTPUT_DIR = Path("data/cleaned")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_outlier_list():
    """Load list of outlier providers to remove"""
    outlier_file = ANALYSIS_DIR / "outlier_providers_to_remove.csv"
    
    if not outlier_file.exists():
        print("⚠️  No outlier list found!")
        print("   Run 'python analyze_data_skewness.py' first!")
        return set()
    
    outlier_df = pd.read_csv(outlier_file)
    outliers = set(outlier_df['provider_id'].values)
    
    print(f"📋 Loaded {len(outliers)} outlier providers to remove")
    return outliers

def load_skewness_info():
    """Load feature skewness information"""
    skewness_file = ANALYSIS_DIR / "feature_skewness.csv"
    
    if not skewness_file.exists():
        print("⚠️  No skewness analysis found!")
        return pd.DataFrame()
    
    return pd.read_csv(skewness_file)

def clean_dataset(df, outliers_to_remove):
    """Remove outlier providers"""
    print("\n🧹 Cleaning dataset...")
    print(f"   Original: {len(df):,} providers")
    
    cleaned_df = df[~df['provider_id'].isin(outliers_to_remove)].copy()
    
    removed = len(df) - len(cleaned_df)
    print(f"   Removed: {removed:,} providers ({removed/len(df):.2%})")
    print(f"   Cleaned: {len(cleaned_df):,} providers")
    
    return cleaned_df

def apply_log_transform(df, features):
    """Apply log transformation to specified features"""
    print(f"\n📊 Applying log transformation to {len(features)} features...")
    
    transformed_df = df.copy()
    
    for feature in features:
        if feature in df.columns:
            # Add 1 to handle zeros, then log transform
            transformed_df[feature] = np.log1p(df[feature])
            print(f"   ✓ {feature}")
    
    return transformed_df

def apply_power_transform(df, features):
    """Apply Yeo-Johnson power transformation"""
    print(f"\n🔧 Applying power transformation to {len(features)} features...")
    
    transformed_df = df.copy()
    pt = PowerTransformer(method='yeo-johnson')
    
    for feature in features:
        if feature in df.columns:
            try:
                transformed_values = pt.fit_transform(df[[feature]])
                transformed_df[feature] = transformed_values
                print(f"   ✓ {feature}")
            except Exception as e:
                print(f"   ✗ {feature} - Failed: {str(e)}")
    
    return transformed_df

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🧹 PROVIDER FEATURES CLEANING")
    print("="*60)
    
    # Load data
    print("\n📂 Loading dataset...")
    df = pd.read_csv(DATA_DIR / "provider_features.csv")
    print(f"✅ Loaded {len(df):,} providers")
    
    # Load outliers and skewness info
    outliers = load_outlier_list()
    skewness_df = load_skewness_info()
    
    if len(outliers) == 0:
        print("\n⚠️  No cleaning needed. Exiting.")
        return
    
    # Clean dataset
    cleaned_df = clean_dataset(df, outliers)
    
    # Identify features for transformation
    if len(skewness_df) > 0:
        highly_skewed = skewness_df[skewness_df['Highly_Skewed'] == True]
        
        # Features for log transform (counts/volumes)
        log_features = [
            'total_service_cost', 'total_services', 'total_benes_phys',
            'total_drug_cost', 'total_scripts', 'total_benes_presc',
            'total_claim_cost', 'total_benes'
        ]
        log_features = [f for f in log_features if f in cleaned_df.columns]
        
        # Features for power transform (ratios and archetypes)
        power_features = [
            'services_per_bene', 'cost_per_service', 'pagerank_centrality',
            'provider_archetype_0', 'provider_archetype_1', 
            'provider_archetype_2', 'provider_archetype_3', 'provider_archetype_4'
        ]
        power_features = [f for f in power_features if f in cleaned_df.columns]
        
        # Apply transformations
        log_transformed_df = apply_log_transform(cleaned_df, log_features)
        fully_transformed_df = apply_power_transform(log_transformed_df, power_features)
    else:
        log_transformed_df = cleaned_df
        fully_transformed_df = cleaned_df
    
    # Save datasets
    print("\n💾 Saving cleaned datasets...")
    
    # 1. Just outliers removed
    cleaned_df.to_csv(OUTPUT_DIR / "provider_features_cleaned.csv", index=False)
    print(f"   ✓ {OUTPUT_DIR / 'provider_features_cleaned.csv'}")
    print(f"     (Outliers removed only)")
    
    # 2. Log transformations applied
    log_transformed_df.to_csv(OUTPUT_DIR / "provider_features_log_transformed.csv", index=False)
    print(f"   ✓ {OUTPUT_DIR / 'provider_features_log_transformed.csv'}")
    print(f"     (Outliers removed + log transform)")
    
    # 3. Full transformations
    fully_transformed_df.to_csv(OUTPUT_DIR / "provider_features_fully_transformed.csv", index=False)
    print(f"   ✓ {OUTPUT_DIR / 'provider_features_fully_transformed.csv'}")
    print(f"     (Outliers removed + all transformations)")
    
    # Summary
    print("\n" + "="*60)
    print("✅ CLEANING COMPLETE!")
    print("="*60)
    
    print(f"\n📊 Summary:")
    print(f"   Original providers: {len(df):,}")
    print(f"   Cleaned providers: {len(cleaned_df):,}")
    print(f"   Removed: {len(df) - len(cleaned_df):,} ({(len(df) - len(cleaned_df))/len(df):.2%})")
    
    print(f"\n📁 Generated 3 versions:")
    print(f"   1. provider_features_cleaned.csv")
    print(f"      → Use for minimal changes")
    print(f"   ")
    print(f"   2. provider_features_log_transformed.csv")
    print(f"      → Use for moderate transformation")
    print(f"   ")
    print(f"   3. provider_features_fully_transformed.csv")
    print(f"      → Use for maximum normalization (RECOMMENDED)")
    
    print(f"\n📌 Next Steps:")
    print(f"   1. Update src/training/train.py to use cleaned data:")
    print(f"      df = pd.read_csv('data/cleaned/provider_features_fully_transformed.csv')")
    print(f"   ")
    print(f"   2. Retrain the model:")
    print(f"      python src/training/train.py")
    print(f"   ")
    print(f"   3. Compare performance with original model")

if __name__ == "__main__":
    main()
