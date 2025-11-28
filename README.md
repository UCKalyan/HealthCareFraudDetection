# FraudGuard - Healthcare Fraud Detection System

<div align="center">

![FraudGuard Logo](static/images/logo.png)

**Adaptive and Explainable AI for Healthcare Fraud Detection**

*Multi-Agentic AI • Deep Learning • Model Context Protocol (MCP)*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)](https://fastapi.tiangolo.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.10+-orange.svg)](https://www.tensorflow.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Overview

FraudGuard is an advanced healthcare fraud detection system that combines **Multi-Agentic AI**, **Deep Learning**, and **Explainable AI (XAI)** to identify anomalous billing patterns in Medicare data. The system features a team of specialized AI agents that work together to analyze provider behavior, explain decisions using SHAP, and generate comprehensive narrative reports.

### ✨ Key Features

- 🤖 **Multi-Agent Architecture** - Specialized AI agents for investigation, analysis, and reporting
- 🧠 **Deep Learning** - Neural network-based fraud detection with high accuracy
- 📊 **Explainable AI** - SHAP-based feature importance and interpretability
- 🔐 **Secure Authentication** - Session-based login system
- 🎨 **Modern UI** - Professional dashboard with real-time updates
- 🔌 **MCP Integration** - Standardized protocol for AI tool interoperability
- 📈 **Real-time Monitoring** - Background scanning of provider database

---

## 🏗️ Project Structure

```
HealthCareFraudDetection-master/
├── 📁 data/                    # Raw and processed datasets
├── 📁 src/                     # Source code
│   ├── agents/                 # AI Agents (Investigator, Analyst, Reporter, Monitor)
│   ├── data_processing/        # Data loading and preprocessing
│   ├── models/                 # Deep learning model definitions
│   ├── training/               # Model training scripts
│   ├── explainability/         # SHAP and XAI tools
│   └── utils/                  # Utility functions
├── 📁 templates/               # Jinja2 HTML templates
│   ├── login.html             # Authentication page
│   └── dashboard.html         # Main application UI
├── 📁 static/                  # Static assets
│   ├── images/                # Logo, favicon, and images
│   ├── css/                   # Custom stylesheets
│   └── js/                    # JavaScript files
├── api_server.py              # FastAPI backend with authentication
├── mcp_server.py              # MCP Server for external AI tools
├── main.py                    # Training pipeline
├── build_artifacts.py         # Generate runtime artifacts
├── requirements.txt           # Python dependencies
└── config.yaml                # Configuration file
```

---

## 📊 Datasets

The project uses public datasets from the Centers for Medicare & Medicaid Services (CMS):

1. **Medicare Part D Prescriber Data** - Prescription drug claims
2. **Medicare Physician & Other Supplier Data** - Service and procedure claims
3. **LEIE (List of Excluded Individuals/Entities)** - Known fraudulent providers
   - Source: https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv
   - Filter: Automatically excludes 361+ providers found in LEIE database

---

## 🚀 Setup and Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- 4GB+ RAM recommended

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <your-repo-link>
   cd HealthCareFraudDetection-master
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the system:**
   - Edit `config.yaml` to set your Gemini API key (for LLM-powered agents)
   - Adjust model parameters and paths as needed

---

## 💻 Usage

### 1️⃣ Training Pipeline

Train the fraud detection model from scratch:

```bash
python main.py
```

This will:
- Load and preprocess Medicare data
- Engineer advanced features (archetypes, network centrality)
- Train the deep learning model
- Evaluate performance metrics
- Save the trained model

### 2️⃣ Web Application (Recommended)

Launch the complete fraud detection workbench with authentication:

**Step 1: Build Runtime Artifacts** (Run once)
```bash
python build_artifacts.py
```

**Step 2: Start the Application Server**
```bash
uvicorn api_server:app --reload
```

**Step 3: Access the Application**
- Open your browser to: `http://localhost:8000`
- Login with demo credentials:
  - **Username:** `admin`
  - **Password:** `fraud2024`

#### 🎯 Application Features

- **Dashboard** - Real-time statistics and high-risk provider watchlist
- **Provider Directory** - Searchable, sortable, filterable provider database
- **Manual Analysis** - "What-if" scenario testing with custom provider profiles
- **System Architecture** - Visual overview of the multi-agent system
- **AI Agent Progress** - Real-time status updates during analysis

### 3️⃣ MCP Server (External AI Integration)

Expose fraud detection tools to external AI assistants:

```bash
python mcp_server.py
```

**Available MCP Tools:**
- `get_provider_data(npi)` - Fetch raw provider features
- `predict_fraud_risk(npi)` - Get Deep Learning risk score (0.0-1.0)
- `explain_fraud_risk(npi)` - Get SHAP-based explanation

**Available MCP Resources:**
- `fraud://providers/list` - List of high-risk providers
- `fraud://providers/{npi}` - Direct access to provider records

**Use Cases:**
- Integrate with Claude Desktop
- Connect to IDE AI assistants
- Build custom chatbot interfaces
- Automate fraud investigations

---

## 🤖 Multi-Agent Architecture

The system employs a collaborative team of specialized AI agents:

### 🕵️ Investigator Agent
- **Role:** Data Scout & Rule-Based Checker
- **Tasks:**
  - Performs initial red flag detection (e.g., cost > $200)
  - Summarizes provider's basic profile
  - Identifies obvious anomalies

### 📊 Analyst Agent
- **Role:** Deep Learning Expert
- **Tasks:**
  - Runs TensorFlow model for fraud prediction
  - Calculates SHAP values for explainability
  - Interprets feature importance using LLM
  - Generates technical analysis

### 👨‍⚖️ Supervisor Agent
- **Role:** Decision Maker
- **Tasks:**
    - Reviews findings from Investigator and Analyst
    - Determines payment action (STOP, HOLD, REVIEW, RELEASE)
    - Provides reasoning and confidence score

### 📝 Reporter Agent
- **Role:** Communication Specialist
- **Tasks:**
  - Synthesizes findings from Investigator, Analyst, and Supervisor
  - Generates polished HTML narrative reports
  - Presents insights in user-friendly format

### 📡 Monitor Agent
- **Role:** Background Sentinel
- **Tasks:**
  - Continuously scans provider database
  - Calculates real-time fraud statistics
  - Updates dashboard metrics
  - Maintains scan state persistence

---

## 🔑 Key Technologies

### Machine Learning & AI
- **TensorFlow** - Deep neural network for fraud detection
- **SHAP** - Model explainability and feature importance
- **scikit-learn** - Data preprocessing and clustering
- **NetworkX** - Graph-based features (PageRank centrality)

### Backend
- **FastAPI** - Modern, high-performance web framework
- **Jinja2** - Server-side template rendering
- **Uvicorn** - ASGI server
- **Pandas** - Data manipulation and analysis

### Frontend
- **TailwindCSS** - Utility-first CSS framework
- **Chart.js** - Interactive data visualizations
- **Vanilla JavaScript** - Dynamic UI interactions

### Security
- **Session-based Authentication** - Secure login system
- **HTTP-only Cookies** - XSS protection
- **CSRF Protection** - Cross-site request forgery prevention

---

## 📈 Model Performance

The deep learning model achieves:
- **High Accuracy** - Effective fraud detection
- **Explainability** - SHAP values for every prediction
- **Scalability** - Batch processing of large datasets
- **Real-time Inference** - Fast predictions (<100ms)

---

## 🔐 Security & Authentication

### Demo Credentials
- **Username:** `admin`
- **Password:** `fraud2024`

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

---

## 🎨 UI/UX Features

### Current Features
- ✅ Professional branding with custom logo
- ✅ Modern gradient design
- ✅ Responsive layout
- ✅ Real-time agent progress tracking
- ✅ Interactive data tables with sorting/filtering
- ✅ SHAP visualization with tooltips
- ✅ Session-based authentication

### Planned Enhancements
See [UX Improvements Document](docs/ux_improvements.md) for detailed roadmap:
- Advanced data visualizations
- Keyboard shortcuts
- Toast notifications
- Export functionality
- Collaboration features
- Mobile optimization

---

## 📚 API Documentation

Once the server is running, access interactive API docs:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Key Endpoints

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

---

## 🧪 Testing

### Manual Testing
```bash
# Test MCP server
python test_mcp.py

# Test LLM integration
python test_llm.py
```

### Browser Testing
1. Start the application server
2. Navigate to `http://localhost:8000`
3. Test authentication flow
4. Verify all dashboard features
5. Test provider analysis workflow

---

## 📖 Documentation

- **[Implementation Plan](docs/implementation_plan.md)** - Technical implementation details
- **[Data Processing Guide](docs/data_processing.md)** - Detailed pipeline and feature engineering docs
- **[System Architecture](ARCHITECTURE.md)** - Architecture and ER diagrams
- **[Walkthrough](docs/walkthrough.md)** - Feature walkthrough and testing results
- **[UX Improvements](docs/ux_improvements.md)** - Future enhancement suggestions

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

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
- **Project Advisor** - [Advisor Name]
- **Institution** - [University Name]

---

## 🙏 Acknowledgments

- Centers for Medicare & Medicaid Services (CMS) for public datasets
- Office of Inspector General (OIG) for LEIE data
- TensorFlow and SHAP communities
- FastAPI and Jinja2 developers

---

## 📞 Support

For questions, issues, or suggestions:
- Open an issue on GitHub
- Contact: [your-email@example.com]
- Documentation: [Link to detailed docs]

---

<div align="center">

**Built with ❤️ for Healthcare Integrity**

*Protecting Medicare beneficiaries through AI-powered fraud detection*

</div>