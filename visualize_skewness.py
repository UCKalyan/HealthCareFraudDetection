"""
Advanced Skewness Visualization
Creates KDE plots, box plots, and detailed visualizations to understand data skewness
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)

# Configuration
DATA_DIR = Path("data")
ANALYSIS_DIR = Path("analysis_output")
VIZ_DIR = ANALYSIS_DIR / "visualizations"
VIZ_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Load the provider features dataset"""
    print("📂 Loading dataset...")
    df = pd.read_csv(DATA_DIR / "provider_features.csv")
    print(f"✅ Loaded {len(df):,} providers")
    return df

def load_skewness_data():
    """Load skewness analysis results"""
    skewness_df = pd.read_csv(ANALYSIS_DIR / "feature_skewness.csv")
    return skewness_df

def create_kde_comparison_plots(df, skewness_df, top_n=9):
    """Create KDE plots comparing original vs normal distribution"""
    print("\n📊 Creating KDE comparison plots...")
    
    # Get top skewed features
    top_skewed = skewness_df.nlargest(top_n, 'Skewness', keep='all')
    
    fig, axes = plt.subplots(3, 3, figsize=(18, 14))
    axes = axes.flatten()
    
    for idx, (_, row) in enumerate(top_skewed.iterrows()):
        if idx >= 9:
            break
        
        feature = row['Feature']
        ax = axes[idx]
        
        # Get data
        data = df[feature].dropna()
        
        # Plot KDE of actual data
        try:
            data.plot(kind='kde', ax=ax, color='red', linewidth=2, label='Actual Data')
            
            # Plot theoretical normal distribution
            mean, std = data.mean(), data.std()
            x = np.linspace(data.min(), data.max(), 100)
            normal_dist = stats.norm.pdf(x, mean, std)
            ax.plot(x, normal_dist, 'b--', linewidth=2, label='Normal Distribution')
            
            ax.set_title(f"{feature}\nSkewness: {row['Skewness']:.2f}", 
                        fontsize=11, fontweight='bold')
            ax.set_xlabel('Value')
            ax.set_ylabel('Density')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:30]}', 
                   ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    plt.savefig(VIZ_DIR / 'kde_comparison_plots.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {VIZ_DIR / 'kde_comparison_plots.png'}")
    plt.close()

def create_before_after_transformation(df, feature_name):
    """Show before/after transformation for a single feature"""
    print(f"\n🔄 Creating before/after transformation for {feature_name}...")
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    
    # Original data
    original = df[feature_name].dropna()
    
    # Apply transformations
    log_transformed = np.log1p(original)
    
    from sklearn.preprocessing import PowerTransformer
    pt = PowerTransformer(method='yeo-johnson')
    power_transformed = pt.fit_transform(original.values.reshape(-1, 1)).flatten()
    
    # Row 1: Histograms
    axes[0, 0].hist(original, bins=50, edgecolor='black', alpha=0.7, color='red')
    axes[0, 0].set_title(f'Original\nSkewness: {stats.skew(original):.2f}', fontweight='bold')
    axes[0, 0].set_ylabel('Frequency')
    
    axes[0, 1].hist(log_transformed, bins=50, edgecolor='black', alpha=0.7, color='orange')
    axes[0, 1].set_title(f'Log Transformed\nSkewness: {stats.skew(log_transformed):.2f}', fontweight='bold')
    
    axes[0, 2].hist(power_transformed, bins=50, edgecolor='black', alpha=0.7, color='green')
    axes[0, 2].set_title(f'Power Transformed\nSkewness: {stats.skew(power_transformed):.2f}', fontweight='bold')
    
    # Row 2: KDE plots
    original.plot(kind='kde', ax=axes[1, 0], color='red', linewidth=2)
    axes[1, 0].set_title('Original Distribution (KDE)', fontweight='bold')
    axes[1, 0].set_xlabel('Value')
    axes[1, 0].set_ylabel('Density')
    axes[1, 0].grid(True, alpha=0.3)
    
    pd.Series(log_transformed).plot(kind='kde', ax=axes[1, 1], color='orange', linewidth=2)
    axes[1, 1].set_title('Log Transformed (KDE)', fontweight='bold')
    axes[1, 1].set_xlabel('Value')
    axes[1, 1].grid(True, alpha=0.3)
    
    pd.Series(power_transformed).plot(kind='kde', ax=axes[1, 2], color='green', linewidth=2)
    axes[1, 2].set_title('Power Transformed (KDE)', fontweight='bold')
    axes[1, 2].set_xlabel('Value')
    axes[1, 2].grid(True, alpha=0.3)
    
    plt.suptitle(f'Transformation Impact: {feature_name}', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    safe_name = feature_name.replace('/', '_').replace(' ', '_')
    plt.savefig(VIZ_DIR / f'transformation_{safe_name}.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {VIZ_DIR / f'transformation_{safe_name}.png'}")
    plt.close()

def create_box_violin_plots(df, skewness_df, top_n=6):
    """Create box and violin plots to show outliers"""
    print("\n📦 Creating box and violin plots...")
    
    top_skewed = skewness_df.nlargest(top_n, 'Skewness', keep='all')
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for idx, (_, row) in enumerate(top_skewed.iterrows()):
        if idx >= 6:
            break
        
        feature = row['Feature']
        ax = axes[idx]
        
        data = df[feature].dropna()
        
        # Create violin plot with box plot overlay
        parts = ax.violinplot([data], positions=[0], showmeans=True, showmedians=True)
        
        # Color the violin
        for pc in parts['bodies']:
            pc.set_facecolor('lightblue')
            pc.set_alpha(0.7)
        
        # Add box plot
        bp = ax.boxplot([data], positions=[0], widths=0.3, 
                        patch_artist=True, showfliers=True)
        
        for patch in bp['boxes']:
            patch.set_facecolor('orange')
            patch.set_alpha(0.5)
        
        ax.set_title(f"{feature}\nSkewness: {row['Skewness']:.2f}", 
                    fontsize=11, fontweight='bold')
        ax.set_ylabel('Value')
        ax.set_xticks([])
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add statistics text
        stats_text = f"Mean: {data.mean():.2e}\nMedian: {data.median():.2e}\nStd: {data.std():.2e}"
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               fontsize=8, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.suptitle('Box & Violin Plots: Highly Skewed Features', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(VIZ_DIR / 'box_violin_plots.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {VIZ_DIR / 'box_violin_plots.png'}")
    plt.close()

def create_qq_plots(df, skewness_df, top_n=6):
    """Create Q-Q plots to show deviation from normality"""
    print("\n📈 Creating Q-Q plots...")
    
    top_skewed = skewness_df.nlargest(top_n, 'Skewness', keep='all')
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for idx, (_, row) in enumerate(top_skewed.iterrows()):
        if idx >= 6:
            break
        
        feature = row['Feature']
        ax = axes[idx]
        
        data = df[feature].dropna()
        
        # Create Q-Q plot
        stats.probplot(data, dist="norm", plot=ax)
        
        ax.set_title(f"{feature}\nSkewness: {row['Skewness']:.2f}", 
                    fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('Q-Q Plots: Deviation from Normal Distribution', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(VIZ_DIR / 'qq_plots.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {VIZ_DIR / 'qq_plots.png'}")
    plt.close()

def create_log_scale_comparison(df, skewness_df, top_n=6):
    """Create linear vs log scale comparison"""
    print("\n📊 Creating linear vs log scale comparison...")
    
    top_skewed = skewness_df.nlargest(top_n, 'Skewness', keep='all')
    
    fig, axes = plt.subplots(3, 4, figsize=(20, 12))
    
    for idx, (_, row) in enumerate(top_skewed.iterrows()):
        if idx >= 6:
            break
        
        feature = row['Feature']
        data = df[feature].dropna()
        
        # Linear scale histogram
        ax1 = axes[idx, 0]
        ax1.hist(data, bins=50, edgecolor='black', alpha=0.7, color='red')
        ax1.set_title(f'{feature}\n(Linear Scale)', fontsize=10)
        ax1.set_ylabel('Frequency')
        
        # Log scale histogram
        ax2 = axes[idx, 1]
        ax2.hist(data, bins=50, edgecolor='black', alpha=0.7, color='blue')
        ax2.set_yscale('log')
        ax2.set_title(f'{feature}\n(Log Y-Scale)', fontsize=10)
        
        # Linear KDE
        ax3 = axes[idx, 2]
        data.plot(kind='kde', ax=ax3, color='red', linewidth=2)
        ax3.set_title(f'{feature}\n(KDE)', fontsize=10)
        ax3.grid(True, alpha=0.3)
        
        # Cumulative distribution
        ax4 = axes[idx, 3]
        sorted_data = np.sort(data)
        cumulative = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        ax4.plot(sorted_data, cumulative, linewidth=2, color='green')
        ax4.set_title(f'{feature}\n(CDF)', fontsize=10)
        ax4.set_ylabel('Cumulative Probability')
        ax4.grid(True, alpha=0.3)
    
    plt.suptitle('Multi-View Analysis: Highly Skewed Features', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(VIZ_DIR / 'multi_view_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {VIZ_DIR / 'multi_view_analysis.png'}")
    plt.close()

def create_skewness_impact_summary(skewness_df):
    """Create comprehensive skewness impact visualization"""
    print("\n📊 Creating skewness impact summary...")
    
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Skewness distribution
    ax1 = fig.add_subplot(gs[0, :2])
    skewness_values = skewness_df['Skewness'].abs()
    ax1.hist(skewness_values, bins=30, edgecolor='black', alpha=0.7, color='coral')
    ax1.axvline(x=2.0, color='red', linestyle='--', linewidth=2, label='Threshold (2.0)')
    ax1.set_xlabel('Absolute Skewness', fontsize=12)
    ax1.set_ylabel('Number of Features', fontsize=12)
    ax1.set_title('Distribution of Feature Skewness', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Skewness categories pie chart
    ax2 = fig.add_subplot(gs[0, 2])
    categories = pd.cut(skewness_values, bins=[0, 0.5, 1.0, 2.0, float('inf')],
                       labels=['Low\n(0-0.5)', 'Moderate\n(0.5-1.0)', 
                              'High\n(1.0-2.0)', 'Extreme\n(>2.0)'])
    category_counts = categories.value_counts()
    colors = ['green', 'yellow', 'orange', 'red']
    ax2.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%',
           colors=colors, startangle=90)
    ax2.set_title('Skewness Categories', fontsize=12, fontweight='bold')
    
    # 3. Top 10 skewed features bar chart
    ax3 = fig.add_subplot(gs[1, :])
    top_10 = skewness_df.nlargest(10, 'Skewness', keep='all')
    colors_bar = ['red' if abs(s) > 100 else 'orange' if abs(s) > 10 else 'yellow' 
                  for s in top_10['Skewness']]
    ax3.barh(top_10['Feature'], top_10['Skewness'], color=colors_bar, edgecolor='black')
    ax3.set_xlabel('Skewness', fontsize=12)
    ax3.set_title('Top 10 Most Skewed Features', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # 4. Skewness vs Kurtosis scatter
    ax4 = fig.add_subplot(gs[2, 0])
    scatter = ax4.scatter(skewness_df['Skewness'], skewness_df['Kurtosis'], 
                         c=skewness_values, cmap='YlOrRd', s=100, alpha=0.6, edgecolors='black')
    ax4.set_xlabel('Skewness', fontsize=11)
    ax4.set_ylabel('Kurtosis', fontsize=11)
    ax4.set_title('Skewness vs Kurtosis', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax4, label='Abs Skewness')
    
    # 5. Mean vs Median ratio
    ax5 = fig.add_subplot(gs[2, 1])
    mean_median_ratio = skewness_df['Mean'] / (skewness_df['Median'] + 1e-10)
    ax5.scatter(skewness_df['Skewness'], mean_median_ratio, 
               c=skewness_values, cmap='YlOrRd', s=100, alpha=0.6, edgecolors='black')
    ax5.axhline(y=1, color='blue', linestyle='--', label='Mean = Median')
    ax5.set_xlabel('Skewness', fontsize=11)
    ax5.set_ylabel('Mean / Median Ratio', fontsize=11)
    ax5.set_title('Mean-Median Ratio vs Skewness', fontsize=12, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    ax5.set_yscale('log')
    
    # 6. Statistics summary table
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.axis('off')
    
    summary_stats = [
        ['Metric', 'Value'],
        ['Total Features', f"{len(skewness_df)}"],
        ['Highly Skewed (>2)', f"{(skewness_values > 2).sum()}"],
        ['Max Skewness', f"{skewness_values.max():.2f}"],
        ['Avg Skewness', f"{skewness_values.mean():.2f}"],
        ['Median Skewness', f"{skewness_values.median():.2f}"],
    ]
    
    table = ax6.table(cellText=summary_stats, cellLoc='left', loc='center',
                     colWidths=[0.6, 0.4])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Style header row
    for i in range(2):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax6.set_title('Summary Statistics', fontsize=12, fontweight='bold', pad=20)
    
    plt.suptitle('Comprehensive Skewness Impact Analysis', 
                fontsize=18, fontweight='bold', y=0.98)
    
    plt.savefig(VIZ_DIR / 'skewness_impact_summary.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {VIZ_DIR / 'skewness_impact_summary.png'}")
    plt.close()

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("📊 ADVANCED SKEWNESS VISUALIZATION")
    print("="*60)
    
    # Load data
    df = load_data()
    skewness_df = load_skewness_data()
    
    # Create visualizations
    create_kde_comparison_plots(df, skewness_df)
    create_box_violin_plots(df, skewness_df)
    create_qq_plots(df, skewness_df)
    create_log_scale_comparison(df, skewness_df)
    create_skewness_impact_summary(skewness_df)
    
    # Create before/after for top 3 most skewed
    top_3 = skewness_df.nlargest(3, 'Skewness', keep='all')
    for _, row in top_3.iterrows():
        create_before_after_transformation(df, row['Feature'])
    
    print("\n" + "="*60)
    print("✅ VISUALIZATION COMPLETE!")
    print("="*60)
    print(f"\n📁 All visualizations saved to: {VIZ_DIR}/")
    print("\nGenerated files:")
    print("  • kde_comparison_plots.png - KDE vs Normal distribution")
    print("  • box_violin_plots.png - Box & violin plots showing outliers")
    print("  • qq_plots.png - Q-Q plots for normality testing")
    print("  • multi_view_analysis.png - Multiple perspectives on skewness")
    print("  • skewness_impact_summary.png - Comprehensive summary dashboard")
    print("  • transformation_*.png - Before/after transformation for top features")

if __name__ == "__main__":
    main()
