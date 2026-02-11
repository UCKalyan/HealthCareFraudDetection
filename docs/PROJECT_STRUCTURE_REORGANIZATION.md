# Project Folder Structure - Reorganization Plan

## 📂 Current Structure Analysis

The project currently has:
- **Fraud Detection App** - Root directory with mixed files
- **Finance App** - In `finance-app/` subdirectory
- **Shared Documentation** - In `docs/` directory

---

## 🎯 Proposed Clean Structure

```
HealthCareFraudDetection-master/
│
├── README.md                           # Main project overview
├── QUICK_START.md                      # Quick start for both apps
├── .gitignore
│
├── docs/                               # 📚 SHARED DOCUMENTATION
│   ├── INTEGRATION_GUIDE.md           # How both apps integrate via MCP
│   ├── MCP_INTEGRATION_COMPLETE.md    # Complete MCP implementation summary
│   ├── MCP_BIDIRECTIONAL_DEMO.md      # Bidirectional demo scenarios
│   ├── MCP_IMPLEMENTATION_CODE.md     # Code for MCP scenarios
│   ├── TIERED_PAYMENT_HOLD_SYSTEM.md # Tiered system documentation
│   ├── UI_DEMO_GUIDE.md               # UI demo scenarios
│   ├── AUTONOMOUS_FINANCE_INTEGRATION_DESIGN.md
│   ├── FINANCE_APP_DATA_ANALYSIS.md
│   └── ARCHITECTURE.md                # Overall system architecture
│
├── fraud-detection-app/               # 🔍 FRAUD DETECTION APPLICATION
│   ├── README.md                      # Fraud app specific docs
│   ├── requirements.txt               # Python dependencies
│   ├── config.yaml                    # Configuration
│   ├── api_server.py                  # FastAPI web server (port 8000)
│   ├── mcp_server.py                  # MCP server (stdio mode)
│   ├── build_artifacts.py             # Build feature store
│   ├── main.py                        # Training pipeline
│   ├── start_mcp_server.sh           # MCP startup script
│   │
│   ├── src/                           # Source code
│   │   ├── agents/                    # AI agents
│   │   │   ├── analyst.py
│   │   │   ├── investigator.py
│   │   │   ├── reporter.py
│   │   │   ├── supervisor.py
│   │   │   └── monitor.py
│   │   ├── data_processing/          # Data pipeline
│   │   │   ├── ingest.py
│   │   │   └── preprocessor.py
│   │   ├── routers/                  # API routes
│   │   │   ├── investigation.py
│   │   │   ├── dashboard.py
│   │   │   └── search.py
│   │   ├── services/                 # Business logic
│   │   │   └── semantic_search.py
│   │   ├── training/                 # ML training
│   │   │   ├── model.py
│   │   │   └── retrain_from_feedback.py
│   │   ├── utils/                    # Utilities
│   │   │   ├── config_loader.py
│   │   │   ├── graph_builder.py
│   │   │   └── notifications.py
│   │   ├── database.py               # DB connection
│   │   ├── dependencies.py           # FastAPI dependencies
│   │   └── schemas.py                # Pydantic models
│   │
│   ├── templates/                     # Jinja2 templates (UI)
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── investigation.html
│   │   ├── investigation_report.html
│   │   ├── search.html
│   │   ├── supervisor_dashboard.html
│   │   ├── payment_hold_widget.html  # MCP integration widget
│   │   └── provider_directory.html
│   │
│   ├── static/                        # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │       ├── favicon.ico
│   │       └── fraud_detection_logo.png
│   │
│   ├── data/                          # Data directory
│   │   ├── raw/                       # Raw CMS datasets
│   │   ├── processed/                 # Processed features
│   │   │   └── provider_features.csv
│   │   ├── feedback.db               # User feedback
│   │   ├── cases.db                  # Case management
│   │   └── providers.db              # Main database
│   │
│   ├── models/                        # Trained models
│   │   ├── fraud_detection_model.keras
│   │   ├── kmeans_model.joblib
│   │   ├── robust_scaler.joblib
│   │   └── specialty_stats.json
│   │
│   ├── reports/                       # Generated reports
│   │   └── report_*.pdf
│   │
│   └── scripts/                       # Utility scripts
│       ├── migrate_to_db.py
│       └── test_mcp.py
│
├── finance-app/                       # 💰 FINANCE APPLICATION
│   ├── README.md                      # Finance app specific docs
│   ├── requirements.txt               # Python dependencies
│   ├── api_server.py                  # FastAPI web server (port 8001)
│   ├── mcp_server.py                  # MCP server (stdio mode)
│   │
│   ├── src/                           # Source code
│   │   └── data/                      # Data processing
│   │       ├── aggregate_payment_data.py
│   │       ├── setup_database.py
│   │       └── generate_analytics.py
│   │
│   ├── templates/                     # Jinja2 templates (UI)
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── payments.html
│   │   ├── providers.html
│   │   ├── analytics.html
│   │   └── audit.html
│   │
│   ├── static/                        # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │       ├── favicon.ico
│   │       └── finance_logo.png
│   │
│   ├── data/                          # Data directory
│   │   ├── raw/                       # Raw payment data
│   │   ├── processed/                 # Processed data
│   │   │   └── provider_financial_profiles.csv
│   │   └── finance.db                # SQLite database
│   │
│   └── analytics/                     # Analytics outputs
│       ├── payment_statistics.json
│       ├── fraud_correlation.json
│       ├── high_risk_providers.csv
│       └── agent_performance.json
│
└── shared/                            # 🔄 SHARED UTILITIES (if any)
    └── (currently empty)
```

---

## 📋 Reorganization Steps

### **Step 1: Rename Root App Folder**

Move all fraud detection files to dedicated folder:

```bash
# Create new fraud-detection-app directory
mkdir fraud-detection-app

# Move fraud detection files
mv src fraud-detection-app/
mv templates fraud-detection-app/
mv static fraud-detection-app/
mv data fraud-detection-app/
mv models fraud-detection-app/
mv reports fraud-detection-app/
mv scripts fraud-detection-app/
mv api_server.py fraud-detection-app/
mv mcp_server.py fraud-detection-app/
mv build_artifacts.py fraud-detection-app/
mv main.py fraud-detection-app/
mv config.yaml fraud-detection-app/
mv requirements.txt fraud-detection-app/requirements.txt
mv start_mcp_server.sh fraud-detection-app/
```

### **Step 2: Keep Finance App As-Is**

The `finance-app/` folder is already well-organized.

### **Step 3: Organize Documentation**

Keep all integration docs in `/docs`:
- ✅ Already done - all docs are in `docs/`

### **Step 4: Root Level Files**

Keep these at project root:
- `README.md` - Main project overview
- `QUICK_START.md` - Quick start guide
- `.gitignore` - Git ignore rules
- `test_mcp_integration.py` - Integration test script

---

## 🎯 Benefits of New Structure

### **Clear Separation**
```
fraud-detection-app/   → All fraud detection code
finance-app/          → All finance code  
docs/                 → Shared documentation
```

### **Easy Navigation**
- Each app is self-contained
- No confusion about which files belong where
- Clear entry points (api_server.py in each folder)

### **Independent Deployment**
- Can deploy fraud detection separately
- Can deploy finance separately
- Or deploy both together

### **Better Documentation**
- App-specific README in each app folder
- Shared integration docs in `/docs`
- Quick start at root for overview

---

## 📝 Files That Need Path Updates

After reorganization, update these references:

### **1. QUICK_START.md**
```markdown
# OLD
cd /Users/kalyan/Documents/HealthCareFraudDetection-master
python api_server.py

# NEW
cd /Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app
python api_server.py
```

### **2. Integration Test Script**
```python
# test_mcp_integration.py
# Update paths to both apps
fraud_app_path = "fraud-detection-app"
finance_app_path = "finance-app"
```

### **3. start_mcp_server.sh**
```bash
# Update paths to models and data
export MODEL_PATH="models/fraud_detection_model.keras"
export FEATURE_STORE_PATH="data/processed/provider_features.csv"
```

### **4. Import Statements**
No changes needed! Python imports use relative paths within each app.

---

## 🚀 Migration Command Script

Create this script to automate the reorganization:

```bash
#!/bin/bash
# migrate_structure.sh

echo "🔄 Reorganizing project structure..."

# Create fraud-detection-app directory
mkdir -p fraud-detection-app

# Move fraud detection directories
echo "Moving source directories..."
mv src fraud-detection-app/ 2>/dev/null || true
mv templates fraud-detection-app/ 2>/dev/null || true
mv static fraud-detection-app/ 2>/dev/null || true
mv data fraud-detection-app/ 2>/dev/null || true
mv models fraud-detection-app/ 2>/dev/null || true
mv reports fraud-detection-app/ 2>/dev/null || true
mv scripts fraud-detection-app/ 2>/dev/null || true

# Move fraud detection files
echo "Moving application files..."
mv api_server.py fraud-detection-app/ 2>/dev/null || true
mv mcp_server.py fraud-detection-app/ 2>/dev/null || true
mv build_artifacts.py fraud-detection-app/ 2>/dev/null || true
mv main.py fraud-detection-app/ 2>/dev/null || true
mv config.yaml fraud-detection-app/ 2>/dev/null || true
mv start_mcp_server.sh fraud-detection-app/ 2>/dev/null || true

# Move requirements
mv requirements.txt fraud-detection-app/requirements.txt 2>/dev/null || true

# Create app-specific READMEs
echo "Creating app-specific documentation..."
echo "# Fraud Detection Application" > fraud-detection-app/README.md
echo "See main project README and /docs for details." >> fraud-detection-app/README.md

echo "✅ Reorganization complete!"
echo ""
echo "New structure:"
echo "  fraud-detection-app/  - Fraud Detection application"
echo "  finance-app/          - Finance application"
echo "  docs/                 - Shared documentation"
echo ""
echo "Next steps:"
echo "1. Update QUICK_START.md with new paths"
echo "2. Test both applications"
echo "3. Update any hardcoded paths"
```

---

## ✅ Verification Checklist

After reorganization:

### **Fraud Detection App**
- [ ] `fraud-detection-app/api_server.py` exists
- [ ] `fraud-detection-app/src/` contains all source code
- [ ] `fraud-detection-app/templates/` contains HTML templates
- [ ] `fraud-detection-app/data/` contains databases
- [ ] `fraud-detection-app/models/` contains ML models
- [ ] Start server: `cd fraud-detection-app && python api_server.py`
- [ ] Access at: http://localhost:8000

### **Finance App**
- [ ] `finance-app/api_server.py` exists
- [ ] `finance-app/src/data/` contains data scripts
- [ ] `finance-app/templates/` contains HTML templates
- [ ] `finance-app/data/finance.db` exists
- [ ] Start server: `cd finance-app && python api_server.py`
- [ ] Access at: http://localhost:8001

### **Documentation**
- [ ] `docs/` contains all integration guides
- [ ] `README.md` at root explains overall project
- [ ] `QUICK_START.md` updated with new paths

### **Test Integration**
- [ ] Run `test_mcp_integration.py` from root
- [ ] Both apps start successfully
- [ ] MCP communication works
- [ ] UIs accessible

---

## 📊 Before vs After

### **Before (Current)**
```
HealthCareFraudDetection-master/
├── src/                    ← Fraud detection code
├── templates/              ← Fraud detection templates
├── api_server.py           ← Fraud detection server
├── mcp_server.py           ← Fraud detection MCP
├── finance-app/            ← Finance app (organized)
│   ├── src/
│   ├── templates/
│   └── api_server.py
└── docs/                   ← Documentation
```

### **After (Proposed)**
```
HealthCareFraudDetection-master/
├── fraud-detection-app/    ← ALL fraud detection
│   ├── src/
│   ├── templates/
│   ├── api_server.py
│   └── mcp_server.py
├── finance-app/            ← ALL finance (unchanged)
│   ├── src/
│   ├── templates/
│   └── api_server.py
└── docs/                   ← Shared docs
```

**Much cleaner!** ✨

---

## 🎯 Recommendation

**Option A: Full Reorganization** (Cleanest)
- Move all fraud detection files to `fraud-detection-app/`
- Keep finance app as-is
- Update paths in documentation

**Option B: Minimal Changes** (Safest)
- Keep current structure
- Just add README files for clarity
- Document the structure clearly

**I recommend Option A** for long-term maintainability, but we can test it in a branch first.

Would you like me to create the migration script and execute the reorganization?
