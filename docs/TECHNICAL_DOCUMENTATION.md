# FraudGuard - Comprehensive Technical Documentation

## Table of Contents
1. [Mathematical Notation Guide](#mathematical-notation-guide)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Technology Stack](#technology-stack)
5. [Data Models](#data-models)
6. [Machine Learning Pipeline](#machine-learning-pipeline)
7. [Multi-Agent System](#multi-agent-system)
8. [API Reference](#api-reference)
9. [Deployment](#deployment)
10. [Security](#security)
11. [Performance](#performance)

---

## Mathematical Notation Guide

This section explains all mathematical formulas, symbols, and statistical concepts used throughout the documentation.

### Common Symbols

| Symbol | Meaning | Example |
|--------|---------|---------|
| **μ** (mu) | Mean (average) value | μ = Σx / n |
| **σ** (sigma) | Standard deviation | σ = √(Σ(x-μ)² / n) |
| **Σ** (capital sigma) | Sum of all values | Σx = x₁ + x₂ + ... + xₙ |
| **∈** (element of) | Value belongs to set | x ∈ [0, 1] means x is between 0 and 1 |
| **∩** (intersection) | Common elements | A ∩ B |
| **∪** (union) | Combined elements | A ∪ B |
| **→** (arrow) | Approaches or maps to | x → y |
| **≥** (greater or equal) | Greater than or equal to | x ≥ 5 |
| **≤** (less or equal) | Less than or equal to | x ≤ 10 |
| **∂** (partial derivative) | Rate of change | ∂L/∂W |
| **√** (square root) | Square root | √16 = 4 |

### Statistical Formulas

#### 1. Mean (Average)
```
μ = Σx / n
```
**Explanation**: Sum all values (Σx) and divide by the count (n).

**Example**: For values [10, 20, 30], μ = (10+20+30)/3 = 20

#### 2. Standard Deviation
```
σ = √(Σ(x - μ)² / n)
```
**Explanation**: 
1. Calculate mean (μ)
2. For each value (x), find difference from mean: (x - μ)
3. Square each difference: (x - μ)²
4. Sum all squared differences: Σ(x - μ)²
5. Divide by count: / n
6. Take square root: √

**Purpose**: Measures how spread out values are from the mean.

**Example**: For [10, 20, 30] with μ=20:
- Differences: [-10, 0, +10]
- Squared: [100, 0, 100]
- Sum: 200
- Divide by 3: 66.67
- Square root: σ = 8.16

#### 3. Z-Score (Standard Score)
```
z = (x - μ) / σ
```
**Explanation**:
- `x`: The value we're measuring
- `μ`: Mean of all values in the group
- `σ`: Standard deviation of the group
- `z`: How many standard deviations away from mean

**Purpose**: Normalizes values to compare across different scales.

**Interpretation**:
- z = 0: Value is exactly at the mean
- z = 1: Value is 1 standard deviation above mean
- z = -1: Value is 1 standard deviation below mean
- |z| > 2: Unusual value (outlier)
- |z| > 3: Very unusual value (strong outlier)

**Example**: If a provider's cost per service is $250:
- Specialty mean (μ) = $100
- Specialty std dev (σ) = $50
- z = (250 - 100) / 50 = 3.0
- **Interpretation**: This provider charges 3 standard deviations above average (very high!)

#### 4. Tanh (Hyperbolic Tangent)
```
tanh(x) = (e^x - e^-x) / (e^x + e^-x)
```
**Explanation**: A mathematical function that squashes any value into the range [-1, 1].

**Simplified**: 
- Very negative numbers → -1
- Zero → 0
- Very positive numbers → +1

**Purpose**: In our system, we use `tanh(z-score)` to:
1. Keep all features in a bounded range
2. Prevent extreme values from dominating the model
3. Make features comparable

**Example**:
- tanh(0) = 0 (at mean)
- tanh(1) ≈ 0.76 (above mean)
- tanh(3) ≈ 0.995 (very high, but bounded)
- tanh(-3) ≈ -0.995 (very low, but bounded)

### Machine Learning Formulas

#### 5. Cosine Similarity
```
cosine_sim(A, B) = (A · B) / (||A|| × ||B||)
```
**Explanation**:
- `A · B`: Dot product = A₁×B₁ + A₂×B₂ + ... + Aₙ×Bₙ
- `||A||`: Magnitude of A = √(A₁² + A₂² + ... + Aₙ²)
- `||B||`: Magnitude of B = √(B₁² + B₂² + ... + Bₙ²)

**Purpose**: Measures how similar two providers are based on their features.

**Range**: -1 to 1
- 1: Identical behavior
- 0: No similarity
- -1: Completely opposite

**Example**: Two providers with features [100, 20] and [200, 40]:
- Dot product: 100×200 + 20×40 = 20,800
- Magnitude A: √(100² + 20²) = √10,400 = 101.98
- Magnitude B: √(200² + 40²) = √41,600 = 203.96
- Similarity: 20,800 / (101.98 × 203.96) = 0.999 (nearly identical!)

#### 6. PageRank
```
PR(v) = (1-d)/N + d × Σ(PR(u) / L(u))
```
**Explanation**:
- `PR(v)`: PageRank score for provider v
- `d`: Damping factor (usually 0.85) - probability of following a link
- `N`: Total number of providers
- `PR(u)`: PageRank of provider u who links to v
- `L(u)`: Number of outgoing links from u
- `Σ`: Sum over all providers u that link to v

**Purpose**: Identifies influential providers in the similarity network.

**Interpretation**:
- High PageRank: Provider is similar to many other providers (central in network)
- Low PageRank: Provider has unique behavior (isolated in network)

**Example**: If provider A is similar to 10 others who are each similar to 2 providers, A gets importance from being a "hub" in the network.

#### 7. Sigmoid Function
```
σ(x) = 1 / (1 + e^-x)
```
**Explanation**: Converts any number to a probability between 0 and 1.

**Simplified**:
- Very negative x → 0
- x = 0 → 0.5
- Very positive x → 1

**Purpose**: Final layer of neural network converts score to fraud probability.

**Example**:
- σ(-5) ≈ 0.007 (low fraud risk)
- σ(0) = 0.5 (boundary)
- σ(5) ≈ 0.993 (high fraud risk)

#### 8. Focal Loss
```
FL(p_t) = -α × (1 - p_t)^γ × log(p_t)
```
**Explanation**:
- `p_t`: Predicted probability for the true class
- `α`: Weighting factor (balances positive/negative examples)
- `γ`: Focusing parameter (default 2.0) - emphasizes hard examples
- `log`: Natural logarithm

**Purpose**: Loss function that focuses training on hard-to-classify examples.

**Why We Use It**: 
- Standard datasets have few fraud cases (imbalanced)
- Focal loss reduces loss for easy examples (well-classified)
- Increases loss for hard examples (misclassified)
- Forces model to learn from difficult fraud cases

**Example**:
- Easy example (p_t = 0.9): Loss is reduced by factor (1-0.9)² = 0.01
- Hard example (p_t = 0.6): Loss is reduced by factor (1-0.6)² = 0.16
- Model focuses 16x more on the hard example!

#### 9. SHAP (Shapley Values)
```
φᵢ = Σ [ (|S|! × (|N|-|S|-1)!) / |N|! ] × [f(S∪{i}) - f(S)]
```
**Explanation**:
- `φᵢ`: SHAP value for feature i (contribution to prediction)
- `S`: A subset of features (a "coalition")
- `N`: All features
- `|S|`: Number of features in subset S
- `!`: Factorial (e.g., 5! = 5×4×3×2×1 = 120)
- `f(S∪{i})`: Model prediction with features S and feature i
- `f(S)`: Model prediction with only features S
- `Σ`: Sum over all possible subsets S

**Purpose**: Fairly distributes the prediction credit among all features.

**Simplified Interpretation**:
- Positive SHAP: Feature increases fraud risk
- Negative SHAP: Feature decreases fraud risk
- Magnitude: How much the feature matters

**Example**: If base risk is 0.1 and prediction is 0.8:
- Total increase: 0.7
- SHAP values distribute this: [+0.4 from cost, +0.2 from volume, +0.1 from centrality]
- Sum of SHAP values = 0.7 (explains the full difference)

### Neural Network Formulas

#### 10. Forward Propagation
```
z = W × x + b
a = activation(z)
```
**Explanation**:
- `x`: Input features (11-dimensional vector)
- `W`: Weights matrix (learned during training)
- `b`: Bias term (learned during training)
- `z`: Pre-activation value (weighted sum)
- `a`: Activated output (passed through activation function)

**Example for one neuron**:
- Input: x = [0.5, 0.3, 0.8]
- Weights: W = [0.2, -0.4, 0.6]
- Bias: b = 0.1
- z = 0.5×0.2 + 0.3×(-0.4) + 0.8×0.6 + 0.1 = 0.1 - 0.12 + 0.48 + 0.1 = 0.56
- a = PReLU(0.56) = 0.56 (positive, so pass through)

#### 11. Backpropagation (Gradient Descent)
```
∂L/∂W = (∂L/∂a) × (∂a/∂z) × (∂z/∂W)
W_new = W_old - α × ∂L/∂W
```
**Explanation**:
- `L`: Loss (error) of the model
- `∂L/∂W`: Gradient (how much changing weight W affects loss)
- `α`: Learning rate (step size for updates)
- Chain rule: Calculate gradient by multiplying derivatives

**Purpose**: Updates weights to reduce prediction errors.

**Simplified Process**:
1. Make prediction (forward pass)
2. Calculate error (loss)
3. Find how each weight contributed to error (backward pass)
4. Adjust weights to reduce error (gradient descent)

#### 12. Adam Optimizer
```
m_t = β₁ × m_{t-1} + (1 - β₁) × g_t
v_t = β₂ × v_{t-1} + (1 - β₂) × g_t²
W = W - α × m_t / √(v_t + ε)
```
**Explanation**:
- `g_t`: Gradient at timestep t
- `m_t`: Moving average of gradients (momentum)
- `v_t`: Moving average of squared gradients (variance)
- `β₁`: Momentum decay rate (typically 0.9)
- `β₂`: Variance decay rate (typically 0.999)
- `α`: Learning rate (typically 0.001)
- `ε`: Small constant to prevent division by zero (typically 10⁻⁸)

**Purpose**: Adaptive learning rate optimizer that:
1. Maintains momentum (smooths out updates)
2. Adapts learning rate per parameter
3. Converges faster than standard gradient descent

**Why Better**: Combines benefits of momentum and adaptive learning rates.

---

## 1. Project Overview

### 1.1 Purpose
FraudGuard is an advanced healthcare fraud detection system designed to identify anomalous billing patterns in Medicare data using Multi-Agentic AI, Deep Learning, and Explainable AI (XAI). The system analyzes provider behavior across multiple data sources to detect potential fraud, waste, and abuse.

### 1.2 Key Objectives
- **Automated Fraud Detection**: Identify fraudulent billing patterns using deep learning models
- **Explainability**: Provide clear, interpretable explanations for all predictions using SHAP
- **Multi-Agent Collaboration**: Employ specialized AI agents for investigation, analysis, and reporting
- **Real-time Monitoring**: Continuously scan provider database for emerging risks
- **Scalability**: Process large-scale Medicare datasets efficiently

### 1.3 Core Capabilities
- Deep neural network-based fraud risk scoring (0.0-1.0 scale)
- SHAP-based feature importance analysis
- Network analysis using provider similarity graphs
- Rule-based anomaly detection
- LLM-powered narrative report generation
- Real-time dashboard with search and filtering
- Session-based authentication system
- Model Context Protocol (MCP) integration

---

## 2. System Architecture

### 2.1 High-Level Architecture

The system follows a modular, layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Dashboard  │  │ Investigation│  │    Search    │  │
│  │   (Jinja2)   │  │    Reports   │  │   Interface  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │            FastAPI REST API Server               │  │
│  │  /analyze_provider  /dashboard_stats  /search    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Agent Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Investigator│ │ Analyst  │ │Supervisor│ │ Reporter │  │
│  │   Agent   │ │  Agent   │ │  Agent   │ │  Agent   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│        ↓            ↓            ↓            ↓         │
│  ┌────────────────────────────────────────────────┐    │
│  │           LangGraph Workflow Engine             │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   ML Model   │  │     SHAP     │  │   Network    │  │
│  │  (TensorFlow)│  │  Explainer   │  │   Analysis   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   SQLite     │  │     CSV      │  │   Feature    │  │
│  │  (Providers) │  │  (Raw Data)  │  │    Store     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Component Descriptions

#### Presentation Layer
- **Dashboard**: Main UI for viewing provider statistics, risk scores, and analytics
- **Investigation Reports**: Detailed HTML reports with SHAP visualizations and risk analysis
- **Search Interface**: Advanced search and filter capabilities for provider directory

#### Application Layer
- **FastAPI Server**: High-performance async REST API with automatic documentation
- **Session Management**: HTTP-only cookie-based authentication
- **Request Validation**: Pydantic models for request/response validation

#### Agent Layer
- **Investigator Agent**: Performs initial rule-based anomaly detection
- **Analyst Agent**: Runs ML model and generates SHAP explanations
- **Supervisor Agent**: Makes final payment decisions based on risk analysis
- **Reporter Agent**: Synthesizes findings into narrative reports
- **LangGraph Engine**: Orchestrates multi-agent workflows with state management

#### Service Layer
- **ML Model**: Deep neural network for fraud risk prediction
- **SHAP Explainer**: Generates feature importance explanations
- **Network Analysis**: Cosine similarity-based peer comparison

#### Data Layer
- **SQLite Database**: Stores provider records, cases, and feedback
- **CSV Files**: Raw Medicare datasets (Physician, Prescriber, LEIE)
- **Feature Store**: Pre-computed engineered features for fast inference

---

## 3. Technology Stack

### 3.1 Backend Technologies

#### Core Framework
- **FastAPI 0.95+**: Modern async web framework
  - Auto-generated OpenAPI documentation
  - Built-in request validation
  - High performance (comparable to Node.js/Go)

#### Machine Learning
- **TensorFlow 2.10+**: Deep learning framework
  - Custom focal loss for imbalanced datasets
  - Model serialization and versioning
- **scikit-learn 1.0+**: Traditional ML and preprocessing
  - RobustScaler for outlier handling
  - KMeans clustering for archetype detection
- **SHAP 0.41+**: Model explainability
  - TreeExplainer for tree-based models
  - DeepExplainer for neural networks
- **imbalanced-learn**: SMOTE for class imbalance

#### AI Orchestration
- **LangGraph 0.0.26+**: Workflow engine for multi-agent systems
  - State management across agent interactions
  - Conditional routing based on analysis results
- **LangChain Core**: Foundation for LLM integration

#### Data Processing
- **Pandas 1.5+**: Data manipulation and analysis
- **NumPy 1.23+**: Numerical computing
- **NetworkX 2.8+**: Graph analysis (PageRank centrality)

#### Database
- **SQLite3**: Embedded database for provider records, cases, and feedback
- **Python sqlite3 module**: Native database interface

### 3.2 Frontend Technologies

#### UI Framework
- **TailwindCSS 3.x**: Utility-first CSS framework
  - Responsive design system
  - Custom color schemes
- **Alpine.js**: Lightweight reactive framework (optional)

#### Templating
- **Jinja2**: Server-side template rendering
  - Template inheritance
  - Context variables
  - Custom filters

#### Visualization
- **Chart.js 3.x**: Interactive charts
  - Risk distribution histograms
  - Feature importance bar charts
  - Time series plots
- **Custom CSS/JS**: SHAP waterfall visualizations

### 3.3 Development & Deployment

#### Server
- **Uvicorn**: ASGI server for FastAPI
  - Hot reload during development
  - Multi-worker support in production

#### Environment Management
- **Python dotenv**: Environment variable management
- **Virtual Environment**: Isolated Python dependencies

#### Containerization
- **Docker**: Container platform
- **Docker Compose**: Multi-container orchestration

### 3.4 External Services

#### LLM Provider
- **Google Gemini Pro**: Large language model for report generation
  - API-based integration
  - Rate limiting and retry logic

#### Data Sources
- **CMS Public Datasets**: Medicare claims data
- **OIG LEIE**: List of Excluded Individuals/Entities

---

## 4. Data Models

### 4.1 Source Data Models

#### Physician Dataset (`PHY_R25`)
**Source**: Medicare Physician & Other Supplier PUF

| Column | Type | Description |
|--------|------|-------------|
| `Rndrng_NPI` | Integer | National Provider Identifier (Unique ID) |
| `Rndrng_Prvdr_Type` | String | Provider specialty (e.g., Internal Medicine) |
| `Avg_Sbmtd_Chrg` | Float | Average submitted charge per service |
| `Tot_Srvcs` | Integer | Total number of services provided |
| `Tot_Benes` | Integer | Total unique beneficiaries served |

**Additional Columns**:
- `Rndrng_Prvdr_First_Name`, `Rndrng_Prvdr_Last_Name`
- `Rndrng_Prvdr_City`, `Rndrng_Prvdr_State_Abrvtn`
- `Rndrng_Prvdr_Gndr`
- Various service-specific metrics

#### Prescriber Dataset (`DPR_RY25`)
**Source**: Medicare Part D Prescriber PUF

| Column | Type | Description |
|--------|------|-------------|
| `PRSCRBR_NPI` | Integer | National Provider Identifier |
| `Prscrbr_Type` | String | Prescriber specialty |
| `Tot_Drug_Cst` | Float | Total drug cost |
| `Tot_Clms` | Integer | Total prescription claims |
| `Tot_Benes` | Integer | Total unique beneficiaries |

**Additional Columns**:
- Drug-specific metrics (opioids, antibiotics, etc.)
- Geographic information
- Beneficiary demographics

#### LEIE Dataset
**Source**: OIG List of Excluded Individuals/Entities

| Column | Type | Description |
|--------|------|-------------|
| `NPI` | Integer | National Provider Identifier |
| `LASTNAME` | String | Provider last name |
| `FIRSTNAME` | String | Provider first name |
| `EXCLTYPE` | String | Type of exclusion |
| `EXCLDATE` | Date | Date of exclusion |

**Purpose**: Ground truth labels for known fraudulent providers

### 4.2 Feature Engineering

#### Base Features
```python
{
    "cost_per_service": Avg_Sbmtd_Chrg,
    "services_per_bene": Tot_Srvcs / Tot_Benes,
    "cost_per_bene_phys": Avg_Sbmtd_Chrg * Tot_Srvcs / Tot_Benes,
    "scripts_per_bene": Tot_Clms / Tot_Benes,
    "drug_cost_per_script": Tot_Drug_Cst / Tot_Clms,
    "cost_per_bene_presc": Tot_Drug_Cst / Tot_Benes
}
```

#### Z-Score Normalized Features
For each base feature, calculate specialty-specific z-scores:
```python
z_score = (value - specialty_mean) / specialty_std
z_tanh = tanh(z_score)  # Bounded to [-1, 1]
```

Features:
- `cps_z_tanh`: Cost per service deviation
- `spb_z_tanh`: Services per beneficiary deviation
- `cpb_phys_z_tanh`: Cost per beneficiary (physician) deviation
- `dcp_z_tanh`: Drug cost per script deviation
- `cpb_presc_z_tanh`: Cost per beneficiary (prescriber) deviation

#### Clustering Features (Archetypes)
K-Means clustering to identify provider behavior patterns:
- `cluster_0` through `cluster_4` (one-hot encoded)
- Based on `cost_per_service` and `services_per_bene`

Archetype Interpretations:
- **Cluster 0**: Routine Care (low cost, low volume)
- **Cluster 1**: Elevated Risk Profile (high cost, high volume)
- **Cluster 2**: High Volume Operators (low cost, high volume)
- **Cluster 3**: Specialist Care (high cost, low volume)
- **Cluster 4**: Balanced Practice (moderate cost & volume)

#### Graph Features
PageRank centrality based on provider similarity network:
```python
similarity = cosine_similarity([cost_per_service, services_per_bene])
network = build_graph(similarity > 0.95, top_k=5)
pagerank_centrality = pagerank(network)
```

#### Final Feature Vector
```python
feature_vector = [
    cps_z_tanh,
    spb_z_tanh,
    cpb_phys_z_tanh,
    dcp_z_tanh,
    cpb_presc_z_tanh,
    cluster_0,
    cluster_1,
    cluster_2,
    cluster_3,
    cluster_4,
    pagerank_centrality
]  # Shape: (11,) for binary classification
```

### 4.3 Database Schema

#### `providers` Table
```sql
CREATE TABLE providers (
    npi TEXT PRIMARY KEY,
    name TEXT,
    specialty TEXT,
    city TEXT,
    state TEXT,
    risk_score REAL,
    risk_level TEXT,  -- HIGH, MEDIUM, LOW
    features_json TEXT,
    last_analyzed DATETIME,
    model_version TEXT
);
```

#### `feedback` Table
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npi TEXT NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,  -- CONFIRM_FRAUD, CONFIRM_CLEAN, UNCLEAR
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

#### `cases` Table
```sql
CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npi TEXT NOT NULL,
    provider_name TEXT,
    status TEXT DEFAULT 'PENDING',  -- PENDING, REVIEWED
    submitted_by TEXT,
    decision TEXT,  -- STOP, HOLD, REVIEW, RELEASE
    notes TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Machine Learning Pipeline

### 5.1 Training Pipeline

#### Phase 1: Data Loading
```python
def load_and_prep_data(config):
    physician_df = load_csv(physician_keyword)
    prescriber_df = load_csv(prescriber_keyword)
    leie_df = load_csv(leie_keyword)
    
    # Merge on NPI
    merged_df = physician_df.merge(prescriber_df, on='NPI')
    return physician_df, prescriber_df, leie_df
```

#### Phase 2: Feature Engineering
```python
def create_advanced_features_and_split(phys_df, presc_df, leie_df, config):
    # 1. Merge datasets on NPI
    df = merge_datasets(phys_df, presc_df)
    
    # 2. Calculate base features
    df = calculate_base_features(df)
    
    # 3. Calculate specialty statistics
    specialty_stats = df.groupby('specialty').agg({
        'cost_per_service': ['mean', 'std'],
        'services_per_bene': ['mean', 'std']
    })
    
    # 4. Calculate z-scores
    df = calculate_zscores(df, specialty_stats)
    
    # 5. Apply clustering
    kmeans = KMeans(n_clusters=5)
    df['cluster'] = kmeans.fit_predict(df[['cost_per_service', 'services_per_bene']])
    df = one_hot_encode(df, 'cluster')
    
    # 6. Build similarity graph
    similarity_matrix = cosine_similarity(df[['cost_per_service', 'services_per_bene']])
    graph = build_graph(similarity_matrix, threshold=0.95)
    pagerank = nx.pagerank(graph)
    df['pagerank_centrality'] = df['NPI'].map(pagerank)
    
    # 7. Labeling (unsupervised)
    df['fraud_label'] = (df['combined_z_score'] > 3.0).astype(int)
    
    # 8. Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        df[feature_columns], df['fraud_label'], test_size=0.2
    )
    
    return X_train, X_test, y_train, y_test
```

#### Phase 3: Model Training
```python
def train_model(model, X_train, y_train, X_val, y_val, class_weights, config):
    # Apply SMOTE for class balance
    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)
    
    # Callbacks
    early_stop = EarlyStopping(monitor='val_loss', patience=5)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3)
    
    # Training
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=50,
        batch_size=2048,
        class_weight=class_weights,
        callbacks=[early_stop, reduce_lr]
    )
    
    # Save model
    model.save(config['model_path'])
    return history
```

### 5.2 Model Architecture

#### Deep Neural Network
```python
def build_deep_learning_model(input_shape, config):
    model = Sequential([
        Input(shape=input_shape),  # (11,)
        
        # Layer 1: Feature extraction
        Dense(64, kernel_regularizer=l2(0.001)),
        PReLU(),
        BatchNormalization(),
        Dropout(0.4),
        
        # Layer 2: Abstract representation
        Dense(32, kernel_regularizer=l2(0.001)),
        PReLU(),
        BatchNormalization(),
        Dropout(0.4),
        
        # Output layer: Binary classification
        Dense(1, activation='sigmoid')
    ])
    
    optimizer = Adam(learning_rate=0.001)
    
    model.compile(
        optimizer=optimizer,
        loss=BinaryFocalCrossentropy(gamma=2.0),
        metrics=[AUC(name='AUC')]
    )
    
    return model
```

**Architecture Details**:
- **Input**: 11-dimensional feature vector
- **Hidden Layer 1**: 64 neurons with PReLU activation, batch normalization, 40% dropout
- **Hidden Layer 2**: 32 neurons with PReLU activation, batch normalization, 40% dropout
- **Output**: 1 neuron with sigmoid activation (fraud probability)
- **Loss Function**: Binary Focal Crossentropy (handles class imbalance)
- **Optimizer**: Adam with learning rate 0.001
- **Regularization**: L2 regularization (λ=0.001) and dropout

### 5.3 Model Evaluation

#### Metrics
```python
def evaluate_model(model, X_test, y_test, config):
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'auc': roc_auc_score(y_test, y_pred_proba)
    }
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plot_confusion_matrix(cm)
    
    # PR curve
    plot_precision_recall_curve(y_test, y_pred_proba)
    
    return metrics
```

### 5.4 Explainability (SHAP)

```python
def generate_shap_summary(model, X_train, X_test, feature_names, config):
    # Create SHAP explainer
    explainer = shap.DeepExplainer(model, X_train[:100])
    
    # Calculate SHAP values for test set
    shap_values = explainer.shap_values(X_test[:100])
    
    # Generate summary plot
    shap.summary_plot(shap_values, X_test[:100], feature_names=feature_names)
    
    # Save explainer for inference
    joblib.dump(explainer, config['explainer_path'])
    
    return explainer, shap_values, X_test[:100]
```

---

## 6. Multi-Agent System

### 6.1 Agent Architecture

The system employs a collaborative team of specialized AI agents orchestrated by LangGraph:

```
┌─────────────────────────────────────────────────────────┐
│                  LangGraph State Graph                    │
│                                                           │
│   ┌─────────────┐      ┌─────────────┐                  │
│   │ Investigator│─────▶│   Analyst   │                  │
│   │    Agent    │      │    Agent    │                  │
│   └─────────────┘      └─────────────┘                  │
│                               │                           │
│                               ▼                           │
│                        ┌─────────────┐                   │
│                        │  Supervisor │                   │
│                        │    Agent    │                   │
│                        └─────────────┘                   │
│                               │                           │
│                               ▼                           │
│                        ┌─────────────┐                   │
│                        │  Reporter   │                   │
│                        │    Agent    │                   │
│                        └─────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Agent Descriptions

#### Investigator Agent
**Role**: Data Scout & Rule-Based Checker

**Responsibilities**:
1. Fetch provider raw data from database
2. Perform initial red flag detection
3. Summarize provider profile

**Rules**:
- Flag if `cost_per_service > $200`
- Flag if `services_per_bene > 50`
- Flag if `pagerank_centrality > 0.01` (highly connected)

**Output**:
```python
{
    "npi": 1234567890,
    "provider_name": "Dr. John Doe",
    "specialty": "Internal Medicine",
    "red_flags": ["Cost per service unusually high: $245"],
    "summary": "Provider shows elevated billing patterns"
}
```

#### Analyst Agent
**Role**: Deep Learning Expert

**Responsibilities**:
1. Run TensorFlow model for fraud prediction
2. Calculate SHAP values for explainability
3. Interpret feature importance using LLM
4. Generate technical analysis

**Process**:
```python
def run(self, provider_data, ml_assets):
    # 1. Extract features
    features = extract_features(provider_data)
    
    # 2. Predict risk
    risk_score = model.predict(features)[0][0]
    
    # 3. Calculate SHAP
    shap_values = explainer.shap_values(features)
    
    # 4. Interpret with LLM
    interpretation = self._call_llm(
        format_shap_prompt(shap_values, feature_names)
    )
    
    return {
        "risk_score": risk_score,
        "risk_level": classify_risk(risk_score),
        "shap_explanation": shap_values,
        "interpretation": interpretation
    }
```

#### Supervisor Agent
**Role**: Decision Maker

**Responsibilities**:
1. Review findings from Investigator and Analyst
2. Determine payment action
3. Provide reasoning and confidence

**Decision Logic**:
- **STOP PAYMENT**: Risk > 0.9 or clear policy violation
- **HOLD PAYMENT**: Risk > 0.7 (suspicious patterns)
- **REVIEW**: Risk 0.5-0.7 (inconclusive)
- **RELEASE**: Risk < 0.5 (low risk)

**Output**:
```python
{
    "decision": "HOLD PAYMENT",
    "confidence": "High",
    "reasoning": "Risk score 0.85 indicates likely overbilling. Multiple red flags present."
}
```

#### Reporter Agent
**Role**: Communication Specialist

**Responsibilities**:
1. Synthesize findings from all agents
2. Generate polished HTML narrative report
3. Present insights in user-friendly format

**Report Structure**:
- Executive Summary
- Risk Profile
- Key Risk Drivers
- Model Insights (SHAP visualization)
- Investigator Findings
- Analyst Findings
- Supervisor Decision
- Recommendation

### 6.3 LangGraph Workflow

```python
def build_fraud_graph():
    workflow = StateGraph(FraudAnalysisState)
    
    # Add nodes
    workflow.add_node("investigator", investigator_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("reporter", reporter_node)
    
    # Define flow
    workflow.set_entry_point("investigator")
    workflow.add_edge("investigator", "analyst")
    workflow.add_edge("analyst", "supervisor")
    workflow.add_edge("supervisor", "reporter")
    workflow.add_edge("reporter", END)
    
    return workflow.compile()
```

**State Object**:
```python
class FraudAnalysisState(TypedDict):
    npi: int
    provider_data: Any
    ml_assets: Dict[str, Any]
    risk_score: float
    risk_level: str
    shap_values: List[Dict]
    investigator_finding: str
    analyst_finding: str
    supervisor_decision: str
    final_report: str
    trace: List[str]
```

### 6.4 Monitor Agent

**Role**: Background Sentinel

**Responsibilities**:
1. Continuously scan provider database
2. Calculate real-time fraud statistics
3. Update dashboard metrics
4. Maintain scan state persistence

**Implementation**:
```python
async def monitor_loop():
    while True:
        # Load state
        state = load_monitor_state()
        
        # Get batch of providers
        providers = get_provider_batch(state['offset'], batch_size=100)
        
        # Calculate risks
        for provider in providers:
            risk = calculate_risk(provider)
            update_database(provider.npi, risk)
            
        # Update statistics
        stats = calculate_statistics()
        save_stats(stats)
        
        # Update state
        state['offset'] += batch_size
        save_monitor_state(state)
        
        await asyncio.sleep(60)  # 1 minute interval
```

---

## 7. API Reference

### 7.1 Authentication Endpoints

#### `GET /login`
Render login page

**Response**: HTML login form

#### `POST /login`
Authenticate user

**Request Body**:
```json
{
    "username": "admin",
    "password": "fraud2025"
}
```

**Response**: Redirect to `/dashboard` with session cookie

#### `GET /logout`
Logout user

**Response**: Redirect to `/login`, clear session cookie

### 7.2 Dashboard Endpoints

#### `GET /dashboard`
Render main dashboard (protected)

**Authentication**: Required

**Response**: HTML dashboard with statistics and provider directory

#### `GET /dashboard_stats`
Get real-time dashboard statistics

**Authentication**: Required

**Response**:
```json
{
    "total_providers": 123456,
    "high_risk_count": 1234,
    "medium_risk_count": 5678,
    "low_risk_count": 116544,
    "avg_risk_score": 0.234,
    "monitor_status": {
        "is_running": true,
        "scanned_count": 50000,
        "last_updated": "2025-11-28T10:30:00"
    }
}
```

### 7.3 Provider Endpoints

#### `GET /providers`
Get paginated provider directory

**Authentication**: Required

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `page_size` (int): Results per page (default: 50)
- `search` (string): Search query (NPI or name)
- `risk_filter` (string): Filter by risk level (HIGH, MEDIUM, LOW)
- `sort_by` (string): Sort column (default: risk_score)
- `sort_order` (string): Sort direction (asc, desc)

**Response**:
```json
{
    "providers": [
        {
            "npi": "1234567890",
            "name": "Dr. John Doe",
            "specialty": "Internal Medicine",
            "city": "New York",
            "state": "NY",
            "risk_score": 0.85,
            "risk_level": "HIGH"
        }
    ],
    "total": 123456,
    "page": 1,
    "page_size": 50,
    "total_pages": 2469
}
```

#### `POST /analyze_provider`
Analyze specific provider by NPI

**Authentication**: Required

**Request Body**:
```json
{
    "npi": 1234567890
}
```

**Response**:
```json
{
    "npi": "1234567890",
    "provider_name": "Dr. John Doe",
    "risk_score": 0.85,
    "risk_level": "HIGH",
    "report_html": "<html>...</html>",
    "shap_values": [...],
    "decision": "HOLD PAYMENT"
}
```

#### `POST /analyze_new_provider`
Analyze custom provider profile (what-if analysis)

**Authentication**: Required

**Request Body**:
```json
{
    "total_service_cost": 500000.0,
    "total_services": 2000,
    "total_benes_phys": 100,
    "total_drug_cost": 300000.0,
    "total_scripts": 1500,
    "total_benes_presc": 80,
    "specialty": "Internal Medicine"
}
```

**Response**: Same as `/analyze_provider`

### 7.4 Search Endpoints

#### `GET /search_providers`
Search providers by NPI or name

**Authentication**: Required

**Query Parameters**:
- `q` (string): Search query

**Response**:
```json
{
    "results": [
        {
            "npi": "1234567890",
            "name": "Dr. John Doe",
            "specialty": "Internal Medicine",
            "risk_score": 0.85
        }
    ],
    "count": 1
}
```

### 7.5 Case Management Endpoints

#### `POST /cases/submit`
Submit case to supervisor

**Authentication**: Required (investigator role)

**Request Body**:
```json
{
    "npi": "1234567890",
    "provider_name": "Dr. John Doe",
    "notes": "High risk score, suspicious billing patterns"
}
```

**Response**:
```json
{
    "status": "success",
    "message": "Case submitted to supervisor"
}
```

#### `GET /api/cases/pending`
Get pending cases

**Authentication**: Required (supervisor role)

**Response**:
```json
[
    {
        "id": 1,
        "npi": "1234567890",
        "provider_name": "Dr. John Doe",
        "status": "PENDING",
        "submitted_by": "investigator",
        "timestamp": "2025-11-28T10:00:00"
    }
]
```

#### `POST /api/cases/decide`
Submit supervisor decision

**Authentication**: Required (supervisor role)

**Request Body**:
```json
{
    "case_id": 1,
    "decision": "STOP PAYMENT",
    "notes": "Clear evidence of upcoding and unbundling"
}
```

**Response**:
```json
{
    "status": "success",
    "message": "Decision recorded and email sent"
}
```

---

## 8. Deployment

### 8.1 Development Environment

#### Prerequisites
- Python 3.8+
- pip package manager
- 4GB+ RAM

#### Setup
```bash
# Clone repository
git clone <repo-url>
cd HealthCareFraudDetection-master

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Build artifacts
python build_artifacts.py

# Start development server
uvicorn api_server:app --reload
```

### 8.2 Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  fraudguard:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - RAW_DATA_PATH=/app/data
    volumes:
      - ./data:/app/data
      - ./models:/app/models
```

#### Deployment
```bash
docker-compose up -d
```

### 8.3 Production Deployment

#### Architecture
```
┌─────────────┐
│   Internet  │
└──────┬──────┘
       │
┌──────▼──────┐
│  Nginx      │ (Reverse Proxy, SSL/TLS)
└──────┬──────┘
       │
┌──────▼──────┐
│  Uvicorn    │ (4 workers)
│  FastAPI    │
└──────┬──────┘
       │
┌──────▼──────┐
│  SQLite     │ (or PostgreSQL for production)
└─────────────┘
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name fraudguard.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Systemd Service
```ini
[Unit]
Description=FraudGuard API Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/fraudguard
Environment="PATH=/opt/fraudguard/venv/bin"
ExecStart=/opt/fraudguard/venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

---

## 9. Security

### 9.1 Authentication
- Session-based authentication with HTTP-only cookies
- Secure random session ID generation (32-byte token)
- In-memory session storage (move to Redis for production)

### 9.2 Production Recommendations
- **HTTPS**: Use SSL/TLS certificates (Let's Encrypt)
- **Password Hashing**: Implement bcrypt or argon2
- **CSRF Protection**: Add CSRF tokens to forms
- **Rate Limiting**: Prevent brute-force attacks
- **Input Validation**: Strict Pydantic models
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: Template auto-escaping (Jinja2)

---

## 10. Performance

### 10.1 Optimization Strategies

#### Database
- Indexed NPI column for fast lookups
- Pre-computed risk scores
- Batch processing for monitor agent

#### Model Inference
- Feature store for pre-computed features
- Model caching in memory
- Batch predictions

#### Caching
- SHAP explainer cached per model version
- Specialty statistics cached
- KMeans model cached

### 10.2 Scalability

#### Horizontal Scaling
- Stateless API (can run multiple instances)
- Load balancer (Nginx/HAProxy)
- Shared database or distributed cache

#### Vertical Scaling
- Increase worker count (CPU-bound tasks)
- GPU acceleration for model inference
- Larger RAM for bigger datasets

---

## Appendix

### A. Environment Variables
```bash
GEMINI_API_KEY=your_api_key_here
RAW_DATA_PATH=data/raw_data
MODEL_PATH=saved_models/fraud_model.h5
SCALER_PATH=models/scaler.joblib
EXPLAINER_PATH=models/explainer.joblib
FEATURE_COLUMNS_PATH=models/feature_columns.json
FEATURE_STORE_PATH=data/provider_features.csv
```

### B. Configuration Reference
See [config.yaml](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/config.yaml) for complete configuration schema.

### C. Glossary
- **NPI**: National Provider Identifier
- **SHAP**: SHapley Additive exPlanations
- **LEIE**: List of Excluded Individuals/Entities
- **CMS**: Centers for Medicare & Medicaid Services
- **OIG**: Office of Inspector General
- **AUC**: Area Under Curve (ROC-AUC)
- **SMOTE**: Synthetic Minority Over-sampling Technique

---

*Document Version: 1.0*  
*Last Updated: 2025-11-28*  
*Author: Kalyan Uppuluri*
