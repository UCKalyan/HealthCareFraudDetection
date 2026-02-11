# System Architecture

## 1. High-Level Overview

FraudGuard is designed as a modular, multi-agent system. It separates data processing, model training, and the user-facing application into distinct layers.

```mermaid
graph TD
    subgraph "Data Layer"
        Raw[Raw CSV Data] --> Loader[Data Loader]
        Loader --> Pre[Preprocessor]
        LEIE[LEIE Labels] --> Pre
    end

    subgraph "Model Layer"
        Pre -->|Features| SMOTE[SMOTE Balancing]
        SMOTE --> Train[Training Pipeline]
        Train --> Model[Deep Learning Model]
        Train --> Explainer[SHAP Explainer]
    end

    subgraph "Application Layer"
        Model --> API[FastAPI Server]
        Explainer --> API
        API --> Agents[AI Agents]
        Agents --> UI[Web Dashboard]
    end

    subgraph "Agentic Layer"
        UI --> Investigator[Investigator Agent]
        Investigator --> Analyst[Analyst Agent]
        Analyst --> Supervisor[Supervisor Agent]
        Supervisor --> Reporter[Reporter Agent]
        Reporter --> Report[Final Report]
    end
```

## 2. Data Entity-Relationship (ER) Diagram

The system integrates three primary datasets using the **National Provider Identifier (NPI)** as the primary key.

```mermaid
erDiagram
    MEDICARE_PART_B ||--o{ PROVIDER : "identifies"
    MEDICARE_PART_D ||--o{ PROVIDER : "identifies"
    LEIE_EXCLUSIONS |o--|| PROVIDER : "labels"

    PROVIDER {
        string provider_id PK "NPI"
        string specialty "Coalesced Specialty"
        string first_name
        string org_name
        boolean has_part_b
        boolean has_part_d
    }

    MEDICARE_PART_B {
        string Rndrng_NPI FK
        string HCPCS_Cd "Procedure Code"
        string Place_Of_Srvc
        float Tot_Srvcs
        float Avg_Sbmtd_Chrg
    }

    MEDICARE_PART_D {
        string PRSCRBR_NPI FK
        float Tot_Drug_Cst
        float Tot_Clms
        float Tot_Benes
    }

    LEIE_EXCLUSIONS {
        string NPI FK
        string EXCLTYPE
        date EXCLDATE
    }
```

## 3. Component Details

### 3.1 Data Processing
- **Loader:** Handles CSV ingestion and encoding issues.
- **Preprocessor:** Performs outer joins, coalesces missing data, and generates advanced features (PageRank, Archetypes).

### 3.2 AI Agents
- **Investigator:** Rule-based checks (e.g., cost thresholds).
- **Analyst:** Runs the Deep Learning model and interprets SHAP values.
- **Supervisor:** Reviews findings and makes payment decisions (Stop/Hold/Release).
- **Reporter:** Synthesizes findings into human-readable HTML reports using LLMs.
- **Monitor:** Background task that scans the database for new anomalies.

### 3.3 Backend API
- **FastAPI:** Provides REST endpoints for the UI and MCP server.
- **Authentication:** Session-based login with secure cookie handling.

### 3.4 MCP Server
- Exposes internal tools (`predict_fraud`, `explain_fraud`) to external AI assistants via the Model Context Protocol.
