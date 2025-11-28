import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json

def generate_report(data_path, output_dir):
    """Generates a data quality report and visualizations."""
    
    print(f"Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: File not found at {data_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    figures_dir = os.path.join(output_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    report_content = "# Data Quality and Distribution Report\n\n"
    
    # 1. Dataset Overview
    report_content += "## 1. Dataset Overview\n"
    report_content += f"- **Total Records:** {len(df)}\n"
    report_content += f"- **Total Features:** {len(df.columns)}\n\n"

    # 2. Specialty Counts
    report_content += "## 2. Provider Specialties\n"
    specialty_counts = df['specialty'].value_counts()
    report_content += f"- **Total Unique Specialties:** {len(specialty_counts)}\n"
    report_content += "### Top 20 Specialties\n"
    report_content += "| Specialty | Count | Percentage |\n"
    report_content += "|---|---|---|\n"
    for specialty, count in specialty_counts.head(20).items():
        percentage = (count / len(df)) * 100
        report_content += f"| {specialty} | {count} | {percentage:.2f}% |\n"
    report_content += "\n"

    # Graph: Top 20 Specialties
    plt.figure(figsize=(12, 8))
    sns.barplot(y=specialty_counts.head(20).index, x=specialty_counts.head(20).values, palette="viridis")
    plt.title("Top 20 Provider Specialties")
    plt.xlabel("Count")
    plt.ylabel("Specialty")
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "top_specialties.png"))
    plt.close()
    report_content += "![Top Specialties](figures/top_specialties.png)\n\n"

    # 3. Numerical Feature Statistics
    report_content += "## 3. Numerical Feature Statistics\n"
    numerical_cols = ['total_service_cost', 'total_services', 'total_benes_phys', 
                      'total_drug_cost', 'total_scripts', 'total_benes_presc',
                      'cost_per_service', 'services_per_bene', 'risk_score']
    
    # Filter for existing columns
    existing_num_cols = [col for col in numerical_cols if col in df.columns]
    
    if existing_num_cols:
        stats = df[existing_num_cols].describe().T[['mean', '50%', 'std', 'min', 'max']]
        stats.columns = ['Mean', 'Median', 'Std Dev', 'Min', 'Max']
        report_content += stats.to_markdown()
        report_content += "\n\n"

        # Graphs: Distributions
        report_content += "### Feature Distributions (Log Scale for Skewed Data)\n"
        for col in existing_num_cols:
            plt.figure(figsize=(10, 6))
            # Use log scale for highly skewed cost/count data
            if 'cost' in col or 'total' in col or 'per' in col:
                sns.histplot(df[col], bins=50, kde=True, log_scale=True)
                plt.title(f"Distribution of {col} (Log Scale)")
            else:
                sns.histplot(df[col], bins=50, kde=True)
                plt.title(f"Distribution of {col}")
            
            filename = f"dist_{col}.png"
            plt.savefig(os.path.join(figures_dir, filename))
            plt.close()
            report_content += f"#### {col}\n![Distribution of {col}](figures/{filename})\n\n"

    # 4. Risk Score Analysis (if available)
    if 'risk_score' in df.columns:
        report_content += "## 4. Risk Score Analysis\n"
        high_risk = df[df['risk_score'] > 0.75]
        medium_risk = df[(df['risk_score'] > 0.5) & (df['risk_score'] <= 0.75)]
        low_risk = df[df['risk_score'] <= 0.5]
        
        report_content += f"- **High Risk (> 0.75):** {len(high_risk)} ({len(high_risk)/len(df)*100:.2f}%)\n"
        report_content += f"- **Medium Risk (0.5 - 0.75):** {len(medium_risk)} ({len(medium_risk)/len(df)*100:.2f}%)\n"
        report_content += f"- **Low Risk (< 0.5):** {len(low_risk)} ({len(low_risk)/len(df)*100:.2f}%)\n\n"
        
        # Graph: Risk Score Distribution
        plt.figure(figsize=(10, 6))
        sns.histplot(df['risk_score'], bins=50, kde=True, color='red')
        plt.title("Risk Score Distribution")
        plt.xlabel("Risk Score")
        plt.savefig(os.path.join(figures_dir, "risk_score_dist.png"))
        plt.close()
        report_content += "![Risk Score Distribution](figures/risk_score_dist.png)\n\n"

    # Save Report
    report_path = os.path.join(output_dir, "data_quality_report.md")
    with open(report_path, "w") as f:
        f.write(report_content)
    
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    # Use absolute paths based on project structure
    base_dir = os.getcwd()
    data_file = os.path.join(base_dir, "data/provider_features.csv")
    output_folder = os.path.join(base_dir, "reports")
    
    generate_report(data_file, output_folder)
