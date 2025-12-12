# FraudGuard - ML Pipeline, CI/CD & Algorithm Diagrams

## Table of Contents
1. [ML Training Pipeline](#1-ml-training-pipeline)
2. [ML Inference Pipeline](#2-ml-inference-pipeline)
3. [Model Architecture](#3-model-architecture)
4. [Algorithm Diagrams](#4-algorithm-diagrams)
5. [CI/CD Pipeline](#5-cicd-pipeline)
6. [Deployment Workflows](#6-deployment-workflows)

---

## 1. ML Training Pipeline

### 1.1 Complete Training Workflow

```mermaid
flowchart TB
    START([Start Training]) --> CHECK_FEATURE{Feature Store<br/>Exists?}
    
    CHECK_FEATURE -->|Yes| LOAD_FEATURES[Load Pre-computed Features<br/>from CSV]
    CHECK_FEATURE -->|No| LOAD_RAW[Load Raw Data<br/>Physician, Prescriber, LEIE]
    
    LOAD_RAW --> MERGE[Merge Datasets on NPI]
    MERGE --> ENGINEER[Feature Engineering Pipeline]
    
    subgraph "Feature Engineering"
        ENGINEER --> BASE_FEAT[Calculate Base Features<br/>6 metrics]
        BASE_FEAT --> SPECIALTY_STATS[Calculate Specialty Statistics<br/>Group by specialty]
        SPECIALTY_STATS --> ZSCORE[Calculate Z-Scores<br/>Normalize by specialty]
        ZSCORE --> KMEANS_FIT[Fit K-Means Clustering<br/>n_clusters=5]
        KMEANS_FIT --> BUILD_GRAPH[Build Similarity Graph<br/>Cosine similarity]
        BUILD_GRAPH --> PAGERANK[Calculate PageRank<br/>Network centrality]
        PAGERANK --> SAVE_FEATURES[Save to Feature Store]
    end
    
    SAVE_FEATURES --> SPLIT
    LOAD_FEATURES --> SPLIT[Train-Val-Test Split<br/>60-20-20]
    
    SPLIT --> LABEL{Labeling<br/>Method?}
    LABEL -->|Supervised| LEIE_LABEL[LEIE-based Labels<br/>Match with exclusion list]
    LABEL -->|Unsupervised| ZSCORE_LABEL[Z-Score based Labels<br/>combined_z > 3.0]
    
    LEIE_LABEL --> SMOTE
    ZSCORE_LABEL --> SMOTE[Apply SMOTE<br/>Balance classes]
    
    SMOTE --> CLASS_WEIGHTS[Calculate Class Weights<br/>Handle remaining imbalance]
    
    CLASS_WEIGHTS --> BUILD_MODEL[Build Deep Learning Model<br/>Input: 11 features<br/>Output: Fraud probability]
    
    subgraph "Model Architecture"
        BUILD_MODEL --> LAYER1[Dense Layer 64<br/>PReLU, BatchNorm, Dropout]
        LAYER1 --> LAYER2[Dense Layer 32<br/>PReLU, BatchNorm, Dropout]
        LAYER2 --> OUTPUT[Dense Layer 1<br/>Sigmoid activation]
    end
    
    OUTPUT --> COMPILE[Compile Model<br/>Loss: Focal Crossentropy<br/>Optimizer: Adam<br/>Metrics: AUC]
    
    COMPILE --> CALLBACKS[Setup Callbacks<br/>EarlyStopping, ReduceLR]
    
    CALLBACKS --> TRAIN_LOOP[Training Loop<br/>Epochs: 50<br/>Batch: 2048]
    
    TRAIN_LOOP --> EPOCH{Epoch<br/>Complete?}
    EPOCH -->|Continue| VAL[Validation]
    VAL --> CHECK_EARLY{Early<br/>Stopping?}
    CHECK_EARLY -->|No| TRAIN_LOOP
    CHECK_EARLY -->|Yes| SAVE_MODEL
    EPOCH -->|Max epochs| SAVE_MODEL[Save Model<br/>saved_models/fraud_model.h5]
    
    SAVE_MODEL --> EVALUATE[Evaluate on Test Set<br/>Calculate metrics]
    
    subgraph "Evaluation"
        EVALUATE --> METRICS[Calculate Metrics<br/>Accuracy, Precision, Recall, F1, AUC]
        METRICS --> CONFUSION[Generate Confusion Matrix]
        CONFUSION --> PR_CURVE[Plot Precision-Recall Curve]
    end
    
    PR_CURVE --> SHAP_GEN[Generate SHAP Explanations<br/>Sample 100 test instances]
    
    SHAP_GEN --> SHAP_PLOT[Create SHAP Summary Plot<br/>Feature importance visualization]
    
    SHAP_PLOT --> LLM_REPORT[Generate LLM Report<br/>Narrative analysis]
    
    LLM_REPORT --> END([Training Complete])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style BUILD_MODEL fill:#9B59B6,stroke:#8E44AD,color:#fff
    style SMOTE fill:#F39C12,stroke:#E67E22,color:#fff
    style SHAP_GEN fill:#3498DB,stroke:#2980B9,color:#fff
```

### 1.2 Feature Engineering Detail

```mermaid
graph TB
    subgraph "Input Data"
        PHYS["Physician Data<br/>Tot_Srvcs, Tot_Benes<br/>Avg_Sbmtd_Chrg"]
        PRESC["Prescriber Data<br/>Tot_Clms, Tot_Benes<br/>Tot_Drug_Cst"]
    end
    
    subgraph "Stage 1: Base Features"
        direction LR
        F1["cost_per_service<br/>= Avg_Sbmtd_Chrg"]
        F2["services_per_bene<br/>= Tot_Srvcs / Tot_Benes"]
        F3["cost_per_bene_phys<br/>= Total / Tot_Benes"]
        F4["scripts_per_bene<br/>= Tot_Clms / Tot_Benes"]
        F5["drug_cost_per_script<br/>= Tot_Drug_Cst / Tot_Clms"]
        F6["cost_per_bene_presc<br/>= Tot_Drug_Cst / Tot_Benes"]
    end
    
    subgraph "Stage 2: Specialty Normalization"
        STATS["Calculate per specialty:<br/>μ (mean)<br/>σ (std dev)"]
        NORM1["cps_z = (cps - μ_cps) / σ_cps"]
        NORM2["spb_z = (spb - μ_spb) / σ_spb"]
        NORM3["cpb_phys_z = (cpb_p - μ) / σ"]
        NORM4["dcp_z = (dcp - μ_dcp) / σ_dcp"]
        NORM5["cpb_presc_z = (cpb_pr - μ) / σ"]
    end
    
    subgraph "Stage 3: Bounded Transform"
        TANH1["cps_z_tanh = tanh(cps_z)"]
        TANH2["spb_z_tanh = tanh(spb_z)"]
        TANH3["cpb_phys_z_tanh = tanh(cpb_phys_z)"]
        TANH4["dcp_z_tanh = tanh(dcp_z)"]
        TANH5["cpb_presc_z_tanh = tanh(cpb_presc_z)"]
    end
    
    subgraph "Stage 4: Clustering"
        CLUSTER_INPUT["Features:<br/>cost_per_service<br/>services_per_bene"]
        KMEANS["K-Means<br/>n_clusters = 5"]
        ONEHOT["One-Hot Encode<br/>5 binary features"]
    end
    
    subgraph "Stage 5: Graph Analysis"
        SIM_MATRIX["Cosine Similarity Matrix<br/>Based on cps, spb"]
        THRESHOLD["Apply Threshold<br/>similarity > 0.95"]
        TOP_K["Select Top-K Peers<br/>k = 5"]
        GRAPH_BUILD["Build Network Graph<br/>Directed edges"]
        PAGERANK_CALC["PageRank Algorithm<br/>Influence score"]
    end
    
    subgraph "Output: Feature Vector"
        FINAL["[cps_z_tanh,<br/>spb_z_tanh,<br/>cpb_phys_z_tanh,<br/>dcp_z_tanh,<br/>cpb_presc_z_tanh,<br/>cluster_0,<br/>cluster_1,<br/>cluster_2,<br/>cluster_3,<br/>cluster_4,<br/>pagerank_centrality]<br/><br/>Shape: (11,)"]
    end
    
    PHYS --> F1
    PHYS --> F2
    PHYS --> F3
    PRESC --> F4
    PRESC --> F5
    PRESC --> F6
    
    F1 --> STATS
    F2 --> STATS
    F3 --> STATS
    F4 --> STATS
    F5 --> STATS
    F6 --> STATS
    
    STATS --> NORM1
    STATS --> NORM2
    STATS --> NORM3
    STATS --> NORM4
    STATS --> NORM5
    
    NORM1 --> TANH1
    NORM2 --> TANH2
    NORM3 --> TANH3
    NORM4 --> TANH4
    NORM5 --> TANH5
    
    F1 --> CLUSTER_INPUT
    F2 --> CLUSTER_INPUT
    CLUSTER_INPUT --> KMEANS
    KMEANS --> ONEHOT
    
    F1 --> SIM_MATRIX
    F2 --> SIM_MATRIX
    SIM_MATRIX --> THRESHOLD
    THRESHOLD --> TOP_K
    TOP_K --> GRAPH_BUILD
    GRAPH_BUILD --> PAGERANK_CALC
    
    TANH1 --> FINAL
    TANH2 --> FINAL
    TANH3 --> FINAL
    TANH4 --> FINAL
    TANH5 --> FINAL
    ONEHOT --> FINAL
    PAGERANK_CALC --> FINAL
    
    style FINAL fill:#E74C3C,stroke:#C0392B,color:#fff
    style KMEANS fill:#9B59B6,stroke:#8E44AD,color:#fff
    style PAGERANK_CALC fill:#3498DB,stroke:#2980B9,color:#fff
```

---

## 2. ML Inference Pipeline

### 2.1 Real-time Inference Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant FeatureEngine
    participant FeatureStore
    participant Scaler
    participant StableModel
    participant FastModel
    participant SHAPExplainer
    participant Response
    
    User->>API: POST /api/provider_risk/{npi}
    
    API->>FeatureEngine: get_features(npi)
    
    FeatureEngine->>FeatureStore: Query pre-computed features
    
    alt Features exist in store
        FeatureStore-->>FeatureEngine: Return feature vector
    else Features not found
        FeatureEngine->>FeatureStore: Load raw provider data
        FeatureEngine->>FeatureEngine: Calculate features on-the-fly
        FeatureEngine-->>FeatureEngine: Feature vector ready
    end
    
    FeatureEngine-->>API: feature_vector (11-dim)
    
    API->>Scaler: transform(feature_vector)
    Scaler-->>API: scaled_features
    
    par Dual Prediction
        API->>StableModel: predict(scaled_features)
        StableModel-->>API: stable_score
        API->>FastModel: predict(scaled_features)
        FastModel-->>API: fast_score
    end
    
    API->>SHAPExplainer: shap_values(scaled_features)
    SHAPExplainer-->>API: shap_values
    
    API->>Response: Compare Scores (HOPE Logic)
    Response->>Response: Check for Early Warning (Fast >> Stable)
    Response->>Response: Format Response
    
    Response-->>User: {<br/>  stable_score: 0.85,<br/>  fast_score: 0.92,<br/>  alert: "Early Warning",<br/>  shap_values: [...]<br/>}
    
    Note over StableModel: Inference: ~50ms
    Note over FastModel: Inference: ~30ms
```

### 2.2 Batch Inference (Monitor Agent)

```mermaid
flowchart TD
    START([Monitor Agent Start]) --> LOAD_STATE[Load State<br/>current offset]
    
    LOAD_STATE --> QUERY[Query Database<br/>Get 100 providers<br/>OFFSET current_offset]
    
    QUERY --> BATCH_LOOP[For each provider in batch]
    
    BATCH_LOOP --> GET_FEATURES[Get Feature Vector<br/>From feature store]
    
    GET_FEATURES --> SCALE[Scale Features<br/>RobustScaler]
    
    SCALE --> BATCH_PREDICT[Batch Prediction<br/>model.predict(batch)]
    
    BATCH_PREDICT --> RISK_SCORES[Extract Risk Scores<br/>Array of 100 scores]
    
    RISK_SCORES --> CLASSIFY_BATCH[Classify Risk Levels<br/>HIGH/MEDIUM/LOW]
    
    CLASSIFY_BATCH --> UPDATE_DB[Update Database<br/>Batch UPDATE query]
    
    UPDATE_DB --> CALC_STATS[Calculate Aggregate Stats<br/>total, high_risk_count, avg_risk]
    
    CALC_STATS --> INC_OFFSET[Increment Offset<br/>offset += 100]
    
    INC_OFFSET --> SAVE_STATE[Save State<br/>monitor_state.json]
    
    SAVE_STATE --> SLEEP[Sleep 60 seconds]
    
    SLEEP --> QUERY
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style BATCH_PREDICT fill:#9B59B6,stroke:#8E44AD,color:#fff
    style UPDATE_DB fill:#3498DB,stroke:#2980B9,color:#fff
```

---

## 3. Model Architecture

### 3.1 Deep Neural Network Architecture

```mermaid
graph TB
    INPUT["Input Layer<br/>Shape: (None, 11)<br/><br/>Features:<br/>• cps_z_tanh<br/>• spb_z_tanh<br/>• cpb_phys_z_tanh<br/>• dcp_z_tanh<br/>• cpb_presc_z_tanh<br/>• cluster_0..4 (5 dims)<br/>• pagerank_centrality"]
    
    subgraph "Hidden Layer 1"
        DENSE1["Dense Layer<br/>Units: 64<br/>Regularization: L2(0.001)"]
        PRELU1["PReLU Activation<br/>Learnable α parameter"]
        BN1["Batch Normalization<br/>Normalize activations"]
        DROP1["Dropout(0.4)<br/>40% dropout rate"]
    end
    
    subgraph "Hidden Layer 2"
        DENSE2["Dense Layer<br/>Units: 32<br/>Regularization: L2(0.001)"]
        PRELU2["PReLU Activation<br/>Learnable α parameter"]
        BN2["Batch Normalization<br/>Normalize activations"]
        DROP2["Dropout(0.4)<br/>40% dropout rate"]
    end
    
    OUTPUT["Output Layer<br/>Units: 1<br/>Activation: Sigmoid<br/><br/>Output: Fraud Probability<br/>Range: [0.0, 1.0]"]
    
    LOSS["Loss Function<br/>Binary Focal Crossentropy<br/>γ = 2.0<br/><br/>Handles class imbalance"]
    
    OPTIMIZER["Optimizer<br/>Adam<br/>Learning Rate: 0.001<br/>β₁=0.9, β₂=0.999"]
    
    INPUT --> DENSE1
    DENSE1 --> PRELU1
    PRELU1 --> BN1
    BN1 --> DROP1
    
    DROP1 --> DENSE2
    DENSE2 --> PRELU2
    PRELU2 --> BN2
    BN2 --> DROP2
    
    DROP2 --> OUTPUT
    
    OUTPUT -.Loss Calculation.-> LOSS
    LOSS -.Backpropagation.-> OPTIMIZER
    OPTIMIZER -.Weight Update.-> DENSE1
    OPTIMIZER -.Weight Update.-> DENSE2
    
    style INPUT fill:#3498DB,stroke:#2980B9,color:#fff
    style OUTPUT fill:#E74C3C,stroke:#C0392B,color:#fff
    style LOSS fill:#F39C12,stroke:#E67E22,color:#fff
    style OPTIMIZER fill:#9B59B6,stroke:#8E44AD,color:#fff
```

### 3.3 Nested Learning Architecture (HOPE)

The system uses a **Hybrid Online & Periodic Estimation (HOPE)** architecture to balance stability with responsiveness.

```mermaid
graph TB
    INPUT[Input Features]
    
    subgraph "Dual-Speed System"
        SLOW[Stable Model<br/>Retrained Weekly<br/>High Accuracy]
        FAST[Fast Model<br/>Updated Daily<br/>High Sensitivity]
    end
    
    INPUT --> SLOW
    INPUT --> FAST
    
    SLOW -->|Score S| COMPARE{Compare}
    FAST -->|Score F| COMPARE
    
    COMPARE -->|S ≈ F| STABLE[Stable Risk Score]
    COMPARE -->|F >> S| ALERT[Early Warning Alert<br/>Emerging Fraud Pattern]
    
    style SLOW fill:#3498DB,color:#fff
    style FAST fill:#E74C3C,color:#fff
```

**Components**:
1.  **Stable Model**: The robust DNN described in 3.1. Retrained weekly on full verified dataset.
2.  **Fast Model**: Lightweight version updated daily with recent feedback and emerging patterns.
3.  **Comparison Logic**:
    - If scores are similar, confidence is high.
    - If Fast Model spikes while Stable is low, it triggers an "Early Warning".

---

### 3.2 Training Process Detail

```mermaid
flowchart LR
    subgraph "Input Data"
        X_TRAIN["X_train<br/>Shape: (N, 11)<br/>After SMOTE"]
        Y_TRAIN["y_train<br/>Shape: (N,)<br/>Binary labels"]
        X_VAL["X_val<br/>Shape: (M, 11)"]
        Y_VAL["y_val<br/>Shape: (M,)"]
    end
    
    subgraph "Forward Pass"
        FORWARD["Forward Propagation<br/>z = W·x + b<br/>a = activation(z)"]
        PREDICT["Prediction<br/>ŷ = σ(final_layer)"]
    end
    
    subgraph "Loss Calculation"
        FOCAL["Focal Loss<br/>FL(pt) = -α(1-pt)^γ log(pt)<br/>γ = 2.0"]
        CLASS_WEIGHT["Apply Class Weights<br/>Balance contribution"]
    end
    
    subgraph "Backward Pass"
        GRADIENT["Calculate Gradients<br/>∂L/∂W using backprop"]
        ADAM["Adam Optimizer<br/>m = β₁m + (1-β₁)g<br/>v = β₂v + (1-β₂)g²<br/>W = W - α·m/√v"]
    end
    
    subgraph "Validation"
        VAL_FORWARD["Validate on X_val"]
        VAL_LOSS["Calculate val_loss"]
        CALLBACKS["Check Callbacks<br/>EarlyStopping<br/>ReduceLR"]
    end
    
    X_TRAIN --> FORWARD
    FORWARD --> PREDICT
    PREDICT --> FOCAL
    Y_TRAIN --> FOCAL
    FOCAL --> CLASS_WEIGHT
    CLASS_WEIGHT --> GRADIENT
    GRADIENT --> ADAM
    ADAM -.Update Weights.-> FORWARD
    
    X_VAL --> VAL_FORWARD
    VAL_FORWARD --> VAL_LOSS
    Y_VAL --> VAL_LOSS
    VAL_LOSS --> CALLBACKS
    CALLBACKS -.Control Training.-> ADAM
    
    style FOCAL fill:#F39C12,stroke:#E67E22,color:#fff
    style ADAM fill:#9B59B6,stroke:#8E44AD,color:#fff
```

---

## 4. Algorithm Diagrams

> **Note**: For detailed mathematical explanations of all formulas used in these algorithms, see the [Mathematical Notation Guide](./TECHNICAL_DOCUMENTATION.md#mathematical-notation-guide) in the Technical Documentation.

### Algorithm Explanations

This section provides step-by-step explanations of the core algorithms used in the FraudGuard system.

#### 4.0.1 Risk Calculation Algorithm - Detailed Explanation

**Purpose**: Calculate a fraud risk score (0-1) for a healthcare provider based on billing patterns.

**Step-by-Step Process**:

1. **Extract Raw Metrics** from source data:
   - Physician data: `Tot_Srvcs`, `Tot_Benes`, `Avg_Sbmtd_Chrg`
   - Prescriber data: `Tot_Clms`, `Tot_Benes`, `Tot_Drug_Cst`

2. **Calculate 6 Base Features**:
   ```
   cost_per_service = Avg_Sbmtd_Chrg
   services_per_bene = Tot_Srvcs / Tot_Benes
   cost_per_bene_phys = (Avg_Sbmtd_Chrg × Tot_Srvcs) / Tot_Benes
   scripts_per_bene = Tot_Clms / Tot_Benes
   drug_cost_per_script = Tot_Drug_Cst / Tot_Clms
   cost_per_bene_presc = Tot_Drug_Cst / Tot_Benes
   ```
   **Why**: These ratios normalize billing across providers of different sizes.

3. **Specialty Normalization** (Z-Score Calculation):
   ```
   z = (value - specialty_mean) / specialty_std
   ```
   **Example**: Internal Medicine physician with cost_per_service = $150
   - Specialty mean = $100
   - Specialty std dev = $25
   - z = (150 - 100) / 25 = 2.0 (2 standard deviations above average)
   
   **Why**: Compares each provider to their specialty peers (cardiologists expected to cost more than family doctors).

4. **Tanh Transform** (Bounded Normalization):
   ```
   z_tanh = tanh(z)
   ```
   **Range**: [-1, 1]
   **Why**: Prevents extreme outliers from dominating the model. A provider 10 std devs above mean becomes ~1.0 instead of 10.0.

5. **Cluster Assignment** (K-Means):
   - Assigns provider to 1 of 5 archetypes based on cost and volume
   - One-hot encoded as 5 binary features
   **Why**: Captures practice patterns (e.g., high-cost specialist vs. high-volume routine care).

6. **PageRank** Centrality:
   - Measures provider's position in similarity network
   - High PageRank = similar to many other providers (central behavior)
   - Low PageRank = unique practice patterns (isolated)
   **Why**: Identifies referral networks and potential collusion patterns.

7. **Assemble 11-Dimensional Feature Vector**:
   ```
   [cps_z_tanh, spb_z_tanh, cpb_phys_z_tanh, dcp_z_tanh, cpb_presc_z_tanh,
    cluster_0, cluster_1, cluster_2, cluster_3, cluster_4,
    pagerank_centrality]
   ```

8. **Scale Features** with RobustScaler:
   - Centers features around median (robust to outliers)
   - Scales based on interquartile range

9. **Neural Network Forward Pass**:
   - Layer 1: 11 → 64 neurons (feature extraction)
   - Layer 2: 64 → 32 neurons (abstract representation)
   - Output: 32 → 1 neuron (fraud probability)

10. **Sigmoid Activation**:
    ```
    risk_score = 1 / (1 + e^(-x))
    ```
    Converts network output to probability in [0, 1].

11. **Classification**:
    - risk > 0.7: HIGH
    - 0.4 ≤ risk ≤ 0.7: MEDIUM
    - risk < 0.4: LOW

**Example End-to-End**:
- Provider bills $300/service (specialty avg: $100, std: $50)
- z-score: (300-100)/50 = 4.0 (very high!)
- tanh(4.0) = 0.9993
- After neural network: risk_score = 0.92
- Classification: HIGH RISK

---

#### 4.0.2 SHAP Explanation Algorithm - Detailed Explanation

**Purpose**: Explain *why* the model assigned a specific risk score by calculating each feature's contribution.

**The Problem**: A neural network gives a risk score, but doesn't explain which features drove that score.

**The Solution**: SHAP (SHapley Additive exPlanations) uses game theory to fairly distribute credit.

**Key Concept**: Shapley values from cooperative game theory.
- **Players**: Features (cost_per_service, services_per_bene, etc.)
- **Game**: Predicting fraud risk
- **Payout**: Final prediction - baseline prediction
- **Question**: How much should each feature be "paid" for its contribution?

**Step-by-Step Process**:

1. **Initialize Background Dataset**:
   - Sample 100 random training examples
   - These represent "typical" provider profiles

2. **Calculate Baseline Prediction**:
   ```
   E[f(x)] = average prediction over background data
   ```
   **Example**: Baseline = 0.12 (12% average risk across all providers)

3. **For Each Feature i**:
   - Generate all possible subsets of other features (called "coalitions")
   - **Example**: For 3 features {A, B, C}, coalitions for feature A:
     - {} (no features)
     - {B}
     - {C}
     - {B, C}

4. **Calculate Marginal Contribution**:
   For each coalition S:
   ```
   Δ = f(S ∪ {i}) - f(S)
   ```
   **Meaning**: Prediction with feature i included - prediction without

   **Example**:
   - f({cost, volume}) = 0.7
   - f({cost, volume, centrality}) = 0.85
   - Δ = 0.85 - 0.7 = 0.15 (centrality adds +0.15 to risk)

5. **Weight by Coalition Size**:
   ```
   weight = |S|! × (n - |S| - 1)! / n!
   ```
   **Why**: Gives more weight to coalitions of medium size
   - Small coalitions (few features): Less reliable
   - Large coalitions (many features): Less informative about feature i

6. **Accumulate Weighted Contributions**:
   ```
   φᵢ = Σ [weight × Δ]
   ```
   **Result**: Feature i's SHAP value

7. **Normalization Property**:
   ```
   Σφᵢ = f(x) - E[f(x)]
   ```
   **Example**: If prediction = 0.85 and baseline = 0.12:
   - Total to distribute: 0.85 - 0.12 = 0.73
   - SHAP values sum to 0.73

8. **Interpret SHAP Values**:
   ```
   Prediction = Baseline + SHAP₁ + SHAP₂ + ... + SHAPₙ
              = 0.12    + 0.40  + 0.25  + ... + 0.08
              = 0.85
   ```

**Example SHAP Breakdown**:
```
Feature                   Value       SHAP    Interpretation
────────────────────────────────────────────────────────────
Baseline                               0.12   Average provider
cost_per_service         $300         +0.40   Very high cost (+40%)
services_per_bene        60           +0.25   High volume (+25%)
cluster_1 (High Risk)    Yes          +0.10   Risky archetype (+10%)
pagerank_centrality      0.02         -0.02   Not well-connected (-2%)
────────────────────────────────────────────────────────────
Final Prediction                       0.85   85% fraud risk
```

**Visualization** (Waterfall Chart):
```
0.12 (Baseline) 
  → +0.40 (Cost pushed right)
    → +0.25 (Volume pushed right)
      → +0.10 (Cluster pushed right)
        → -0.02 (Centrality pulled left)
          = 0.85 (Final)
```

---

#### 4.0.3 Network Analysis (PageRank) - Detailed Explanation

**Purpose**: Identify providers who are central in the similarity network (potential fraud rings or referral schemes).

**Analogy**: Google's PageRank for web pages, applied to provider similarity.

**Key Idea**: A provider is "important" if similar to many other providers who are themselves important.

**Step-by-Step Process**:

1. **Extract Features** for all providers:
   - cost_per_service
   - services_per_bene

2. **Build N×2 Feature Matrix**:
   ```
   [provider_1]: [100, 20]
   [provider_2]: [105, 22]
   ...
   [provider_N]: [95, 18]
   ```

3. **Calculate Cosine Similarity** between all pairs:
   ```
   sim(i,j) = (xᵢ · xⱼ) / (||xᵢ|| × ||xⱼ||)
   ```
   **Example**: Providers A=[100, 20] and B=[200, 40]:
   - Dot product: 100×200 + 20×40 = 20,800
   - Magnitude A: √(100² + 20²) = 101.98
   - Magnitude B: √(200² + 40²) = 203.96
   - Similarity: 20,800/(101.98×203.96) = 0.999 (nearly identical!)

4. **Apply Threshold** (0.95):
   - Only keep edges where similarity > 0.95
   - **Rationale**: Focus on very similar providers

5. **Select Top-K** (k=5):
   - For each provider, keep only 5 most similar peers
   - **Why**: Prevents highly connected hubs from dominating

6. **Build Directed Graph**:
   - Nodes: Providers
   - Edges: Provider i → j if j is in top-5 most similar to i

7. **Initialize PageRank**:
   ```
   PR(v) = 1/N for all providers
   ```
   **Example**: 10,000 providers → PR(v) = 0.0001 initially

8. **Iterate PageRank Formula**:
   ```
   PR'(v) = (1-d)/N + d × Σ [PR(u) / L(u)]
   ```
   **Variables**:
   - `d = 0.85`: Damping factor (probability of following a link)
   - `N`: Total providers
   - `PR(u)`: Current PageRank of provider u
   - `L(u)`: Number of outgoing links from u
   - `Σ`: Sum over all u that link to v

   **Intuition**:
   - 15% chance: Random jump to any provider (1-d)/N
   - 85% chance: Follow a link from similar provider

9. **Converge**:
   - Repeat until `||PR' - PR|| < 1e-6`
   - Typically 30-50 iterations

10. **Interpret Results**:
    - **High PageRank (> 0.01)**: Hub provider with many similar peers
      - Could indicate referral network
      - Could indicate standard practice in specialty
    - **Low PageRank (< 0.001)**: Isolated provider with unique behavior
      - Could be specialized niche
      - Could be anomalous billing

**Example Scenario**:
```
Network:
  Provider A → similar to B, C, D, E, F (total 5)
  Provider B → similar to A, G, H (total 3)
  Provider C → similar to A, I (total 2)
  ...

After PageRank:
  A: PR = 0.025 (high centrality, well-connected hub)
  B: PR = 0.012 (moderate)
  C: PR = 0.008 (moderate)
  ...
```

**Fraud Detection Use**:
- High centrality + high risk score → Potential fraud ring leader
- Low centrality + high risk score → Isolated bad actor

---

#### 4.0.4 K-Means Clustering - Detailed Explanation

**Purpose**: Group providers into 5 behavioral archetypes based on cost and volume patterns.

**Why Clustering?**: 
- Captures non-linear patterns
- Creates interpretable archetypes
- Adds categorical features to model

**Step-by-Step Process**:

1. **Select Features**:
   - cost_per_service (x-axis)
   - services_per_bene (y-axis)

2. **Initialize 5 Centroids** randomly:
   ```
   C₁ = [50, 10]   (low cost, low volume)
   C₂ = [300, 80]  (high cost, high volume)
   C₃ = [60, 70]   (low cost, high volume)
   C₄ = [250, 15]  (high cost, low volume)
   C₅ = [150, 40]  (moderate, moderate)
   ```

3. **Assignment Step**:
   For each provider, calculate distance to each centroid:
   ```
   d = √[(x - cₓ)² + (y - cᵧ)²]
   ```
   Assign to nearest centroid.

   **Example**: Provider at [100, 25]
   - d(C₁) = √[(100-50)² + (25-10)²] = √2725 = 52.2
   - d(C₂) = √[(100-300)² + (25-80)²] = √43025 = 207.5
   - d(C₃) = √[(100-60)² + (25-70)²] = √3625 = 60.2
   - d(C₄) = √[(100-250)² + (25-15)²] = √22600 = 150.3
   - d(C₅) = √[(100-150)² + (25-40)²] = √2725 = 52.2
   - **Nearest**: C₁ or C₅ (tie → choose C₁)

4. **Update Step**:
   For each cluster k, calculate new centroid as mean of all assigned points:
   ```
   c_k = (1/|k|) × Σ[all points in cluster k]
   ```

5. **Convergence Check**:
   - If centroids didn't move: STOP
   - Else: Repeat assignment and update

6. **Final Cluster Interpretation**:
   ```
   Cluster 0: Routine Care
     - Low cost ($50-100/service)
     - Low volume (10-30 services/bene)
     - Examples: Primary care, preventive medicine

   Cluster 1: Elevated Risk Profile  
     - High cost ($200+/service)
     - High volume (60+ services/bene)
     - FRAUD INDICATOR: Unusual to have both high

   Cluster 2: High Volume Operators
     - Low cost ($50-80/service)
     - High volume (60+ services/bene)
     - Examples: Urgent care, walk-in clinics

   Cluster 3: Specialist Care
     - High cost ($200+/service)
     - Low volume (5-20 services/bene)
     - Examples: Surgical specialists, rare procedures

   Cluster 4: Balanced Practice
     - Moderate cost ($100-150/service)
     - Moderate volume (30-50 services/bene)
     - Examples: General specialists
   ```

7. **One-Hot Encoding**:
   Convert cluster assignment to 5 binary features:
   ```
   Provider in Cluster 1 → [0, 1, 0, 0, 0]
   Provider in Cluster 3 → [0, 0, 0, 1, 0]
   ```

**Model Usage**:
- Neural network learns that Cluster 1 is risky
- Cluster 3 is legitimate but expensive
- Provides context missing from raw cost/volume alone

---

#### 4.0.5 Anomaly Detection - Detailed Explanation

**Purpose**: Rule-based initial screening before ML model.

**Philosophy**: Quick, interpretable red flags that don't require complex computation.

**7-Rule System**:

**Rule 1: Excessive Cost**
```
IF cost_per_service > $200 THEN FLAG: HIGH
```
**Rationale**: Medicare average is ~$100. Above $200 suggests upcoding or unnecessary procedures.

**Rule 2: High Volume**
```
IF services_per_bene > 50 THEN FLAG: MEDIUM
```
**Rationale**: Average is 20-30. Above 50 suggests overutilization or billing for services not rendered.

**Rule 3: Excessive Billing**
```
IF cost_per_bene > $5000 THEN FLAG: HIGH  
```
**Rationale**: Annual Medicare spending averages $3000/beneficiary. Much higher suggests fraud.

**Rule 4: Expensive Drugs**
```
IF drug_cost_per_script > $500 THEN FLAG: MEDIUM
```
**Rationale**: Median prescription cost is $50-100. High-cost drugs should be rare.

**Rule 5: Highly Connected**
```
IF pagerank_centrality > 0.01 THEN FLAG: LOW
```
**Rationale**: Very connected providers mayindicate referral rings. Needs investigation.

**Rule 6: Cost Outlier**
```
IF cps_z_tanh > 0.8 THEN FLAG: HIGH
```
**Rationale**: tanh(3) ≈ 0.995, so 0.8 means ~2 std devs above specialty mean. Statistical outlier.

**Rule 7: Volume Outlier**
```
IF spb_z_tanh > 0.8 THEN FLAG: HIGH
```
**Rationale**: Same as Rule 6, for volume instead of cost.

**Severity Classification**:
- **0 flags**: CLEAN (no investigation needed)
- **1-2 flags**: REVIEW (minor anomalies, worth checking)
- **3+ flags**: ALERT (multiple red flags, priority investigation)

**Example**:
```
Provider X:
  cost_per_service = $350     → Rule 1: ✓ HIGH
  services_per_bene = 65      → Rule 2: ✓ MEDIUM
  cost_per_bene = $6,500      → Rule 3: ✓ HIGH
  drug_cost_per_script = $120 → Rule 4: ✗
  pagerank = 0.005            → Rule 5: ✗
  cps_z_tanh = 0.92           → Rule 6: ✓ HIGH
  spb_z_tanh = 0.75           → Rule 7: ✗

Total Flags: 4 → STATUS: ALERT
```

**Integration with ML**:
- Anomaly detection runs BEFORE ML model
- Provides context for investigators
- ML model may override (e.g., specialist with legitimately high cost)
- Both used together for final decision

---

### 4.1 Risk Calculation Algorithm

```mermaid
flowchart TD
    START([Input: Provider Data]) --> EXTRACT[Extract Raw Metrics<br/>Physician + Prescriber data]
    
    EXTRACT --> CALC_BASE[Calculate Base Features]
    
    subgraph "Base Feature Calculation"
        CALC_BASE --> B1["cost_per_service = Avg_Sbmtd_Chrg"]
        CALC_BASE --> B2["services_per_bene = Tot_Srvcs / Tot_Benes"]
        CALC_BASE --> B3["cost_per_bene_phys = Total Cost / Tot_Benes"]
        CALC_BASE --> B4["scripts_per_bene = Tot_Clms / Tot_Benes"]
        CALC_BASE --> B5["drug_cost_per_script = Tot_Drug_Cst / Tot_Clms"]
        CALC_BASE --> B6["cost_per_bene_presc = Tot_Drug_Cst / Tot_Benes"]
    end
    
    B1 --> NORM
    B2 --> NORM
    B3 --> NORM
    B4 --> NORM
    B5 --> NORM
    B6 --> NORM
    
    NORM[Specialty Normalization] --> Z1["z₁ = (b₁ - μ₁) / σ₁"]
    NORM --> Z2["z₂ = (b₂ - μ₂) / σ₂"]
    NORM --> Z3["z₃ = (b₃ - μ₃) / σ₃"]
    NORM --> Z4["z₄ = (b₄ - μ₄) / σ₄"]
    NORM --> Z5["z₅ = (b₅ - μ₅) / σ₅"]
    NORM --> Z6["z₆ = (b₆ - μ₆) / σ₆"]
    
    Z1 --> T1["tanh(z₁)"]
    Z2 --> T2["tanh(z₂)"]
    Z3 --> T3["tanh(z₃)"]
    Z4 --> T4["tanh(z₄)"]
    Z5 --> T5["tanh(z₅)"]
    
    T1 --> VEC
    T2 --> VEC
    T3 --> VEC
    T4 --> VEC
    T5 --> VEC
    
    CLUSTER[Cluster Assignment<br/>K-Means prediction] --> VEC
    PAGERANK[PageRank Lookup<br/>From graph] --> VEC
    
    VEC[Assemble Feature Vector<br/>11 dimensions] --> SCALE[Scale with RobustScaler]
    
    SCALE --> MODEL[Deep Neural Network<br/>Forward Pass]
    
    MODEL --> SIGMOID[Sigmoid Activation<br/>σ(x) = 1/(1+e^-x)]
    
    SIGMOID --> RISK[Risk Score ∈ [0, 1]]
    
    RISK --> CLASSIFY{Classify}
    CLASSIFY -->|> 0.7| HIGH[HIGH RISK]
    CLASSIFY -->|0.4-0.7| MEDIUM[MEDIUM RISK]
    CLASSIFY -->|< 0.4| LOW[LOW RISK]
    
    HIGH --> END([Output: Risk Assessment])
    MEDIUM --> END
    LOW --> END
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style MODEL fill:#9B59B6,stroke:#8E44AD,color:#fff
```

### 4.2 SHAP Explanation Algorithm

```mermaid
flowchart TD
    START([Input: Feature Vector x]) --> INIT[Initialize SHAP DeepExplainer<br/>with background data]
    
    INIT --> SAMPLE[Sample Background Data<br/>100 random training examples]
    
    SAMPLE --> BASELINE[Calculate Baseline Prediction<br/>E[f(x)] over background]
    
    BASELINE --> COALITION[Generate Feature Coalitions<br/>All subsets of features]
    
    COALITION --> LOOP{For each<br/>coalition S}
    
    LOOP -->|More coalitions| INCLUDE[Predict with S ∪ {i}<br/>f(x_S∪i)]
    INCLUDE --> EXCLUDE[Predict without i<br/>f(x_S)]
    EXCLUDE --> DIFF[Calculate Difference<br/>Δ = f(x_S∪i) - f(x_S)]
    DIFF --> WEIGHT[Weight by Coalition Size<br/>w = |S|!(|N|-|S|-1)! / |N|!]
    WEIGHT --> ACCUMULATE[Accumulate Contribution<br/>φᵢ += w × Δ]
    ACCUMULATE --> LOOP
    
    LOOP -->|Done| NORMALIZE[Normalize SHAP Values<br/>Σφᵢ = f(x) - E[f(x)]]
    
    NORMALIZE --> SORT[Sort by Absolute Value<br/>|φ₁| ≥ |φ₂| ≥ ... ≥ |φₙ|]
    
    SORT --> TOP_K[Select Top K Features<br/>K = 5 most important]
    
    TOP_K --> FORMAT[Format Explanation<br/>Feature: Value → Impact]
    
    FORMAT --> VISUALIZE[Generate Waterfall Plot<br/>Base value → Prediction]
    
    VISUALIZE --> END([Output: SHAP Explanation])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style NORMALIZE fill:#3498DB,stroke:#2980B9,color:#fff
    style VISUALIZE fill:#F39C12,stroke:#E67E22,color:#fff
```

### 4.3 Network Analysis (PageRank) Algorithm

```mermaid
flowchart TD
    START([Input: All Providers]) --> EXTRACT[Extract Features<br/>cost_per_service, services_per_bene]
    
    EXTRACT --> MATRIX[Build Feature Matrix<br/>N × 2 matrix]
    
    MATRIX --> COSINE[Calculate Cosine Similarity<br/>sim(i,j) = (xᵢ·xⱼ)/(||xᵢ|| ||xⱼ||)]
    
    COSINE --> SIM_MATRIX[Similarity Matrix<br/>N × N symmetric]
    
    SIM_MATRIX --> THRESHOLD{For each pair (i,j)}
    
    THRESHOLD --> CHECK_SIM{sim(i,j)<br/>> 0.95?}
    CHECK_SIM -->|Yes| ADD_EDGE[Add Edge i→j<br/>to graph G]
    CHECK_SIM -->|No| THRESHOLD
    ADD_EDGE --> TOP_K{Edge in<br/>top-5 for i?}
    TOP_K -->|Yes| KEEP[Keep Edge]
    TOP_K -->|No| REMOVE[Remove Edge]
    KEEP --> THRESHOLD
    REMOVE --> THRESHOLD
    
    THRESHOLD -->|All pairs done| GRAPH[Directed Graph G=(V,E)<br/>V = providers, E = similarities]
    
    GRAPH --> INIT_PR[Initialize PageRank<br/>PR(v) = 1/N for all v]
    
    INIT_PR --> ITERATE[PageRank Iteration<br/>PR'(v) = (1-d)/N + d·Σ PR(u)/L(u)]
    
    ITERATE --> CONVERGE{Convergence<br/>||PR' - PR|| < ε?}
    CONVERGE -->|No| UPDATE[PR = PR'<br/>Continue iteration]
    UPDATE --> ITERATE
    CONVERGE -->|Yes| FINAL_PR[Final PageRank Values<br/>Normalized [0, 1]]
    
    FINAL_PR --> MAP[Map NPI → PageRank<br/>Dictionary lookup]
    
    MAP --> END([Output: Centrality Scores])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style GRAPH fill:#3498DB,stroke:#2980B9,color:#fff
    style ITERATE fill:#9B59B6,stroke:#8E44AD,color:#fff
    
    note1[d = damping factor = 0.85<br/>N = number of nodes<br/>L(u) = out-degree of u<br/>ε = convergence threshold = 1e-6]
    style note1 fill:#FFF9C4,stroke:#F9A825,color:#000
```

### 4.4 K-Means Clustering Algorithm

```mermaid
flowchart TD
    START([Input: Provider Features]) --> SELECT[Select Clustering Features<br/>cost_per_service, services_per_bene]
    
    SELECT --> INIT[Initialize K=5 Centroids<br/>Random selection]
    
    INIT --> ASSIGN{For each<br/>provider}
    
    ASSIGN --> DISTANCE[Calculate Distance to Centroids<br/>d = √((x₁-c₁)² + (x₂-c₂)²)]
    
    DISTANCE --> MIN_DIST[Find Nearest Centroid<br/>cluster = argmin(d)]
    
    MIN_DIST --> ASSIGN_CLUSTER[Assign to Cluster<br/>label ∈ {0,1,2,3,4}]
    
    ASSIGN_CLUSTER --> ASSIGN
    
    ASSIGN -->|All assigned| UPDATE{For each<br/>cluster k}
    
    UPDATE --> MEAN[Calculate New Centroid<br/>c_k = mean(all points in k)]
    
    MEAN --> UPDATE
    
    UPDATE -->|All updated| CHECK{Centroids<br/>changed?}
    
    CHECK -->|Yes, iterate| ASSIGN
    CHECK -->|No, converged| FINAL_CLUSTERS[Final Cluster Assignments]
    
    FINAL_CLUSTERS --> ONEHOT[One-Hot Encode<br/>5 binary features]
    
    ONEHOT --> INTERPRET[Interpret Clusters<br/>Archetypes]
    
    INTERPRET --> ARCH0[Cluster 0: Routine Care<br/>Low cost, low volume]
    INTERPRET --> ARCH1[Cluster 1: Elevated Risk<br/>High cost, high volume]
    INTERPRET --> ARCH2[Cluster 2: High Volume<br/>Low cost, high volume]
    INTERPRET --> ARCH3[Cluster 3: Specialist<br/>High cost, low volume]
    INTERPRET --> ARCH4[Cluster 4: Balanced<br/>Moderate cost & volume]
    
    ARCH0 --> END([Output: Cluster Labels])
    ARCH1 --> END
    ARCH2 --> END
    ARCH3 --> END
    ARCH4 --> END
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style FINAL_CLUSTERS fill:#9B59B6,stroke:#8E44AD,color:#fff
    style ARCH1 fill:#F39C12,stroke:#E67E22,color:#fff
```

### 4.5 Anomaly Detection Algorithm

```mermaid
flowchart TD
    START([Input: Provider Data]) --> RULES[Initialize Rule Checkers]
    
    RULES --> R1{cost_per_service<br/>> $200?}
    R1 -->|Yes| FLAG1[Flag: EXCESSIVE_COST<br/>Severity: HIGH]
    R1 -->|No| R2
    FLAG1 --> R2
    
    R2{services_per_bene<br/>> 50?}
    R2 -->|Yes| FLAG2[Flag: HIGH_VOLUME<br/>Severity: MEDIUM]
    R2 -->|No| R3
    FLAG2 --> R3
    
    R3{cost_per_bene_phys<br/>> $5000?}
    R3 -->|Yes| FLAG3[Flag: EXCESSIVE_BILLING<br/>Severity: HIGH]
    R3 -->|No| R4
    FLAG3 --> R4
    
    R4{drug_cost_per_script<br/>> $500?}
    R4 -->|Yes| FLAG4[Flag: EXPENSIVE_DRUGS<br/>Severity: MEDIUM]
    R4 -->|No| R5
    FLAG4 --> R5
    
    R5{pagerank_centrality<br/>> 0.01?}
    R5 -->|Yes| FLAG5[Flag: HIGHLY_CONNECTED<br/>Severity: LOW<br/>Potential referral ring]
    R5 -->|No| R6
    FLAG5 --> R6
    
    R6{cps_z_tanh<br/>> 0.8?}
    R6 -->|Yes| FLAG6[Flag: OUTLIER_COST<br/>Severity: HIGH<br/>3+ std devs from mean]
    R6 -->|No| R7
    FLAG6 --> R7
    
    R7{spb_z_tanh<br/>> 0.8?}
    R7 -->|Yes| FLAG7[Flag: OUTLIER_VOLUME<br/>Severity: HIGH<br/>3+ std devs from mean]
    R7 -->|No| COLLECT
    FLAG7 --> COLLECT
    
    COLLECT[Collect All Flags] --> COUNT{Number of<br/>flags}
    
    COUNT -->|0| CLEAN[Status: CLEAN<br/>No anomalies detected]
    COUNT -->|1-2| REVIEW[Status: REVIEW<br/>Minor anomalies]
    COUNT -->|3+| ALERT[Status: ALERT<br/>Multiple red flags]
    
    CLEAN --> REPORT[Generate Report]
    REVIEW --> REPORT
    ALERT --> REPORT
    
    REPORT --> END([Output: Anomaly Report])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style ALERT fill:#E74C3C,stroke:#C0392B,color:#fff
    style REVIEW fill:#F39C12,stroke:#E67E22,color:#fff
    style CLEAN fill:#2ECC71,stroke:#27AE60,color:#fff
```

---

## 5. CI/CD Pipeline

### 5.1 Continuous Integration Workflow

```mermaid
flowchart TB
    TRIGGER([Code Push / PR]) --> CHECKOUT[Checkout Code<br/>from Repository]
    
    CHECKOUT --> SETUP_ENV[Setup Environment<br/>Python 3.9, venv]
    
    SETUP_ENV --> INSTALL[Install Dependencies<br/>pip install -r requirements.txt]
    
    INSTALL --> LINT[Code Quality Checks]
    
    subgraph "Linting & Formatting"
        LINT --> FLAKE8[Flake8 Linting<br/>PEP8 compliance]
        LINT --> BLACK[Black Formatting<br/>Code style]
        LINT --> MYPY[MyPy Type Checking<br/>Static analysis]
    end
    
    FLAKE8 --> LINT_RESULT
    BLACK --> LINT_RESULT
    MYPY --> LINT_RESULT
    
    LINT_RESULT{Linting<br/>Passed?} -->|No| FAIL_LINT[❌ Build Failed<br/>Notify developers]
    LINT_RESULT -->|Yes| UNIT_TESTS[Unit Tests<br/>pytest tests/]
    
    UNIT_TESTS --> TEST_RESULT{Tests<br/>Passed?}
    TEST_RESULT -->|No| FAIL_TEST[❌ Build Failed<br/>Test failures]
    TEST_RESULT -->|Yes| INTEGRATION
    
    subgraph "Integration Tests"
        INTEGRATION[Integration Tests] --> TEST_API[Test API Endpoints<br/>FastAPI routes]
        INTEGRATION --> TEST_AGENTS[Test Agent Workflows<br/>LangGraph execution]
        INTEGRATION --> TEST_ML[Test ML Pipeline<br/>Model loading & inference]
    end
    
    TEST_API --> INT_RESULT
    TEST_AGENTS --> INT_RESULT
    TEST_ML --> INT_RESULT
    
    INT_RESULT{Integration<br/>Passed?} -->|No| FAIL_INT[❌ Build Failed<br/>Integration errors]
    INT_RESULT -->|Yes| BUILD_ARTIFACTS[Build Artifacts<br/>python build_artifacts.py]
    
    BUILD_ARTIFACTS --> DOCKER{Build<br/>Docker Image?}
    
    DOCKER -->|Yes| DOCKER_BUILD[Docker Build<br/>docker build -t fraudguard:latest]
    DOCKER_BUILD --> DOCKER_PUSH[Push to Registry<br/>docker push]
    DOCKER_PUSH --> SUCCESS
    
    DOCKER -->|No| SUCCESS[✅ Build Successful<br/>Ready for deployment]
    
    FAIL_LINT --> NOTIFY[Send Notifications<br/>Email, Slack]
    FAIL_TEST --> NOTIFY
    FAIL_INT --> NOTIFY
    SUCCESS --> NOTIFY
    
    style TRIGGER fill:#2ECC71,stroke:#27AE60,color:#fff
    style SUCCESS fill:#2ECC71,stroke:#27AE60,color:#fff
    style FAIL_LINT fill:#E74C3C,stroke:#C0392B,color:#fff
    style FAIL_TEST fill:#E74C3C,stroke:#C0392B,color:#fff
    style FAIL_INT fill:#E74C3C,stroke:#C0392B,color:#fff
```

### 5.2 Continuous Deployment Workflow

```mermaid
flowchart TD
    START([Successful Build]) --> ENV{Target<br/>Environment}
    
    ENV -->|Development| DEV_DEPLOY[Deploy to Dev Server]
    ENV -->|Staging| STAGE_DEPLOY[Deploy to Staging]
    ENV -->|Production| PROD_APPROVE{Manual<br/>Approval?}
    
    PROD_APPROVE -->|No| WAIT[Wait for Approval]
    WAIT --> PROD_APPROVE
    PROD_APPROVE -->|Yes| PROD_DEPLOY[Deploy to Production]
    
    DEV_DEPLOY --> DEPLOY_STEPS_DEV
    STAGE_DEPLOY --> DEPLOY_STEPS_STAGE
    PROD_DEPLOY --> DEPLOY_STEPS_PROD
    
    subgraph "Deployment Steps"
        DEPLOY_STEPS_DEV[Deployment Process] --> STOP[Stop Running Service<br/>systemctl stop fraudguard]
        STOP --> BACKUP[Backup Current Version<br/>Database + Models]
        BACKUP --> PULL[Pull Latest Code/Image<br/>git pull / docker pull]
        PULL --> MIGRATE[Run Migrations<br/>Database schema updates]
        MIGRATE --> ENV_CONFIG[Update Environment<br/>Load .env variables]
        ENV_CONFIG --> START_SERVICE[Start Service<br/>systemctl start fraudguard]
    end
    
    DEPLOY_STEPS_STAGE --> START_SERVICE
    DEPLOY_STEPS_PROD --> START_SERVICE
    
    START_SERVICE --> HEALTH{Health<br/>Check}
    
    HEALTH -->|Pass| SMOKE[Smoke Tests<br/>Critical endpoints]
    HEALTH -->|Fail| ROLLBACK[Rollback to Previous<br/>Restore backup]
    
    SMOKE --> SMOKE_RESULT{Smoke Tests<br/>Passed?}
    SMOKE_RESULT -->|No| ROLLBACK
    SMOKE_RESULT -->|Yes| MONITOR[Start Monitoring<br/>Logs, metrics, alerts]
    
    ROLLBACK --> NOTIFY_FAIL[❌ Deployment Failed<br/>Alert team]
    MONITOR --> NOTIFY_SUCCESS[✅ Deployment Successful<br/>Notify team]
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style NOTIFY_SUCCESS fill:#2ECC71,stroke:#27AE60,color:#fff
    style ROLLBACK fill:#E74C3C,stroke:#C0392B,color:#fff
    style NOTIFY_FAIL fill:#E74C3C,stroke:#C0392B,color:#fff
```

### 5.3 Model Retraining Pipeline (CI/CD for ML)

```mermaid
flowchart TB
    TRIGGER([Scheduled / Manual Trigger]) --> COLLECT[Collect Feedback Data<br/>From feedback.db]
    
    COLLECT --> CHECK{Sufficient<br/>Feedback?}
    CHECK -->|< 100 samples| SKIP[Skip Retraining<br/>Insufficient data]
    CHECK -->|≥ 100 samples| PREPARE[Prepare Training Data<br/>Merge with existing]
    
    PREPARE --> TRAIN[Run Training Pipeline<br/>python main.py]
    
    TRAIN --> VALIDATE[Validate New Model<br/>Test set evaluation]
    
    VALIDATE --> COMPARE{Performance<br/>Improved?}
    
    COMPARE -->|No| REJECT[Reject New Model<br/>Keep current version]
    COMPARE -->|Yes| APPROVE{Manual<br/>Review?}
    
    APPROVE -->|Required| REVIEW[Data Scientists Review<br/>Model metrics, SHAP]
    REVIEW --> DECISION{Approve<br/>Deployment?}
    DECISION -->|No| REJECT
    DECISION -->|Yes| DEPLOY_MODEL
    
    APPROVE -->|Auto-approve| DEPLOY_MODEL[Deploy New Model]
    
    DEPLOY_MODEL --> VERSION[Increment Model Version<br/>v1.2.3 → v1.2.4]
    
    VERSION --> SAVE[Save Model Artifacts<br/>Model, scaler, explainer]
    
    SAVE --> UPDATE_CONFIG[Update Config<br/>model_version in DB]
    
    UPDATE_CONFIG --> RESTART[Restart API Server<br/>Load new model]
    
    RESTART --> VERIFY[Verify Model Loading<br/>Test inference]
    
    VERIFY --> VERIFY_RESULT{Model<br/>Working?}
    VERIFY_RESULT -->|No| ROLLBACK_MODEL[Rollback to Previous<br/>Restore old artifacts]
    VERIFY_RESULT -->|Yes| SUCCESS[✅ Model Deployed<br/>Monitor performance]
    
    SKIP --> END([End Pipeline])
    REJECT --> END
    ROLLBACK_MODEL --> END
    SUCCESS --> END
    
    style TRIGGER fill:#2ECC71,stroke:#27AE60,color:#fff
    style SUCCESS fill:#2ECC71,stroke:#27AE60,color:#fff
    style REJECT fill:#F39C12,stroke:#E67E22,color:#fff
    style ROLLBACK_MODEL fill:#E74C3C,stroke:#C0392B,color:#fff
```

---

## 6. Deployment Workflows

### 6.1 Docker Deployment Architecture

```mermaid
graph TB
    subgraph "Host Machine"
        DOCKER_ENGINE[Docker Engine]
        
        subgraph "FraudGuard Container"
            APP[FastAPI Application<br/>Port 8000]
            MODELS[Model Artifacts<br/>/app/models]
            DATA[Data Volume<br/>/app/data]
        end
        
        subgraph "Volumes"
            VOL_DATA[Data Volume<br/>./data:/app/data]
            VOL_MODELS[Models Volume<br/>./models:/app/models]
        end
        
        DOCKER_ENGINE --> APP
        VOL_DATA -.mounted.-> DATA
        VOL_MODELS -.mounted.-> MODELS
    end
    
    subgraph "External"
        NGINX[Nginx Reverse Proxy<br/>Port 80/443]
        USER[End Users]
    end
    
    USER -->|HTTPS| NGINX
    NGINX -->|HTTP| APP
    
    style APP fill:#FF6B6B,stroke:#C73E3A,color:#fff
    style NGINX fill:#3498DB,stroke:#2980B9,color:#fff
```

### 6.2 Production Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx Load Balancer<br/>Round-robin]
    end
    
    subgraph "Application Servers"
        SERVER1[Server 1<br/>Uvicorn Worker 1-2]
        SERVER2[Server 2<br/>Uvicorn Worker 3-4]
        SERVER3[Server 3<br/>Uvicorn Worker 5-6]
    end
    
    subgraph "Shared Storage"
        NFS[NFS Share<br/>Models & Data]
        DB[PostgreSQL Database<br/>Providers, Cases, Feedback]
        REDIS[Redis Cache<br/>Sessions, Features]
    end
    
    subgraph "Monitoring"
        PROMETHEUS[Prometheus<br/>Metrics Collection]
        GRAFANA[Grafana<br/>Dashboards]
        ALERTS[Alert Manager<br/>Notifications]
    end
    
    INTERNET[Internet] --> LB
    LB --> SERVER1
    LB --> SERVER2
    LB --> SERVER3
    
    SERVER1 --> NFS
    SERVER1 --> DB
    SERVER1 --> REDIS
    
    SERVER2 --> NFS
    SERVER2 --> DB
    SERVER2 --> REDIS
    
    SERVER3 --> NFS
    SERVER3 --> DB
    SERVER3 --> REDIS
    
    SERVER1 -.metrics.-> PROMETHEUS
    SERVER2 -.metrics.-> PROMETHEUS
    SERVER3 -.metrics.-> PROMETHEUS
    
    PROMETHEUS --> GRAFANA
    PROMETHEUS --> ALERTS
    
    style LB fill:#3498DB,stroke:#2980B9,color:#fff
    style DB fill:#E74C3C,stroke:#C0392B,color:#fff
    style REDIS fill:#F39C12,stroke:#E67E22,color:#fff
```

---

*Document Version: 1.0*  
*Last Updated: 2025-11-28*  
*Author: Kalyan Uppuluri*
