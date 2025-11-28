# Data Processing Pipeline

This document details the end-to-end data processing pipeline used in the FraudGuard system, from raw data ingestion to feature engineering and label generation.

## 1. Data Sources

The system ingests three primary datasets:

| Dataset | Source | Granularity | Description |
| :--- | :--- | :--- | :--- |
| **Medicare Part B** | CMS | Procedure-Level | Physician services, procedures, and billing details. Aggregated by NPI, HCPCS Code, and Place of Service. |
| **Medicare Part D** | CMS | Provider-Level | Prescription drug claims. Aggregated by NPI. |
| **LEIE** | OIG | Provider-Level | List of Excluded Individuals/Entities. Used as **Ground Truth** for fraud labels. |

## 2. Data Loading & Cleaning (`src/data_processing/loader.py`)

- **File Discovery:** The loader scans the `data/raw_data` directory for files matching configured keywords (`PHY_R25`, `DPR_RY25`, `LEIE`).
- **NPI Mapping:**
    - Part B/D: Uses the configured column name (e.g., `Rndrng_NPI`, `PRSCRBR_NPI`).
    - LEIE: Standardizes `NPI` column to `provider_id`.
- **Encoding Handling:** Automatically retries with `latin1` encoding if `utf-8` fails.

## 3. Data Merging Strategy (`src/data_processing/preprocessor.py`)

We use a robust merging strategy to handle the disjoint nature of Part B (Medical) and Part D (Rx) providers.

### 3.1 Outer Join
- **Logic:** `pd.merge(part_b, part_d, on='provider_id', how='outer')`
- **Reason:** We must retain **all** providers.
    - Some doctors only perform procedures (Part B only).
    - Some only prescribe (Part D only).
    - Most do both (Intersection).

### 3.2 Coalescing Logic (The "0" Problem)
A naive `fillna(0)` would incorrectly label a Part-D-only provider's specialty as "0". We use **Coalescing**:
- **Specialty:** `Part B Specialty` -> if missing, use `Part D Specialty` -> if missing, use "Unknown".
- **Name:** Similar logic for First Name and Organization Name.

### 3.3 Missing Data Flags
To help the model distinguish between "True Zero" (did not prescribe) and "Missing Data" (not in dataset), we add binary flags:
- `has_part_b`: 1 if provider exists in Part B, else 0.
- `has_part_d`: 1 if provider exists in Part D, else 0.

## 4. Feature Engineering

We generate a rich set of features to capture provider behavior.

### 4.1 Aggregated Metrics
- `total_claim_cost`: Sum of Part B Service Cost + Part D Drug Cost.
- `total_benes`: Sum of unique beneficiaries.
- `total_services`: Total procedures + prescriptions.

### 4.2 Derived Ratios
- `cost_per_service`: `total_claim_cost / total_services`
- `services_per_bene`: `total_services / total_benes` (Utilization Rate)

### 4.3 Graph Features (NetworkX)
- **PageRank Centrality:** Measures a provider's influence within their specialty network.
- **Graph Construction:** Nodes = Providers, Edges = Shared Specialty.

### 4.4 Behavioral Archetypes (K-Means)
- We cluster providers into `k=5` behavioral archetypes based on their cost and utilization patterns.
- **Features:** `provider_archetype_0` ... `provider_archetype_4` (One-Hot Encoded).

## 5. Label Generation (Configurable)

The system supports two labeling modes, controlled by `config.yaml`:

### 5.1 Supervised Learning (Default: `supervised`)
- **Source:** LEIE Dataset.
- **Logic:** `y = 1` if `provider_id` is in LEIE, else `0`.
- **Pros:** Learns real-world fraud patterns.
- **Cons:** Extreme class imbalance (~0.02% fraud). Handled via **SMOTE** and **Focal Loss**.

### 5.2 Unsupervised Learning (`unsupervised`)
- **Source:** Statistical Outliers.
- **Logic:** `y = 1` if `Z-Score(total_claim_cost) > 3.0` within their specialty.
- **Pros:** Good for detecting anomalies without labeled data.
- **Cons:** May flag high-volume legitimate doctors as fraud.

## 6. Class Imbalance Handling

For Supervised Learning, we employ a two-pronged strategy:
1.  **SMOTE (Synthetic Minority Over-sampling Technique):** Resamples the minority class (Fraud) in the training set to achieve a 50/50 balance.
2.  **Focal Loss:** A specialized loss function that down-weights easy examples and focuses training on hard-to-classify fraud cases.
