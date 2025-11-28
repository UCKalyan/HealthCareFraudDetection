"""
Provider Features Skewness Analysis
Analyzes the provider_features.csv for skewed data and outliers
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
DATA_DIR = Path("data")
OUTPUT_DIR = Path("analysis_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Skewness thresholds
SKEWNESS_THRESHOLD = 2.0
OUTLIER_Z_SCORE = 3.5

def load_data():
    """Load the provider features dataset"""
    print("📂 Loading dataset...")
    
    df = pd.read_csv(DATA_DIR / "provider_features.csv")
    
    print(f"✅ Loaded {len(df):,} provider records")
    print(f"✅ Features: {len(df.columns)} columns")
    
    return df

def analyze_feature_skewness(df):
    """Analyze skewness of all numerical features"""
    print("\n" + "="*60)
    print("📊 FEATURE SKEWNESS ANALYSIS")
    print("="*60)
    
    # Select numerical columns
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude ID columns
    numerical_cols = [col for col in numerical_cols if not col.endswith('_id')]
    
    skewness_results = []
    
    for col in numerical_cols:
        if df[col].nunique() > 1:  # Skip constant columns
            data = df[col].dropna()
            if len(data) > 0:
                skew = stats.skew(data)
                kurt = stats.kurtosis(data)
                
                skewness_results.append({
                    'Feature': col,
                    'Skewness': skew,
                    'Kurtosis': kurt,
                    'Mean': data.mean(),
                    'Median': data.median(),
                    'Std': data.std(),
                    'Min': data.min(),
                    'Max': data.max(),
                    'Q25': data.quantile(0.25),
                    'Q75': data.quantile(0.75),
                    'Highly_Skewed': abs(skew) > SKEWNESS_THRESHOLD
                })
    
    skewness_df = pd.DataFrame(skewness_results).sort_values('Skewness', key=abs, ascending=False)
    
    # Display results
    print(f"\nTop 15 Most Skewed Features:")
    print(skewness_df[['Feature', 'Skewness', 'Mean', 'Median']].head(15).to_string(index=False))
    
    highly_skewed = skewness_df[skewness_df['Highly_Skewed']]
    print(f"\n⚠️  Found {len(highly_skewed)} highly skewed features (|skewness| > {SKEWNESS_THRESHOLD}):")
    for _, row in highly_skewed.iterrows():
        print(f"   • {row['Feature']}: {row['Skewness']:.2f}")
    
    # Save results
    skewness_df.to_csv(OUTPUT_DIR / 'feature_skewness.csv', index=False)
    print(f"\n💾 Saved: {OUTPUT_DIR / 'feature_skewness.csv'}")
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    top_20 = skewness_df.head(20)
    colors = ['red' if abs(s) > SKEWNESS_THRESHOLD else 'blue' for s in top_20['Skewness']]
    plt.barh(top_20['Feature'], top_20['Skewness'], color=colors)
    plt.xlabel('Skewness', fontsize=12)
    plt.title('Top 20 Most Skewed Features', fontsize=14, fontweight='bold')
    plt.axvline(x=SKEWNESS_THRESHOLD, color='red', linestyle='--', label=f'Threshold: ±{SKEWNESS_THRESHOLD}')
    plt.axvline(x=-SKEWNESS_THRESHOLD, color='red', linestyle='--')
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'feature_skewness_plot.png', dpi=300)
    print(f"📊 Saved: {OUTPUT_DIR / 'feature_skewness_plot.png'}")
    
    return skewness_df

def identify_outlier_providers(df):
    """Identify providers with extreme/outlier values"""
    print("\n" + "="*60)
    print("🔍 OUTLIER PROVIDER DETECTION")
    print("="*60)
    
    outlier_providers = []
    
    # Key metrics to check for outliers
    key_metrics = [
        'total_service_cost',
        'total_services',
        'total_benes_phys',
        'total_claim_cost',
        'total_benes',
        'cost_per_service',
        'services_per_bene'
    ]
    
    # Filter to only existing columns
    key_metrics = [m for m in key_metrics if m in df.columns]
    
    for metric in key_metrics:
        data = df[metric].fillna(0)
        z_scores = np.abs(stats.zscore(data))
        outliers = df[z_scores > OUTLIER_Z_SCORE]
        
        if len(outliers) > 0:
            print(f"\n📌 {metric}: Found {len(outliers)} outlier providers (Z-score > {OUTLIER_Z_SCORE})")
            
            for idx, row in outliers.head(10).iterrows():
                outlier_providers.append({
                    'provider_id': row['provider_id'],
                    'Metric': metric,
                    'Value': row[metric],
                    'Z_Score': z_scores[idx]
                })
    
    if len(outlier_providers) > 0:
        outlier_df = pd.DataFrame(outlier_providers)
        
        # Get unique provider IDs
        unique_outliers = outlier_df['provider_id'].unique()
        print(f"\n⚠️  Total unique outlier providers: {len(unique_outliers)}")
        
        # Save
        outlier_df.to_csv(OUTPUT_DIR / 'outlier_providers_detailed.csv', index=False)
        pd.DataFrame({'provider_id': unique_outliers}).to_csv(OUTPUT_DIR / 'outlier_providers_to_remove.csv', index=False)
        
        print(f"\n💾 Saved: {OUTPUT_DIR / 'outlier_providers_detailed.csv'}")
        print(f"💾 Saved: {OUTPUT_DIR / 'outlier_providers_to_remove.csv'}")
        
        return outlier_df
    else:
        print("\n✅ No extreme outliers found")
        return pd.DataFrame()

def create_distribution_plots(df, skewness_df):
    """Create distribution plots for highly skewed features"""
    print("\n" + "="*60)
    print("📈 CREATING DISTRIBUTION PLOTS")
    print("="*60)
    
    highly_skewed = skewness_df[skewness_df['Highly_Skewed']].head(9)  # Top 9 for 3x3 grid
    
    if len(highly_skewed) == 0:
        print("   No highly skewed features to plot")
        return
    
    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    axes = axes.flatten()
    
    for idx, (_, row) in enumerate(highly_skewed.iterrows()):
        if idx >= 9:
            break
        
        feature = row['Feature']
        data = df[feature].dropna()
        
        axes[idx].hist(data, bins=50, edgecolor='black', alpha=0.7)
        axes[idx].set_title(f"{feature}\n(Skewness: {row['Skewness']:.2f})", fontsize=10)
        axes[idx].set_xlabel('Value')
        axes[idx].set_ylabel('Frequency')
        axes[idx].grid(True, alpha=0.3)
    
    # Hide unused subplots
    for idx in range(len(highly_skewed), 9):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'skewed_distributions.png', dpi=300)
    print(f"📊 Saved: {OUTPUT_DIR / 'skewed_distributions.png'}")

def generate_summary_report(df, skewness_df, outlier_df):
    """Generate summary report"""
    print("\n" + "="*60)
    print("📄 SUMMARY REPORT")
    print("="*60)
    
    print(f"\n📊 Dataset Overview:")
    print(f"   Total Providers: {len(df):,}")
    print(f"   Total Features: {len(df.columns)}")
    print(f"   Numerical Features: {len(skewness_df)}")
    
    print(f"\n📈 Skewness Analysis:")
    print(f"   Highly Skewed Features: {(skewness_df['Highly_Skewed']).sum()}")
    print(f"   Average Skewness: {skewness_df['Skewness'].abs().mean():.2f}")
    
    if len(outlier_df) > 0:
        print(f"\n⚠️  Outlier Detection:")
        print(f"   Outlier Providers: {outlier_df['provider_id'].nunique()}")
        print(f"   Total Outlier Instances: {len(outlier_df)}")
    
    print(f"\n📁 Output Files:")
    print(f"   • feature_skewness.csv - Detailed skewness metrics")
    print(f"   • feature_skewness_plot.png - Visual of most skewed features")
    print(f"   • skewed_distributions.png - Distribution plots")
    if len(outlier_df) > 0:
        print(f"   • outlier_providers_detailed.csv - Detailed outlier analysis")
        print(f"   • outlier_providers_to_remove.csv - List of outlier provider IDs")

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🔬 PROVIDER FEATURES SKEWNESS ANALYSIS")
    print("="*60)
    
    # Load data
    df = load_data()
    
    # Analyze skewness
    skewness_df = analyze_feature_skewness(df)
    
    # Identify outliers
    outlier_df = identify_outlier_providers(df)
    
    # Create plots
    create_distribution_plots(df, skewness_df)
    
    # Summary
    generate_summary_report(df, skewness_df, outlier_df)
    
    print("\n" + "="*60)
    print("✅ ANALYSIS COMPLETE!")
    print("="*60)
    print(f"\n📁 All results saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
