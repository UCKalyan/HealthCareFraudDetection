# FraudGuard - Healthcare Fraud Detection & Finance System

<div align="center">

![FraudGuard Logo](static/images/logo.png)

**Adaptive and Explainable AI for Healthcare Fraud Detection & Autonomous Payment Processing**

*Multi-Agentic AI • Deep Learning • Model Context Protocol (MCP) • Autonomous Finance*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)](https://fastapi.tiangolo.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.10+-orange.svg)](https://www.tensorflow.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Overview

FraudGuard is a comprehensive healthcare fraud detection and payment processing ecosystem that combines **Multi-Agentic AI**, **Deep Learning**, **Explainable AI (XAI)**, and **Autonomous Finance** to identify anomalous billing patterns in Medicare data and automate payment control decisions. The system features two integrated applications that work together to analyze provider behavior, detect fraud, and manage payment recovery.

### 🌟 System Architecture

The platform consists of two interconnected applications:

1. **Fraud Detection Application** - AI-powered fraud analysis and investigation
2. **Finance Application** - Autonomous payment processing and recovery system

Both applications share data through a unified data layer and communicate via the Model Context Protocol (MCP) for seamless integration.

### ✨ Key Features

#### Fraud Detection App
- 🤖 **Multi-Agent Architecture** - Specialized AI agents for investigation, analysis, and reporting
- 🧠 **Deep Learning** - Neural network-based fraud detection with high accuracy
- 🔄 **Nested Learning (HOPE)** - Dual-speed models for detecting emerging threats
- 📊 **Explainable AI** - SHAP-based feature importance and interpretability
- 🔐 **Secure Authentication** - Session-based login system
- 🎨 **Modern UI** - Professional dashboard with real-time updates and risk scanning
- 📈 **Real-time Monitoring** - Background scanning of provider database

#### Finance App
- 💰 **Autonomous Payment Control** - AI-driven payment hold and release decisions
- 🔄 **Payment Recovery System** - Automated recovery agent workflows
- 📊 **Analytics Dashboard** - Real-time payment statistics and risk distribution
- 🔍 **Provider Explorer** - Search and manage 104K+ providers
- 💳 **Transaction Management** - Search, filter, and process 10K+ transactions
- 🎯 **Audit Trail** - Complete agent decision logging
- 🔗 **Fraud Integration** - Seamless integration with fraud detection system

#### Cross-Platform Features
- 🔌 **MCP Integration** - Standardized protocol for AI tool interoperability
- 📁 **Shared Data Layer** - Unified access to provider and payment data
- 🤝 **Agent Collaboration** - Cross-application agent communication
- 📊 **Unified Analytics** - Combined fraud and finance insights

---

## 🏗️ Project Structure

```
HealthCareFraudDetection-master/
├── 📁 fraud-detection-app/        # Fraud Detection Application
│   ├── src/                       # Source code
│   │   ├── agents/               # AI Agents (Investigator, Analyst, Reporter, Monitor)
│   │   ├── data_processing/      # Data loading and preprocessing
│   │   ├── models/               # Deep learning model definitions
│   │   ├── training/             # Model training scripts
│   │   ├── explainability/       # SHAP and XAI tools
│   │   ├── routers/              # FastAPI route handlers
│   │   └── utils/                # Utility functions
│   ├── templates/                # Jinja2 HTML templates
│   ├── static/                   # Static assets (CSS, JS, images)
│   ├── models/                   # Trained model artifacts
│   ├── reports/                  # Investigation reports and PDFs
│   ├── api_server.py            # FastAPI backend (Port 8000)
│   ├── mcp_server.py            # MCP Server for external AI tools
│   ├── main.py                  # Training pipeline
│   ├── build_artifacts.py       # Generate runtime artifacts
│   └── requirements.txt         # Python dependencies
│
├── 📁 finance-app/                # Finance Application
│   ├── src/                      # Source code
│   │   ├── data/                # Database setup and analytics
│   │   └── services/            # Payment classifier and recovery service
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── dashboard.html       # Main finance dashboard
│   │   ├── payments.html        # Payment processing view
│   │   ├── providers.html       # Provider directory
│   │   ├── recovery.html        # Recovery system interface
│   │   ├── analytics.html       # Analytics and charts
│   │   └── audit.html           # Audit trail viewer
│   ├── data/                    # Finance-specific data
│   │   ├── analytics/           # Performance metrics and statistics
│   │   └── databases/           # SQLite databases
│   ├── api_server.py           # FastAPI backend (Port 8001)
│   ├── mcp_server.py           # MCP Server for finance tools
│   └── requirements.txt        # Python dependencies
│
├── 📁 shared-data/               # Shared Data Layer
│   ├── raw/                     # Raw CMS datasets
│   ├── processed/               # Processed features
│   └── databases/               # SQLite databases
│
├── 📁 docs/                      # Documentation
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── ML_PIPELINE_ALGORITHMS.md
│   └── README.md
│
├── README.md                    # This file
├── QUICK_START.md              # Quick start guide
└── .gitignore                  # Git ignore rules
```

**Data Sharing Architecture:**
- Both applications access shared data via symlinks:
  - `fraud-detection-app/data` → `../shared-data`
  - `finance-app/data/shared-data` → `../shared-data`

---

## 📊 Datasets

The project uses public datasets from the Centers for Medicare & Medicaid Services (CMS):

1. **Medicare Part D Prescriber Data** - Prescription drug claims
2. **Medicare Physician & Other Supplier Data** - Service and procedure claims
3. **LEIE (List of Excluded Individuals/Entities)** - Known fraudulent providers
   - Source: https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
   - Filter: Automatically excludes 361+ providers found in LEIE database

**Data Statistics:**
- **Providers:** 104,000+
- **Transactions:** 10,000+
- **Total Payment Volume:** $20.7 Billion
- **Risk Classifications:** HIGH, MEDIUM, LOW

---

## 🚀 Setup and Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- 4GB+ RAM recommended
- SQLite3 (included with Python)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/UCKalyan/HealthCareFraudDetection.git
   cd HealthCareFraudDetection-master
   ```

2. **Install dependencies for both applications:**

   **Fraud Detection App:**
   ```bash
   cd fraud-detection-app
   pip install -r requirements.txt
   cd ..
   ```

   **Finance App:**
   ```bash
   cd finance-app
   pip install -r requirements.txt
   cd ..
   ```

3. **Configure the systems:**
   - Edit `fraud-detection-app/config.yaml` to set your Gemini API key (for LLM-powered agents)
   - Adjust model parameters and paths as needed

4. **Initialize the databases (Finance App):**
   ```bash
   cd finance-app
   python src/data/setup_database.py
   python src/data/aggregate_payment_data.py
   python src/data/generate_analytics.py
   cd ..
   ```

---

## 💻 Usage

### Quick Start (Recommended)

See [QUICK_START.md](QUICK_START.md) for detailed startup instructions.

#### Option 1: Web Apps Only (Simplest)

**Terminal 1 - Fraud Detection App:**
```bash
cd fraud-detection-app
uvicorn api_server:app --host 0.0.0.0 --port 8000
```
→ Access at: **http://localhost:8000** (Login: `admin` / `fraud2025`)

**Terminal 2 - Finance App:**
```bash
cd finance-app
python api_server.py
```
→ Access at: **http://localhost:8001** (Login: `admin` / `finance2024`)

#### Option 2: Full Integration with MCP Servers

Start both web apps as shown above, then additionally:

**Terminal 3 - Fraud Detection MCP Server:**
```bash
cd fraud-detection-app
python mcp_server.py
```

**Terminal 4 - Finance MCP Server:**
```bash
cd finance-app
python mcp_server.py
```

### Stop All Servers

```bash
pkill -f "uvicorn api_server:app"
pkill -f "python api_server.py"
pkill -f "python mcp_server.py"
```

---

## 🎯 Application Features

### Fraud Detection Application (Port 8000)

#### 🏠 Dashboard
- Real-time statistics and high-risk provider watchlist
- Provider directory with search, sort, and filter
- Quick NPI lookup and analysis

#### 🔍 Investigation Features
- **Manual Analysis** - "What-if" scenario testing with custom provider profiles
- **AI Agent Analysis** - Multi-agent investigation workflow
- **SHAP Explanations** - Visual feature importance analysis
- **Report Generation** - Comprehensive HTML and PDF reports

#### 📊 Provider Directory
- Searchable, sortable, filterable database
- Risk score visualization
- Quick actions for analysis and reporting

#### 🎨 System Architecture View
- Visual overview of multi-agent system
- Real-time agent progress tracking
- Agent collaboration visualization

#### 🔑 Demo Credentials
- **Username:** `admin`
- **Password:** `fraud2025`

---

### Finance Application (Port 8001)

#### 💼 Dashboard
- **Payment Statistics:** Total payments, pending, approved, recovered
- **Provider Overview:** 104K+ providers, $20.7B payment volume
- **Quick Actions:** Payment search, provider lookup, recovery system

#### 💳 Payment Processing
- **Search & Filter:** 10K+ transactions by status, amount, provider
- **Batch Operations:** Process multiple payments simultaneously
- **Transaction Details:** Complete payment history and metadata
- **Status Management:** PENDING, APPROVED, HELD, RECOVERED

#### 🔍 Provider Explorer
- **Advanced Search:** By NPI, name, specialty, state
- **Risk Classification:** HIGH, MEDIUM, LOW indicators
- **Payment History:** Complete transaction records per provider
- **Fraud Integration:** Cross-reference with fraud detection scores

#### 📊 Analytics
- **Risk Distribution:** Visual breakdown of payment risk levels
- **Top States:** Geographic payment analysis
- **Agent Performance:** Recovery success rates and decision metrics
- **Fraud Correlation:** Payment holds vs. fraud scores

#### 🔄 Recovery System
- **Autonomous Agents:** AI-driven recovery decision workflows
- **Priority Queue:** High-risk payments processed first
- **Action Tracking:** APPROVED, REJECTED, or MODIFIED decisions
- **Recovery Analytics:** Success rates and recovered amounts

#### 📝 Audit Trail
- **Complete Logging:** All agent decisions and actions
- **Timestamp Tracking:** When decisions were made
- **Reasoning Capture:** Why decisions were made
- **Compliance Reports:** Exportable audit logs

#### 🔑 Demo Credentials
- **Username:** `admin`
- **Password:** `finance2024`

---

## 🤖 Multi-Agent Architecture

### Fraud Detection Agents

#### 🕵️ Investigator Agent
- **Role:** Data Scout & Rule-Based Checker
- **Tasks:**
  - Performs initial red flag detection (e.g., cost > $200)
  - Summarizes provider's basic profile
  - Identifies obvious anomalies

#### 📊 Analyst Agent
- **Role:** Deep Learning Expert
- **Tasks:**
  - Runs TensorFlow model for fraud prediction
  - Calculates SHAP values for explainability
  - Interprets feature importance using LLM
  - Generates technical analysis

#### 👨‍⚖️ Supervisor Agent
- **Role:** Decision Maker
- **Tasks:**
  - Reviews findings from Investigator and Analyst
  - Determines payment action (STOP, HOLD, REVIEW, RELEASE)
  - Provides reasoning and confidence score

#### 📝 Reporter Agent
- **Role:** Communication Specialist
- **Tasks:**
  - Synthesizes findings from all agents
  - Generates polished HTML narrative reports
  - Presents insights in user-friendly format

#### 📡 Monitor Agent
- **Role:** Background Sentinel
- **Tasks:**
  - Continuously scans provider database
  - Calculates real-time fraud statistics
  - Updates dashboard metrics
  - Maintains scan state persistence

### Finance Application Agents

#### 💰 Payment Classifier Agent
- **Role:** Transaction Risk Assessor
- **Tasks:**
  - Classifies payments by risk level (HIGH, MEDIUM, LOW)
  - Integrates fraud scores from fraud detection system
  - Recommends payment actions (APPROVE, HOLD, REJECT)

#### 🔄 Recovery Agent
- **Role:** Payment Recovery Specialist
- **Tasks:**
  - Processes held/flagged payments
  - Reviews fraud evidence and risk scores
  - Makes autonomous recovery decisions
  - Tracks recovery success metrics

### Cross-Application Integration

- **MCP Protocol:** Enables agent-to-agent communication across applications
- **Shared Database:** Unified provider and payment data access
- **Real-time Sync:** Payment holds triggered by fraud detection
- **Audit Coordination:** Combined fraud + finance decision trails

---

## 🔑 Key Technologies

### Machine Learning & AI
- **TensorFlow** - Deep neural network for fraud detection
- **SHAP** - Model explainability and feature importance
- **scikit-learn** - Data preprocessing and clustering
- **NetworkX** - Graph-based features (PageRank centrality)
- **Nested Learning (HOPE)** - Dual-speed adaptive models

### Backend
- **FastAPI** - Modern, high-performance web framework
- **Jinja2** - Server-side template rendering
- **Uvicorn** - ASGI server
- **Pandas** - Data manipulation and analysis
- **SQLite** - Embedded relational database

### Frontend
- **TailwindCSS** - Utility-first CSS framework
- **Chart.js** - Interactive data visualizations
- **Vanilla JavaScript** - Dynamic UI interactions

### Security
- **Session-based Authentication** - Secure login system
- **HTTP-only Cookies** - XSS protection
- **CSRF Protection** - Cross-site request forgery prevention

### Integration
- **Model Context Protocol (MCP)** - Standardized AI tool communication
- **Symbolic Links** - Shared data access between applications
- **RESTful APIs** - Inter-application communication

---

## 📈 Model Performance

### Fraud Detection Model (HOPE Architecture)

The deep learning model achieves:
- **High Accuracy** - Effective fraud detection
- **Explainability** - SHAP values for every prediction
- **Scalability** - Batch processing of large datasets
- **Real-time Inference** - Fast predictions (<100ms)

**Nested Learning (HOPE) Features:**
- **Stable Model (Slow Weights):** Trained on historical data for robust baseline
- **Fast Model (Fast Weights):** Adapts quickly to recent trends (Early Warning System)
- **Dual-Score Visualization:** Side-by-side comparison of long-term vs emerging risk

### Payment Classification Model

- **Risk Stratification:** HIGH, MEDIUM, LOW classifications
- **Fraud Integration:** Cross-references fraud detection scores
- **Decision Support:** Autonomous recommendations with confidence scores

---

## 🔐 Security & Authentication

### Demo Credentials

**Fraud Detection App:**
- Username: `admin`
- Password: `fraud2025`

**Finance App:**
- Username: `admin`
- Password: `finance2024`

### Production Deployment

⚠️ **Important:** The current authentication system is for demonstration purposes only.

For production use, implement:
- Database-backed user management
- Password hashing (bcrypt, argon2)
- HTTPS/TLS encryption
- CSRF token validation
- Rate limiting
- Secure session storage (Redis, database)
- Multi-factor authentication (MFA)
- OAuth/SSO integration
- Role-based access control (RBAC)
- API key management for MCP servers

---

## 📚 API Documentation

### Fraud Detection App API

Once the server is running, access interactive API docs:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

**Key Endpoints:**
```
GET  /                      → Redirect to login or dashboard
GET  /login                 → Login page
POST /login                 → Authenticate user
GET  /logout                → Logout and clear session
GET  /dashboard             → Main application (protected)
GET  /dashboard_stats       → Real-time statistics
GET  /providers             → Provider directory with pagination
POST /analyze_provider      → Analyze specific provider by NPI
POST /analyze_new_provider  → Analyze custom provider profile
```

### Finance App API

**Swagger UI:** `http://localhost:8001/docs`

**Key Endpoints:**
```
GET  /                      → Redirect to dashboard
GET  /login                 → Login page
POST /login                 → Authenticate user
GET  /dashboard             → Finance dashboard
GET  /payments              → Payment processing interface
GET  /providers             → Provider directory
GET  /recovery              → Recovery system
GET  /analytics             → Analytics dashboard
GET  /audit                 → Audit trail
GET  /api/payments          → Get payments with filters
POST /api/payments/process  → Process payment actions
GET  /api/providers/search  → Search providers
GET  /api/analytics/stats   → Get analytics data
```

### MCP Tools

#### Fraud Detection MCP Tools:
- `get_provider_data(npi)` - Fetch raw provider features
- `predict_fraud_risk(npi)` - Get Deep Learning risk score (0.0-1.0)
- `explain_fraud_risk(npi)` - Get SHAP-based explanation

#### Finance MCP Tools:
- `get_payment_status(transaction_id)` - Get payment status
- `process_recovery(transaction_id, action)` - Process recovery decision
- `get_provider_payments(npi)` - Get all payments for a provider

---

## 🧪 Testing

### What to Test

#### Fraud Detection App (Port 8000)
1. Login with demo credentials
2. View dashboard statistics
3. Search provider directory
4. Analyze provider (e.g., NPI: 1003000126)
5. Review generated reports
6. Test manual analysis with custom profiles

#### Finance App (Port 8001)
1. Login with demo credentials
2. **Dashboard** - View 104K providers, $20.7B in payments
3. **Payment Processing** - Search & filter 10K transactions
4. **Provider Explorer** - Search providers by NPI, name, state
5. **Analytics** - Risk distribution & top states charts
6. **Recovery System** - Process payment recovery workflows
7. **Audit Trail** - View agent decision logs

### Manual Testing Scripts

```bash
# Test MCP servers
cd fraud-detection-app
python tests/unit/test_mcp.py

# Test LLM integration
python tests/unit/test_llm.py

# Test provider queries
python tests/unit/test_providers.py
```

---

## 📖 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Fast setup and testing instructions
- **[Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md)** - Detailed technical specs
- **[ML Pipeline & Algorithms](docs/ML_PIPELINE_ALGORITHMS.md)** - Machine learning details
- **[Finance Integration Design](docs/AUTONOMOUS_FINANCE_INTEGRATION_DESIGN.md)** - Finance system architecture

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Development Guidelines:**
- Follow PEP 8 style guide for Python code
- Add unit tests for new features
- Update documentation for significant changes
- Ensure both applications remain compatible
- Test MCP integration after changes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎓 Academic Reference

This project is based on research from:

**J, P., A, S., G, S., & P, M. (2024).** "Healthcare fraud detection using adaptive learning and deep learning techniques." *Evolving Systems*.

DOI: `10.1007/s12530-023-09514-6`

---

## 👥 Authors

- **Kalyan Uppuluri** - M.Tech Project
- **GitHub:** [@UCKalyan](https://github.com/UCKalyan)
- **Repository:** [HealthCareFraudDetection](https://github.com/UCKalyan/HealthCareFraudDetection)

---

## 🙏 Acknowledgments

- Centers for Medicare & Medicaid Services (CMS) for public datasets
- Office of Inspector General (OIG) for LEIE data
- TensorFlow and SHAP communities
- FastAPI and Jinja2 developers
- The open-source AI community

---

## 📞 Support

For questions, issues, or suggestions:
- Open an issue on [GitHub](https://github.com/UCKalyan/HealthCareFraudDetection/issues)
- View the [Quick Start Guide](QUICK_START.md)
- Check the [documentation](docs/)

---

## 🗺️ Roadmap

### Upcoming Features

**Fraud Detection:**
- [ ] Advanced data visualizations
- [ ] Keyboard shortcuts
- [ ] Export functionality (CSV, Excel)
- [ ] Mobile optimization
- [ ] Real-time collaboration features

**Finance:**
- [ ] Advanced payment scheduling
- [ ] Machine learning-based recovery optimization
- [ ] Multi-currency support
- [ ] Automated compliance reporting
- [ ] Integration with external banking APIs

**Integration:**
- [ ] Real-time bidirectional sync between apps
- [ ] Unified authentication system
- [ ] Combined analytics dashboard
- [ ] GraphQL API layer
- [ ] Microservices architecture

---

<div align="center">

**Built with ❤️ for Healthcare Integrity**

*Protecting Medicare beneficiaries through AI-powered fraud detection and autonomous payment processing*

---

**🚀 Get Started:** [Quick Start Guide](QUICK_START.md) | **📖 Docs:** [Documentation](docs/) | **🐛 Issues:** [GitHub Issues](https://github.com/UCKalyan/HealthCareFraudDetection/issues)

</div>