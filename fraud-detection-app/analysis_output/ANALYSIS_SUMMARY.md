# Data Skewness Analysis Results

## 📊 Summary

**Dataset**: 1,767,599 provider records with 21 features

### Key Findings

#### 🚨 Highly Skewed Features (16 total)

The following features have extreme skewness (|skewness| > 2.0):

| Feature | Skewness | Issue |
|---------|----------|-------|
| `provider_archetype_4` | **1329.51** | Extremely rare cluster (Extreme Outlier) |
| `services_per_bene` | **676.84** | Very few high-volume providers |
| `pagerank_centrality` | **466.02** | Network centrality concentrated in few providers |
| `total_benes_phys` | **384.34** | Most providers see few patients |
| `total_benes` | **382.65** | Patient volume highly concentrated |
| `total_benes_presc` | **330.54** | Prescription patient volume skewed |
| `total_services` | **250.04** | Service volume highly concentrated |
| `provider_archetype_1` | **218.56** | Rare cluster (High-Value Specialist) |
| `cost_per_service` | **170.40** | Most providers low-cost, few very expensive |
| `provider_archetype_2` | **76.87** | Uncommon cluster (Tier 2 High Cost) |

#### ⚠️  Outlier Providers Detected

- **59 unique providers** identified as extreme outliers
- These providers have Z-scores > 3.5 on key metrics
- Represent **0.003%** of total providers
- Should be removed before model retraining

### Outlier Breakdown by Metric

| Metric | Outlier Count |
|--------|---------------|
| `total_claim_cost` | 18,911 instances |
| `total_service_cost` | 11,733 instances |
| `cost_per_service` | 7,163 instances |
| `total_services` | 2,476 instances |
| `total_benes` | 430 instances |
| `total_benes_phys` | 398 instances |
| `services_per_bene` | 33 instances |

## 📋 Recommendations

### 1. Remove Outlier Providers ✅
- **Action**: Remove the 59 providers listed in `outlier_providers_to_remove.csv`
- **Impact**: Minimal data loss (0.003% of providers)
- **Benefit**: Cleaner model training, better generalization

### 2. Apply Feature Transformations 📊
For highly skewed features, apply:
- **Log transformation** for count/volume features (total_services, total_benes, etc.)
- **Yeo-Johnson transformation** for features with zeros/negatives
- **Quantile transformation** for extreme skewness (provider archetypes)

### 3. Feature Engineering 🔧
Consider creating:
- **Binned versions** of highly skewed features
- **Rank-based features** instead of raw values
- **Ratio features** that are more normally distributed

### 4. Model Considerations 💡
- Use **tree-based models** (XGBoost, Random Forest) which handle skewness well
- Apply **robust scaling** instead of standard scaling
- Consider **stratified sampling** to ensure rare archetypes are represented

## 📁 Generated Files

All analysis results are in `analysis_output/`:

1. **feature_skewness.csv** - Complete skewness metrics for all features
2. **feature_skewness_plot.png** - Visual chart of top 20 skewed features
3. **skewed_distributions.png** - Distribution histograms for highly skewed features
4. **outlier_providers_detailed.csv** - Detailed outlier analysis with Z-scores
5. **outlier_providers_to_remove.csv** - **List of 59 provider IDs to remove**

## 🔄 Next Steps

### Step 1: Clean the Dataset
```bash
# Create cleaned dataset (removes outliers)
python clean_provider_data.py
```

### Step 2: Retrain the Model
```bash
# Retrain with cleaned data
python src/training/train.py --use-cleaned-data
```

### Step 3: Compare Performance
- Compare model metrics before/after cleaning
- Evaluate if base risk score changes
- Check if fraud detection improves

## 💡 Why This Matters

### Current Issues
1. **Extreme skewness** (avg 261.27) makes models biased toward outliers
2. **59 outlier providers** can dominate model learning
3. **Rare archetypes** (provider_archetype_4) barely represented

### Expected Improvements
1. ✅ More balanced feature distributions
2. ✅ Better model generalization
3. ✅ More realistic risk scores
4. ✅ Reduced false positives from outlier influence

## 📊 Skewness Interpretation

| Skewness Range | Interpretation | Action |
|----------------|----------------|--------|
| -0.5 to +0.5 | Fairly symmetric | No action needed |
| ±0.5 to ±1.0 | Moderately skewed | Consider transformation |
| ±1.0 to ±2.0 | Highly skewed | Transformation recommended |
| > ±2.0 | **Extremely skewed** | **Transformation required** |

**Your dataset**: 16 features with skewness > 2.0 (94% of numerical features!)

---

**Generated**: 2025-11-24
**Dataset**: provider_features.csv (1,767,599 providers)
