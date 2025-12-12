# FraudGuard - Documentation Index

Welcome to the FraudGuard Healthcare Fraud Detection System documentation. This directory contains comprehensive technical documentation, architecture diagrams, and system design specifications.

## 📚 Documentation Structure

### Core Documentation

#### 1. [Technical Documentation](./TECHNICAL_DOCUMENTATION.md)
Comprehensive technical guide covering:
- Project overview and objectives
- System architecture (layered architecture with diagrams)
- Technology stack details
- Data models and schema
- Machine learning pipeline
- Multi-agent system architecture
- API reference (all endpoints)
- Deployment strategies
- Security best practices
- Performance optimization

**Target Audience**: Developers, System Architects, DevOps Engineers

---

#### 2. [Architecture Diagrams](./ARCHITECTURE_DIAGRAMS.md)
Visual system design documentation including:
- **High-Level Architecture**: Complete system overview with all layers
- **System Architecture**: Detailed component interaction diagrams
- **Component Dependencies**: Module dependency graphs
- **Data Model Diagrams**: ER diagrams for all 3 datasets
  - Physician Dataset (Medicare Part B)
  - Prescriber Dataset (Medicare Part D)
  - LEIE Exclusion List
  - Application Database Schema
- **Feature Engineering Data Flow**: Complete feature pipeline
- **Multi-Agent Flow Diagrams**: 
  - LangGraph workflow orchestration
  - Agent state transitions
  - Individual agent flows (Investigator, Analyst, Supervisor, Reporter, Monitor)
- **Request Flow Sequences**: End-to-end request processing

**Target Audience**: System Architects, Technical Leads, Stakeholders

---

#### 3. [ML Pipeline & Algorithms](./ML_PIPELINE_ALGORITHMS.md)
Machine learning and algorithm documentation:
- **Training Pipeline**: Complete ML training workflow
  - Data loading and merging
  - Feature engineering (11-dimensional feature vector)
  - Model architecture (Deep Neural Network)
  - Training process with SMOTE and focal loss
  - Evaluation metrics
- **Inference Pipeline**: Real-time and batch prediction flows
- **Model Architecture**: Detailed DNN layer specifications
- **Algorithm Diagrams**:
  - Risk calculation algorithm
  - SHAP explanation algorithm (Shapley values)
  - Network analysis (PageRank centrality)
  - K-Means clustering (provider archetypes)
  - Anomaly detection (rule-based)
- **CI/CD Pipelines**: 
  - Continuous Integration workflow
  - Continuous Deployment workflow
  - Model retraining pipeline (MLOps)
- **Deployment Workflows**: Docker and production architectures

**Target Audience**: Data Scientists, ML Engineers, DevOps

---

#### 4. [Implementation Plan](./implementation_plan.md)
Detailed roadmap and implementation status for system features:
- Payment Control & Recovery System
- Nested Learning Architecture
- Database Schema Extensions
- UI/UX Improvements

**Target Audience**: Project Managers, Developers, Stakeholders

---

#### 5. [Walkthrough](./walkthrough.md)
Comprehensive guide to implemented features:
- Feature demonstrations
- Verification steps
- System architecture updates
- Usage instructions for new capabilities

**Target Audience**: Users, Testers, Developers

---

## 🗂️ Quick Reference

### System Components

| Component | Description | Documentation |
|-----------|-------------|---------------|
| **Web Application** | FastAPI-based REST API server | [Technical Docs](./TECHNICAL_DOCUMENTATION.md#7-api-reference) |
| **Multi-Agent System** | LangGraph orchestrated AI agents | [Architecture](./ARCHITECTURE_DIAGRAMS.md#5-multi-agent-flow) |
| **ML Model** | Deep Neural Network for fraud detection | [ML Pipeline](./ML_PIPELINE_ALGORITHMS.md#3-model-architecture) |
| **SHAP Explainer** | Feature importance and explainability | [Algorithms](./ML_PIPELINE_ALGORITHMS.md#42-shap-explanation-algorithm) |
| **Monitor Agent** | Background database scanning | [Agent Flow](./ARCHITECTURE_DIAGRAMS.md#53-individual-agent-flows) |
| **Database** | SQLite provider, case, and feedback storage | [Data Models](./ARCHITECTURE_DIAGRAMS.md#4-data-model-diagrams) |

### Key Diagrams

| Diagram | Type | Location |
|---------|------|----------|
| High-Level Architecture | Mermaid | [Architecture Diagrams](./ARCHITECTURE_DIAGRAMS.md#1-high-level-architecture) |
| ER Diagrams (3 datasets) | Mermaid | [Architecture Diagrams](./ARCHITECTURE_DIAGRAMS.md#4-data-model-diagrams) |
| LangGraph Workflow | Mermaid | [Architecture Diagrams](./ARCHITECTURE_DIAGRAMS.md#51-langgraph-workflow-diagram) |
| Training Pipeline | Mermaid | [ML Pipeline](./ML_PIPELINE_ALGORITHMS.md#11-complete-training-workflow) |
| Feature Engineering | Mermaid | [ML Pipeline](./ML_PIPELINE_ALGORITHMS.md#12-feature-engineering-detail) |
| Risk Calculation Algorithm | Mermaid | [Algorithms](./ML_PIPELINE_ALGORITHMS.md#41-risk-calculation-algorithm) |
| CI/CD Pipeline | Mermaid | [ML Pipeline](./ML_PIPELINE_ALGORITHMS.md#51-continuous-integration-workflow) |
| Agent State Transitions | Mermaid | [Architecture Diagrams](./ARCHITECTURE_DIAGRAMS.md#52-agent-state-transitions) |

### API Endpoints Quick Guide

| Endpoint | Method | Purpose | Details |
|----------|--------|---------|---------|
| `/login` | POST | User authentication | [API Ref](./TECHNICAL_DOCUMENTATION.md#71-authentication-endpoints) |
| `/dashboard` | GET | Main application UI | [API Ref](./TECHNICAL_DOCUMENTATION.md#72-dashboard-endpoints) |
| `/analyze_provider` | POST | Analyze provider by NPI | [API Ref](./TECHNICAL_DOCUMENTATION.md#73-provider-endpoints) |
| `/providers` | GET | Get provider directory | [API Ref](./TECHNICAL_DOCUMENTATION.md#73-provider-endpoints) |
| `/cases/submit` | POST | Submit case to supervisor | [API Ref](./TECHNICAL_DOCUMENTATION.md#75-case-management-endpoints) |

---

## 🎯 Use Cases by Role

### For Developers
1. Start with [Technical Documentation](./TECHNICAL_DOCUMENTATION.md) for system overview
2. Review [Component Dependencies](./ARCHITECTURE_DIAGRAMS.md#31-component-dependency-graph) to understand module structure
3. Check [API Reference](./TECHNICAL_DOCUMENTATION.md#7-api-reference) for endpoint specifications
4. Study [Request Flow](./ARCHITECTURE_DIAGRAMS.md#22-request-flow-diagram) for debugging

### For Data Scientists
1. Begin with [ML Training Pipeline](./ML_PIPELINE_ALGORITHMS.md#1-ml-training-pipeline)
2. Understand [Feature Engineering](./ML_PIPELINE_ALGORITHMS.md#12-feature-engineering-detail)
3. Review [Model Architecture](./ML_PIPELINE_ALGORITHMS.md#3-model-architecture)
4. Study [SHAP Algorithm](./ML_PIPELINE_ALGORITHMS.md#42-shap-explanation-algorithm) for explainability

### For System Architects
1. Start with [High-Level Architecture](./ARCHITECTURE_DIAGRAMS.md#1-high-level-architecture)
2. Review [System Architecture](./ARCHITECTURE_DIAGRAMS.md#2-system-architecture)
3. Understand [Deployment Architecture](./ML_PIPELINE_ALGORITHMS.md#61-docker-deployment-architecture)
4. Study [Scalability Considerations](./TECHNICAL_DOCUMENTATION.md#102-scalability)

### For DevOps Engineers
1. Review [CI/CD Pipeline](./ML_PIPELINE_ALGORITHMS.md#5-cicd-pipeline)
2. Study [Deployment Workflows](./ML_PIPELINE_ALGORITHMS.md#6-deployment-workflows)
3. Check [Docker Configuration](./TECHNICAL_DOCUMENTATION.md#82-docker-deployment)
4. Understand [Production Architecture](./ML_PIPELINE_ALGORITHMS.md#62-production-deployment-architecture)

### For Product Managers / Stakeholders
1. Start with [Project Overview](./TECHNICAL_DOCUMENTATION.md#1-project-overview)
2. Review [Multi-Agent Architecture](./TECHNICAL_DOCUMENTATION.md#6-multi-agent-system) explanation
3. Understand [Key Capabilities](./TECHNICAL_DOCUMENTATION.md#13-core-capabilities)
4. Check [High-Level Diagrams](./ARCHITECTURE_DIAGRAMS.md#1-high-level-architecture) for visual understanding

---

## 📊 Dataset Documentation

### 1. Physician Dataset (Medicare Part B)
- **Source**: CMS Physician & Other Supplier PUF
- **Records**: ~1.2M providers
- **Key Fields**: NPI, Specialty, Charges, Services, Beneficiaries
- **ER Diagram**: [Architecture Diagrams §4.1](./ARCHITECTURE_DIAGRAMS.md#41-er-diagram---physician-dataset)

### 2. Prescriber Dataset (Medicare Part D)
- **Source**: CMS Part D Prescriber PUF
- **Records**: ~1.1M prescribers
- **Key Fields**: NPI, Specialty, Drug Costs, Claims, Beneficiaries
- **ER Diagram**: [Architecture Diagrams §4.2](./ARCHITECTURE_DIAGRAMS.md#42-er-diagram---prescriber-dataset)

### 3. LEIE Exclusion List
- **Source**: OIG LEIE Database
- **Records**: 70K+ excluded individuals/entities
- **Purpose**: Ground truth labels for known fraudulent providers
- **ER Diagram**: [Architecture Diagrams §4.3](./ARCHITECTURE_DIAGRAMS.md#43-er-diagram---leie-dataset)

---

## 🧠 Machine Learning Details

### Model Specifications
- **Type**: Deep Neural Network (DNN)
- **Architecture**: 11 → 64 → 32 → 1 (sigmoid)
- **Loss Function**: Binary Focal Crossentropy (γ=2.0)
- **Optimizer**: Adam (lr=0.001)
- **Regularization**: L2 (λ=0.001), Dropout (40%)
- **Training**: SMOTE + Class Weights for imbalance
- **Full Details**: [ML Pipeline §3](./ML_PIPELINE_ALGORITHMS.md#3-model-architecture)

### Feature Vector (11 dimensions)
1. `cps_z_tanh`: Cost per service (z-score, tanh bounded)
2. `spb_z_tanh`: Services per beneficiary (z-score, tanh bounded)
3. `cpb_phys_z_tanh`: Cost per beneficiary - physician (z-score, tanh bounded)
4. `dcp_z_tanh`: Drug cost per script (z-score, tanh bounded)
5. `cpb_presc_z_tanh`: Cost per beneficiary - prescriber (z-score, tanh bounded)
6-10. `cluster_0` to `cluster_4`: K-Means archetype (one-hot)
11. `pagerank_centrality`: Network influence score

**Feature Engineering**: [ML Pipeline §1.2](./ML_PIPELINE_ALGORITHMS.md#12-feature-engineering-detail)

---

## 🤖 Multi-Agent System

### Agent Roles

| Agent | Role | Responsibilities | Flow Diagram |
|-------|------|------------------|--------------|
| **Investigator** | Data Scout | Rule-based red flags, profile summary | [§5.3](./ARCHITECTURE_DIAGRAMS.md#investigator-agent-flow) |
| **Analyst** | ML Expert | Model prediction, SHAP explanation, LLM interpretation | [§5.3](./ARCHITECTURE_DIAGRAMS.md#analyst-agent-flow) |
| **Supervisor** | Decision Maker | Payment decision (STOP/HOLD/REVIEW/RELEASE) | [§5.3](./ARCHITECTURE_DIAGRAMS.md#supervisor-agent-flow) |
| **Reporter** | Communicator | HTML report generation, synthesis | [§5.3](./ARCHITECTURE_DIAGRAMS.md#reporter-agent-flow) |
| **Monitor** | Sentinel | Background database scanning | [§5.3](./ARCHITECTURE_DIAGRAMS.md#monitor-agent-flow) |

### LangGraph Workflow
- **Orchestration**: StateGraph with typed state
- **Flow**: Investigator → Analyst → Supervisor → Reporter → END
- **State Management**: Cumulative state updates across agents
- **Full Workflow**: [Architecture Diagrams §5.1](./ARCHITECTURE_DIAGRAMS.md#51-langgraph-workflow-diagram)

---

## 🔧 Technology Stack Summary

### Backend
- **Framework**: FastAPI 0.95+
- **ML**: TensorFlow 2.10+, scikit-learn, SHAP
- **Agents**: LangGraph 0.0.26+, LangChain Core
- **Database**: SQLite3 (dev), PostgreSQL (production)
- **Data**: Pandas, NumPy, NetworkX

### Frontend
- **Templating**: Jinja2
- **CSS**: TailwindCSS 3.x
- **Visualization**: Chart.js, Custom SHAP charts

### External
- **LLM**: Google Gemini Pro
- **Data Sources**: CMS Public Datasets, OIG LEIE

**Complete Stack**: [Technical Docs §3](./TECHNICAL_DOCUMENTATION.md#3-technology-stack)

---

## 🚀 Getting Started

1. **Installation**: Follow [README.md](../README.md) setup instructions
2. **Configuration**: Review [config.yaml](../config.yaml) parameters
3. **Training**: See [ML Training Pipeline](./ML_PIPELINE_ALGORITHMS.md#1-ml-training-pipeline)
4. **Deployment**: Check [Deployment Workflows](./ML_PIPELINE_ALGORITHMS.md#6-deployment-workflows)
5. **API Usage**: Refer to [API Reference](./TECHNICAL_DOCUMENTATION.md#7-api-reference)

---

## 📝 Document Maintenance

### Version History
- **v1.0** (2025-11-28): Initial comprehensive documentation release
  - Technical documentation
  - Architecture diagrams (17 mermaid diagrams)
  - ML pipeline and algorithms
  - CI/CD workflows

### Contributing
To update documentation:
1. Edit the relevant `.md` file in the `docs/` directory
2. Ensure mermaid diagrams render correctly
3. Update this index if adding new sections
4. Increment version numbers

### Feedback
For documentation questions or suggestions:
- Open an issue on GitHub
- Contact: [your-email@example.com]

---

## 🔗 External Resources

- **Project Repository**: [GitHub Link]
- **CMS Data**: https://data.cms.gov/
- **OIG LEIE**: https://oig.hhs.gov/exclusions/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **LangGraph**: https://github.com/langchain-ai/langgraph
- **SHAP**: https://shap.readthedocs.io/

---

<div align="center">

**FraudGuard Documentation**  
*Comprehensive Technical Reference*

Version 1.0 | Last Updated: 2025-11-28

</div>
