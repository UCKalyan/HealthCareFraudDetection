# FraudGuard - System Architecture & Diagrams

## Table of Contents
1. [High-Level Architecture](#1-high-level-architecture)
2. [System Architecture](#2-system-architecture)
3. [Component Interaction](#3-component-interaction)
4. [Data Model Diagrams](#4-data-model-diagrams)
5. [Multi-Agent Flow](#5-multi-agent-flow)
6. [ML Pipeline](#6-ml-pipeline)
7. [CI/CD Pipeline](#7-cicd-pipeline)
8. [Deployment Architecture](#8-deployment-architecture)

---

## 1. High-Level Architecture

```mermaid
graph TB
    subgraph "User Layer"
        USER[👤 End User<br/>Fraud Investigator]
        BROWSER[🌐 Web Browser]
    end
    
    subgraph "Presentation Layer"
        UI[📊 Dashboard UI<br/>Jinja2 Templates]
        LOGIN[🔐 Login Page]
        REPORT[📄 Investigation Reports]
    end
    
    subgraph "Application Layer"
        API[⚡ FastAPI Server<br/>REST API]
        AUTH[🔑 Session Manager]
        ROUTER_DASH[Dashboard Router]
        ROUTER_INV[Investigation Router]
        ROUTER_SEARCH[Search Router]
    end
    
    subgraph "Agent Layer"
        WORKFLOW[🔄 LangGraph Workflow Engine]
        INV_AGENT[🕵️ Investigator<br/>Agent]
        ANA_AGENT[📊 Analyst<br/>Agent]
        SUP_AGENT[👨‍⚖️ Supervisor<br/>Agent]
        REP_AGENT[📝 Reporter<br/>Agent]
        MON_AGENT[📡 Monitor<br/>Agent]
    end
    
    subgraph "Service Layer"
        ML_MODEL[🧠 TensorFlow Model<br/>Deep Neural Network]
        SHAP_EXP[📈 SHAP Explainer<br/>XAI Service]
        NET_GRAPH[🕸️ Network Analysis<br/>PageRank]
        FEATURE_ENG[⚙️ Feature Engineering]
    end
    
    subgraph "Data Layer"
        SQLITE[💾 SQLite Database<br/>Providers, Cases, Feedback]
        FEATURE_STORE[📦 Feature Store<br/>Pre-computed Features]
        RAW_DATA[📁 Raw Data CSV<br/>Medicare Datasets]
        MODELS_STORE[🗃️ Model Artifacts<br/>Saved Models, Scalers]
    end
    
    subgraph "External Services"
        GEMINI[🤖 Google Gemini<br/>LLM API]
        CMS[📊 CMS Public Data<br/>Medicare Claims]
        OIG[⚠️ OIG LEIE<br/>Exclusion List]
    end
    
    USER --> BROWSER
    BROWSER --> LOGIN
    BROWSER --> UI
    BROWSER --> REPORT
    
    LOGIN --> AUTH
    UI --> API
    REPORT --> API
    
    API --> AUTH
    API --> ROUTER_DASH
    API --> ROUTER_INV
    API --> ROUTER_SEARCH
    
    ROUTER_INV --> WORKFLOW
    ROUTER_DASH --> MON_AGENT
    
    WORKFLOW --> INV_AGENT
    WORKFLOW --> ANA_AGENT
    WORKFLOW --> SUP_AGENT
    WORKFLOW --> REP_AGENT
    
    INV_AGENT --> FEATURE_ENG
    ANA_AGENT --> ML_MODEL
    ANA_AGENT --> SHAP_EXP
    ANA_AGENT --> GEMINI
    SUP_AGENT --> GEMINI
    REP_AGENT --> GEMINI
    MON_AGENT --> ML_MODEL
    
    ML_MODEL --> MODELS_STORE
    NET_GRAPH --> FEATURE_ENG
    FEATURE_ENG --> FEATURE_STORE
    
    SQLITE --> RAW_DATA
    FEATURE_STORE --> RAW_DATA
    
    RAW_DATA -.- CMS
    RAW_DATA -.- OIG
    
    style USER fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style BROWSER fill:#50C878,stroke:#2E7D4E,color:#fff
    style API fill:#FF6B6B,stroke:#C73E3A,color:#fff
    style WORKFLOW fill:#9B59B6,stroke:#6C3483,color:#fff
    style ML_MODEL fill:#F39C12,stroke:#B9770E,color:#fff
    style GEMINI fill:#E74C3C,stroke:#A93226,color:#fff
```

---

## 2. System Architecture

### 2.1 Detailed System Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend"
        direction LR
        DASHBOARD["Dashboard<br/>- Statistics<br/>- Provider Directory<br/>- Risk Distribution"]
        INV_REPORT["Investigation Report<br/>- SHAP Visualization<br/>- Risk Analysis<br/>- Agent Findings"]
        MANUAL_ANALYSIS["Manual Analysis<br/>- What-if Scenarios<br/>- Custom Profiles"]
    end
    
    subgraph "API Layer"
        direction TB
        FASTAPI["FastAPI Application"]
        MIDDLEWARE["Middleware<br/>- CORS<br/>- Logging<br/>- Error Handling"]
        SESSION["Session Management<br/>- Cookie-based Auth<br/>- User Roles"]
        
        FASTAPI --> MIDDLEWARE
        FASTAPI --> SESSION
    end
    
    subgraph "Router Layer"
        DASH_ROUTER["Dashboard Router<br/>/dashboard<br/>/dashboard_stats"]
        INV_ROUTER["Investigation Router<br/>/analyze_provider<br/>/analyze_new_provider"]
        SEARCH_ROUTER["Search Router<br/>/search_providers"]
        CASE_ROUTER["Case Router<br/>/cases/submit<br/>/cases/decide"]
    end
    
    subgraph "Business Logic"
        WORKFLOW_ENGINE["LangGraph Workflow<br/>- State Management<br/>- Agent Orchestration"]
        DEPS["Dependencies Module<br/>- ML Asset Loading<br/>- Config Management"]
    end
    
    subgraph "Agent System"
        direction LR
        AG1["Investigator<br/>Rule-based<br/>Detection"]
        AG2["Analyst<br/>ML Model<br/>SHAP Analysis"]
        AG3["Supervisor<br/>Decision<br/>Making"]
        AG4["Reporter<br/>Report<br/>Generation"]
        AG5["Monitor<br/>Background<br/>Scanning"]
    end
    
    subgraph "ML Services"
        MODEL_SVC["Model Service<br/>- Feature Extraction<br/>- Prediction<br/>- Batch Inference"]
        SHAP_SVC["Explainability Service<br/>- SHAP Calculation<br/>- Feature Importance<br/>- Visualization"]
        NETWORK_SVC["Network Service<br/>- Similarity Graph<br/>- PageRank<br/>- Peer Analysis"]
    end
    
    subgraph "Data Access"
        DB_CONN["Database Connection<br/>- SQLite Provider DB<br/>- Case Management<br/>- Feedback Store"]
        FEATURE_LOADER["Feature Loader<br/>- Pre-computed Features<br/>- Real-time Engineering<br/>- Caching"]
    end
    
    subgraph "Storage"
        direction LR
        DB[("SQLite<br/>Database")]
        CSV[("CSV<br/>Files")]
        MODELS[("Model<br/>Artifacts")]
    end
    
    DASHBOARD --> FASTAPI
    INV_REPORT --> FASTAPI
    MANUAL_ANALYSIS --> FASTAPI
    
    FASTAPI --> DASH_ROUTER
    FASTAPI --> INV_ROUTER
    FASTAPI --> SEARCH_ROUTER
    FASTAPI --> CASE_ROUTER
    
    DASH_ROUTER --> AG5
    INV_ROUTER --> WORKFLOW_ENGINE
    SEARCH_ROUTER --> DB_CONN
    CASE_ROUTER --> DB_CONN
    
    WORKFLOW_ENGINE --> AG1
    WORKFLOW_ENGINE --> AG2
    WORKFLOW_ENGINE --> AG3
    WORKFLOW_ENGINE --> AG4
    
    AG1 --> FEATURE_LOADER
    AG2 --> MODEL_SVC
    AG2 --> SHAP_SVC
    AG5 --> MODEL_SVC
    
    MODEL_SVC --> MODELS
    SHAP_SVC --> MODELS
    NETWORK_SVC --> FEATURE_LOADER
    
    FEATURE_LOADER --> CSV
    DB_CONN --> DB
    
    DEPS -.loads.-> MODELS
    DEPS -.configures.-> WORKFLOW_ENGINE
    
    style FASTAPI fill:#FF6B6B,stroke:#C73E3A,color:#fff
    style WORKFLOW_ENGINE fill:#9B59B6,stroke:#6C3483,color:#fff
    style MODEL_SVC fill:#F39C12,stroke:#B9770E,color:#fff
```

### 2.2 Request Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant FastAPI
    participant Auth
    participant Router
    participant LangGraph
    participant Investigator
    participant Analyst
    participant Supervisor
    participant Reporter
    participant MLModel
    participant SHAP
    participant Gemini
    participant Database
    
    User->>Browser: Enter NPI to analyze
    Browser->>FastAPI: POST /analyze_provider
    FastAPI->>Auth: Validate session
    Auth-->>FastAPI: Session valid
    FastAPI->>Router: Route to investigation
    Router->>LangGraph: Start workflow
    
    LangGraph->>Investigator: Initialize state
    Investigator->>Database: Fetch provider data
    Database-->>Investigator: Provider record
    Investigator->>Investigator: Rule-based checks
    Investigator-->>LangGraph: Red flags found
    
    LangGraph->>Analyst: Pass state
    Analyst->>MLModel: Predict risk
    MLModel-->>Analyst: Risk score: 0.85
    Analyst->>SHAP: Calculate explanations
    SHAP-->>Analyst: SHAP values
    Analyst->>Gemini: Interpret findings
    Gemini-->>Analyst: Technical analysis
    Analyst-->>LangGraph: Analysis complete
    
    LangGraph->>Supervisor: Pass state
    Supervisor->>Gemini: Make decision
    Gemini-->>Supervisor: Decision: HOLD PAYMENT
    Supervisor-->>LangGraph: Decision made
    
    LangGraph->>Reporter: Pass final state
    Reporter->>Gemini: Generate report
    Gemini-->>Reporter: HTML report
    Reporter-->>LangGraph: Report complete
    
    LangGraph-->>Router: Workflow finished
    Router-->>FastAPI: Return response
    FastAPI-->>Browser: JSON with report
    Browser-->>User: Display investigation report
```

---

## 3. Component Interaction

### 3.1 Component Dependency Graph

```mermaid
graph LR
    subgraph "Entry Points"
        MAIN[main.py<br/>Training Pipeline]
        API_SERVER[api_server.py<br/>Web Application]
        MCP_SERVER[mcp_server.py<br/>MCP Interface]
    end
    
    subgraph "Data Processing"
        LOADER[data_processing/<br/>loader.py]
        PREPROCESSOR[data_processing/<br/>preprocessor.py]
    end
    
    subgraph "Models"
        DNN[models/<br/>adaptive_deep_model.py]
    end
    
    subgraph "Training"
        TRAIN[training/<br/>train.py]
        RETRAIN[training/<br/>retrain_from_feedback.py]
    end
    
    subgraph "Explainability"
        SHAP_ANALYZER[explainability/<br/>shap_analyzer.py]
        EXPLAINER[explainability/<br/>explainer.py]
    end
    
    subgraph "Agents"
        BASE_AGENT[agents/<br/>base_agent.py]
        INVESTIGATOR[agents/<br/>investigator.py]
        ANALYST[agents/<br/>analyst.py]
        SUPERVISOR[agents/<br/>supervisor.py]
        REPORTER[agents/<br/>reporter.py]
        MONITOR[agents/<br/>monitor.py]
    end
    
    subgraph "Workflows"
        FRAUD_GRAPH[workflows/<br/>fraud_graph.py]
    end
    
    subgraph "Routers"
        DASH_R[routers/<br/>dashboard.py]
        INV_R[routers/<br/>investigation.py]
        SEARCH_R[routers/<br/>search.py]
    end
    
    subgraph "Utils"
        CONFIG[utils/<br/>config_loader.py]
        EVAL[utils/<br/>evaluation.py]
        NOTIF[utils/<br/>notifications.py]
    end
    
    subgraph "Infrastructure"
        DB[database.py]
        DEPS[dependencies.py]
        SCHEMAS[schemas.py]
    end
    
    MAIN --> CONFIG
    MAIN --> LOADER
    MAIN --> PREPROCESSOR
    MAIN --> DNN
    MAIN --> TRAIN
    MAIN --> EVAL
    MAIN --> SHAP_ANALYZER
    
    API_SERVER --> DEPS
    API_SERVER --> DASH_R
    API_SERVER --> INV_R
    API_SERVER --> SEARCH_R
    API_SERVER --> DB
    API_SERVER --> SCHEMAS
    API_SERVER --> NOTIF
    
    DEPS --> CONFIG
    DEPS --> DNN
    DEPS --> EXPLAINER
    DEPS --> DB
    
    INV_R --> FRAUD_GRAPH
    INV_R --> SCHEMAS
    
    FRAUD_GRAPH --> INVESTIGATOR
    FRAUD_GRAPH --> ANALYST
    FRAUD_GRAPH --> SUPERVISOR
    FRAUD_GRAPH --> REPORTER
    
    INVESTIGATOR --> BASE_AGENT
    ANALYST --> BASE_AGENT
    SUPERVISOR --> BASE_AGENT
    REPORTER --> BASE_AGENT
    MONITOR --> BASE_AGENT
    
    ANALYST --> SHAP_ANALYZER
    
    DASH_R --> MONITOR
    DASH_R --> DB
    
    LOADER --> CONFIG
    PREPROCESSOR --> CONFIG
    TRAIN --> CONFIG
    
    style MAIN fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style API_SERVER fill:#FF6B6B,stroke:#C73E3A,color:#fff
    style FRAUD_GRAPH fill:#9B59B6,stroke:#6C3483,color:#fff
    style DNN fill:#F39C12,stroke:#B9770E,color:#fff
```

---

## 4. Data Model Diagrams

### 4.1 ER Diagram - Physician Dataset

```mermaid
erDiagram
    PHYSICIAN_DATA {
        int Rndrng_NPI PK "National Provider Identifier"
        string Rndrng_Prvdr_First_Name "First Name"
        string Rndrng_Prvdr_Last_Name "Last Name"
        string Rndrng_Prvdr_Type "Provider Specialty"
        string Rndrng_Prvdr_State_Abrvtn "State"
        string Rndrng_Prvdr_City "City"
        string Rndrng_Prvdr_Gndr "Gender"
        int Tot_Srvcs "Total Services"
        int Tot_Benes "Total Beneficiaries"
        float Avg_Sbmtd_Chrg "Average Submitted Charge"
        float Avg_Mdcr_Alowd_Amt "Average Medicare Allowed"
        float Avg_Mdcr_Pymt_Amt "Average Medicare Payment"
        int Tot_Bene_Day_Srvcs "Total Beneficiary Day Services"
    }
    
    SPECIALTY_STATS {
        string specialty PK "Provider Specialty"
        float cps_mean "Cost Per Service Mean"
        float cps_std "Cost Per Service Std Dev"
        float spb_mean "Services Per Bene Mean"
        float spb_std "Services Per Bene Std Dev"
        int provider_count "Number of Providers"
    }
    
    PHYSICIAN_DATA ||--o{ SPECIALTY_STATS : "belongs_to_specialty"
```

### 4.2 ER Diagram - Prescriber Dataset

```mermaid
erDiagram
    PRESCRIBER_DATA {
        int PRSCRBR_NPI PK "National Provider Identifier"
        string Prscrbr_First_Name "First Name"
        string Prscrbr_Last_Name "Last Name"
        string Prscrbr_Type "Prescriber Specialty"
        string Prscrbr_State_Abrvtn "State"
        string Prscrbr_City "City"
        string Prscrbr_Gndr "Gender"
        int Tot_Clms "Total Claims"
        int Tot_Benes "Total Beneficiaries"
        float Tot_Drug_Cst "Total Drug Cost"
        int Tot_Day_Suply "Total Day Supply"
        int Opioid_Clm_Cnt "Opioid Claim Count"
        int Antbtc_Clm_Cnt "Antibiotic Claim Count"
    }
    
    DRUG_CATEGORIES {
        string category PK "Drug Category"
        string description "Category Description"
        float avg_cost "Average Cost"
    }
    
    PRESCRIBER_DATA ||--o{ DRUG_CATEGORIES : "prescribes"
```

### 4.3 ER Diagram - LEIE Dataset

```mermaid
erDiagram
    LEIE_EXCLUSIONS {
        int NPI PK "National Provider Identifier"
        string LASTNAME "Last Name"
        string FIRSTNAME "First Name"
        string MIDNAME "Middle Name"
        string BUSNAME "Business Name"
        string GENERAL "General Type"
        string SPECIALTY "Specialty"
        string EXCLTYPE "Exclusion Type"
        date EXCLDATE "Exclusion Date"
        date REINDATE "Reinstatement Date"
        string WAIVERSTATE "Waiver State"
    }
    
    EXCLUSION_TYPES {
        string code PK "Exclusion Type Code"
        string description "Description"
        string severity "Severity Level"
    }
    
    LEIE_EXCLUSIONS ||--o{ EXCLUSION_TYPES : "has_type"
```

### 4.4 Application Database Schema

```mermaid
erDiagram
    PROVIDERS {
        string npi PK "National Provider Identifier"
        string name "Provider Name"
        string specialty "Medical Specialty"
        string city "City"
        string state "State Code"
        float risk_score "Fraud Risk Score (0-1)"
        string risk_level "Risk Level (HIGH/MEDIUM/LOW)"
        text features_json "Serialized Features"
        datetime last_analyzed "Last Analysis Timestamp"
        string model_version "Model Version Used"
    }
    
    FEEDBACK {
        int id PK "Feedback ID"
        string npi FK "Provider NPI"
        string username "Investigator Username"
        string action "Action (CONFIRM_FRAUD/CONFIRM_CLEAN)"
        datetime timestamp "Submission Time"
        text notes "Optional Notes"
    }
    
    CASES {
        int id PK "Case ID"
        string npi FK "Provider NPI"
        string provider_name "Provider Name"
        string status "Status (PENDING/REVIEWED)"
        string submitted_by "Investigator Username"
        string decision "Supervisor Decision"
        text notes "Case Notes"
        datetime timestamp "Submission Time"
    }
    
    USERS {
        string username PK "Username"
        string password_hash "Hashed Password"
        string role "User Role (admin/investigator/supervisor)"
        datetime created_at "Account Creation"
    }
    
    PROVIDERS ||--o{ FEEDBACK : "receives_feedback"
    PROVIDERS ||--o{ CASES : "has_cases"
    USERS ||--o{ FEEDBACK : "submits"
    USERS ||--o{ CASES : "creates"
```

### 4.5 Feature Engineering Data Flow

```mermaid
graph TB
    subgraph "Source Data"
        PHYS_CSV["Physician CSV<br/>PHY_R25"]
        PRESC_CSV["Prescriber CSV<br/>DPR_RY25"]
        LEIE_CSV["LEIE CSV<br/>Exclusions"]
    end
    
    subgraph "Data Merging"
        MERGE["Inner Join on NPI<br/>Combined Dataset"]
    end
    
    subgraph "Base Features"
        BF1["cost_per_service<br/>= Avg_Sbmtd_Chrg"]
        BF2["services_per_bene<br/>= Tot_Srvcs / Tot_Benes"]
        BF3["cost_per_bene_phys<br/>= Total Cost / Tot_Benes"]
        BF4["scripts_per_bene<br/>= Tot_Clms / Tot_Benes"]
        BF5["drug_cost_per_script<br/>= Tot_Drug_Cst / Tot_Clms"]
        BF6["cost_per_bene_presc<br/>= Tot_Drug_Cst / Tot_Benes"]
    end
    
    subgraph "Normalization"
        STATS["Specialty Statistics<br/>Group by specialty<br/>Calculate mean & std"]
        ZSCORE["Z-Score Calculation<br/>z = (x - μ) / σ"]
        TANH["Tanh Transform<br/>z_tanh = tanh(z)<br/>Range: [-1, 1]"]
    end
    
    subgraph "Clustering"
        KMEANS["K-Means Clustering<br/>n_clusters = 5<br/>Features: cps, spb"]
        ONEHOT["One-Hot Encoding<br/>5 binary features:<br/>cluster_0..cluster_4"]
    end
    
    subgraph "Graph Features"
        SIMILARITY["Cosine Similarity<br/>Based on cps, spb"]
        GRAPH["Build Network<br/>threshold = 0.95<br/>top_k = 5"]
        PAGERANK["PageRank Centrality<br/>Network influence score"]
    end
    
    subgraph "Labeling"
        LABEL_LEIE["Supervised: LEIE match"]
        LABEL_UNSUP["Unsupervised:<br/>combined_z > 3.0"]
    end
    
    subgraph "Final Features"
        FEATURE_VEC["Feature Vector (11-dim)<br/>cps_z_tanh<br/>spb_z_tanh<br/>cpb_phys_z_tanh<br/>dcp_z_tanh<br/>cpb_presc_z_tanh<br/>cluster_0..cluster_4<br/>pagerank_centrality"]
    end
    
    PHYS_CSV --> MERGE
    PRESC_CSV --> MERGE
    
    MERGE --> BF1
    MERGE --> BF2
    MERGE --> BF3
    MERGE --> BF4
    MERGE --> BF5
    MERGE --> BF6
    
    BF1 --> STATS
    BF2 --> STATS
    BF3 --> STATS
    BF4 --> STATS
    BF5 --> STATS
    BF6 --> STATS
    
    STATS --> ZSCORE
    ZSCORE --> TANH
    
    BF1 --> KMEANS
    BF2 --> KMEANS
    KMEANS --> ONEHOT
    
    BF1 --> SIMILARITY
    BF2 --> SIMILARITY
    SIMILARITY --> GRAPH
    GRAPH --> PAGERANK
    
    LEIE_CSV --> LABEL_LEIE
    TANH --> LABEL_UNSUP
    
    TANH --> FEATURE_VEC
    ONEHOT --> FEATURE_VEC
    PAGERANK --> FEATURE_VEC
    
    style MERGE fill:#3498DB,stroke:#2874A6,color:#fff
    style FEATURE_VEC fill:#E74C3C,stroke:#A93226,color:#fff
```

---

## 5. Multi-Agent Flow

### 5.1 LangGraph Workflow Diagram

```mermaid
graph TB
    START([Start Analysis]) --> INIT[Initialize State<br/>NPI, ML Assets]
    
    INIT --> INV_NODE[Investigator Node]
    
    subgraph "Investigator Agent"
        INV_NODE --> INV_FETCH[Fetch Provider Data]
        INV_FETCH --> INV_CHECK[Rule-Based Checks]
        INV_CHECK --> INV_FLAGS{Red Flags<br/>Found?}
        INV_FLAGS -->|Yes| INV_REPORT[Generate Alert Report]
        INV_FLAGS -->|No| INV_NORMAL[Normal Profile]
        INV_REPORT --> INV_OUT[Update State:<br/>investigator_finding]
        INV_NORMAL --> INV_OUT
    end
    
    INV_OUT --> ANA_NODE[Analyst Node]
    
    subgraph "Analyst Agent"
        ANA_NODE --> ANA_FEAT[Extract Features]
        ANA_FEAT --> ANA_PRED[ML Model Prediction]
        ANA_PRED --> ANA_SHAP[Calculate SHAP Values]
        ANA_SHAP --> ANA_LLM[LLM Interpretation<br/>Gemini API]
        ANA_LLM --> ANA_OUT[Update State:<br/>risk_score, shap_values,<br/>analyst_finding]
    end
    
    ANA_OUT --> SUP_NODE[Supervisor Node]
    
    subgraph "Supervisor Agent"
        SUP_NODE --> SUP_REVIEW[Review Findings]
        SUP_REVIEW --> SUP_DECIDE{Risk Score<br/>Analysis}
        SUP_DECIDE -->|>0.9| SUP_STOP[Decision: STOP PAYMENT]
        SUP_DECIDE -->|0.7-0.9| SUP_HOLD[Decision: HOLD PAYMENT]
        SUP_DECIDE -->|0.5-0.7| SUP_REVIEW_DEC[Decision: REVIEW]
        SUP_DECIDE -->|<0.5| SUP_RELEASE[Decision: RELEASE]
        SUP_STOP --> SUP_LLM[LLM Reasoning<br/>Gemini API]
        SUP_HOLD --> SUP_LLM
        SUP_REVIEW_DEC --> SUP_LLM
        SUP_RELEASE --> SUP_LLM
        SUP_LLM --> SUP_OUT[Update State:<br/>supervisor_decision]
    end
    
    SUP_OUT --> REP_NODE[Reporter Node]
    
    subgraph "Reporter Agent"
        REP_NODE --> REP_SYNTH[Synthesize All Findings]
        REP_SYNTH --> REP_LLM[Generate HTML Report<br/>Gemini API]
        REP_LLM --> REP_VIZ[Add SHAP Visualization]
        REP_VIZ --> REP_OUT[Update State:<br/>final_report]
    end
    
    REP_OUT --> END([End Workflow])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style INV_NODE fill:#3498DB,stroke:#2980B9,color:#fff
    style ANA_NODE fill:#9B59B6,stroke:#8E44AD,color:#fff
    style SUP_NODE fill:#F39C12,stroke:#E67E22,color:#fff
    style REP_NODE fill:#1ABC9C,stroke:#16A085,color:#fff
```

### 5.2 Agent State Transitions

```mermaid
stateDiagram-v2
    [*] --> Initialized
    Initialized --> InvestigatorActive : start_workflow()
    
    InvestigatorActive --> InvestigatorComplete : complete_investigation()
    
    InvestigatorComplete --> AnalystActive : pass_state()
    
    AnalystActive --> ModelPrediction : extract_features()
    ModelPrediction --> SHAPCalculation : predict_risk()
    SHAPCalculation --> LLMInterpretation : calculate_shap()
    LLMInterpretation --> AnalystComplete : interpret()
    
    AnalystComplete --> SupervisorActive : pass_state()
    
    SupervisorActive --> DecisionMaking : review_findings()
    DecisionMaking --> StopPayment : risk > 0.9
    DecisionMaking --> HoldPayment : risk > 0.7
    DecisionMaking --> ReviewCase : risk > 0.5
    DecisionMaking --> ReleasePayment : risk < 0.5
    
    StopPayment --> SupervisorComplete
    HoldPayment --> SupervisorComplete
    ReviewCase --> SupervisorComplete
    ReleasePayment --> SupervisorComplete
    
    SupervisorComplete --> ReporterActive : pass_state()
    
    ReporterActive --> ReportGeneration : synthesize()
    ReportGeneration --> ReporterComplete : generate_html()
    
    ReporterComplete --> [*]
    
    note right of ModelPrediction
        Risk score calculated
        using TensorFlow model
    end note
    
    note right of SHAPCalculation
        Feature importance
        explanations generated
    end note
    
    note right of DecisionMaking
        Final payment decision
        based on risk threshold
    end note
```

### 5.3 Individual Agent Flows

#### Investigator Agent Flow

```mermaid
flowchart TD
    START([Start Investigator]) --> LOAD_DATA[Load Provider Data<br/>from Database]
    LOAD_DATA --> CALC_FEATURES[Calculate Base Features<br/>cost_per_service<br/>services_per_bene]
    
    CALC_FEATURES --> CHECK1{Cost per<br/>service > $200?}
    CHECK1 -->|Yes| FLAG1[Add Flag: High Cost]
    CHECK1 -->|No| CHECK2
    FLAG1 --> CHECK2
    
    CHECK2{Services per<br/>bene > 50?}
    CHECK2 -->|Yes| FLAG2[Add Flag: High Volume]
    CHECK2 -->|No| CHECK3
    FLAG2 --> CHECK3
    
    CHECK3{PageRank<br/>centrality > 0.01?}
    CHECK3 -->|Yes| FLAG3[Add Flag: Highly Connected]
    CHECK3 -->|No| SUMMARIZE
    FLAG3 --> SUMMARIZE
    
    SUMMARIZE[Summarize Provider Profile] --> GEN_REPORT[Generate Finding Report]
    GEN_REPORT --> UPDATE_STATE[Update State:<br/>investigator_finding<br/>red_flags]
    UPDATE_STATE --> END([End Investigator])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style FLAG1 fill:#F39C12,stroke:#E67E22,color:#fff
    style FLAG2 fill:#F39C12,stroke:#E67E22,color:#fff
    style FLAG3 fill:#F39C12,stroke:#E67E22,color:#fff
```

#### Analyst Agent Flow

```mermaid
flowchart TD
    START([Start Analyst]) --> LOAD_ASSETS[Load ML Assets<br/>Model, Scaler, Explainer]
    LOAD_ASSETS --> EXTRACT[Extract Features<br/>11-dimensional vector]
    
    EXTRACT --> SCALE[Scale Features<br/>RobustScaler]
    SCALE --> PREDICT[Model Prediction<br/>TensorFlow DNN]
    
    PREDICT --> RISK_SCORE[Risk Score: 0.0-1.0]
    RISK_SCORE --> CLASSIFY{Classify<br/>Risk Level}
    
    CLASSIFY -->|>0.7| HIGH[Risk Level: HIGH]
    CLASSIFY -->|0.4-0.7| MEDIUM[Risk Level: MEDIUM]
    CLASSIFY -->|<0.4| LOW[Risk Level: LOW]
    
    HIGH --> SHAP_CALC
    MEDIUM --> SHAP_CALC
    LOW --> SHAP_CALC
    
    SHAP_CALC[Calculate SHAP Values<br/>Feature Importance]
    SHAP_CALC --> FORMAT[Format SHAP Explanation<br/>Top Contributing Features]
    
    FORMAT --> LLM_PROMPT[Create LLM Prompt<br/>with SHAP analysis]
    LLM_PROMPT --> CALL_LLM[Call Gemini API<br/>Technical Interpretation]
    
    CALL_LLM --> RETRY{API<br/>Success?}
    RETRY -->|No, 429| BACKOFF[Exponential Backoff<br/>Wait & Retry]
    BACKOFF --> CALL_LLM
    RETRY -->|Yes| PARSE[Parse LLM Response]
    
    PARSE --> UPDATE[Update State:<br/>risk_score, risk_level<br/>shap_values, analyst_finding]
    UPDATE --> END([End Analyst])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style HIGH fill:#E74C3C,stroke:#C0392B,color:#fff
    style MEDIUM fill:#F39C12,stroke:#E67E22,color:#fff
    style LOW fill:#2ECC71,stroke:#27AE60,color:#fff
    style CALL_LLM fill:#9B59B6,stroke:#8E44AD,color:#fff
```

#### Supervisor Agent Flow

```mermaid
flowchart TD
    START([Start Supervisor]) --> REVIEW[Review All Findings<br/>Investigator + Analyst]
    
    REVIEW --> ANALYZE_RISK{Analyze<br/>Risk Score}
    
    ANALYZE_RISK -->|>0.9| DECISION_STOP[Decision: STOP PAYMENT<br/>Confidence: High]
    ANALYZE_RISK -->|0.7-0.9| DECISION_HOLD[Decision: HOLD PAYMENT<br/>Confidence: Medium]
    ANALYZE_RISK -->|0.5-0.7| DECISION_REVIEW[Decision: REVIEW<br/>Confidence: Medium]
    ANALYZE_RISK -->|<0.5| DECISION_RELEASE[Decision: RELEASE PAYMENT<br/>Confidence: High]
    
    DECISION_STOP --> PROMPT_STOP[Create LLM Prompt<br/>for STOP reasoning]
    DECISION_HOLD --> PROMPT_HOLD[Create LLM Prompt<br/>for HOLD reasoning]
    DECISION_REVIEW --> PROMPT_REVIEW[Create LLM Prompt<br/>for REVIEW reasoning]
    DECISION_RELEASE --> PROMPT_RELEASE[Create LLM Prompt<br/>for RELEASE reasoning]
    
    PROMPT_STOP --> CALL_LLM[Call Gemini API<br/>Generate Reasoning]
    PROMPT_HOLD --> CALL_LLM
    PROMPT_REVIEW --> CALL_LLM
    PROMPT_RELEASE --> CALL_LLM
    
    CALL_LLM --> FORMAT_DECISION[Format Decision Report<br/>Decision + Confidence + Reasoning]
    
    FORMAT_DECISION --> UPDATE[Update State:<br/>supervisor_decision]
    UPDATE --> END([End Supervisor])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style DECISION_STOP fill:#E74C3C,stroke:#C0392B,color:#fff
    style DECISION_HOLD fill:#F39C12,stroke:#E67E22,color:#fff
    style DECISION_REVIEW fill:#F1C40F,stroke:#F39C12,color:#000
    style DECISION_RELEASE fill:#2ECC71,stroke:#27AE60,color:#fff
    style CALL_LLM fill:#9B59B6,stroke:#8E44AD,color:#fff
```

#### Reporter Agent Flow

```mermaid
flowchart TD
    START([Start Reporter]) --> GATHER[Gather All State Data<br/>Investigator, Analyst, Supervisor]
    
    GATHER --> SYNTH[Synthesize Findings<br/>Combine all reports]
    
    SYNTH --> CREATE_PROMPT[Create Reporter Prompt<br/>Structured template]
    CREATE_PROMPT --> SECTIONS[Define Report Sections<br/>- Executive Summary<br/>- Risk Profile<br/>- Model Insights<br/>- Recommendations]
    
    SECTIONS --> CALL_LLM[Call Gemini API<br/>Generate HTML Report]
    
    CALL_LLM --> PARSE_HTML[Parse HTML Response]
    
    PARSE_HTML --> ADD_SHAP[Add SHAP Visualization<br/>Waterfall Chart]
    ADD_SHAP --> ADD_FEATURES[Add Raw Feature Data<br/>Table with metrics]
    ADD_FEATURES --> ADD_STYLE[Add CSS Styling<br/>Professional formatting]
    
    ADD_STYLE --> VALIDATE[Validate HTML<br/>Ensure completeness]
    
    VALIDATE --> UPDATE[Update State:<br/>final_report (HTML)]
    UPDATE --> END([End Reporter])
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style END fill:#E74C3C,stroke:#C0392B,color:#fff
    style CALL_LLM fill:#9B59B6,stroke:#8E44AD,color:#fff
    style ADD_SHAP fill:#3498DB,stroke:#2980B9,color:#fff
```

#### Monitor Agent Flow

```mermaid
flowchart TD
    START([Start Monitor Loop]) --> LOAD_STATE[Load Monitor State<br/>offset, stats]
    
    LOAD_STATE --> GET_BATCH[Get Provider Batch<br/>offset to offset+100]
    
    GET_BATCH --> HAS_DATA{Providers<br/>available?}
    HAS_DATA -->|No| RESET[Reset offset to 0<br/>Start new scan cycle]
    RESET --> GET_BATCH
    
    HAS_DATA -->|Yes| PROCESS_LOOP[For each provider in batch]
    
    PROCESS_LOOP --> EXTRACT_FEAT[Extract Features]
    EXTRACT_FEAT --> PREDICT[Predict Risk Score<br/>ML Model]
    
    PREDICT --> UPDATE_DB[Update Database<br/>risk_score, risk_level]
    
    UPDATE_DB --> NEXT{More in<br/>batch?}
    NEXT -->|Yes| PROCESS_LOOP
    NEXT -->|No| CALC_STATS[Calculate Statistics<br/>total, high_risk_count, avg_risk]
    
    CALC_STATS --> SAVE_STATS[Save Statistics<br/>to JSON]
    
    SAVE_STATS --> UPDATE_STATE[Update Monitor State<br/>offset += 100]
    
    UPDATE_STATE --> SLEEP[Sleep 60 seconds]
    SLEEP --> GET_BATCH
    
    style START fill:#2ECC71,stroke:#27AE60,color:#fff
    style PROCESS_LOOP fill:#3498DB,stroke:#2980B9,color:#fff
    style SLEEP fill:#95A5A6,stroke:#7F8C8D,color:#fff
```

(Continue in next message due to length...)
