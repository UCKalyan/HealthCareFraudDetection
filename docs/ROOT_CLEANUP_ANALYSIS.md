# Root Directory Cleanup Analysis

## 📋 Files Currently in Root Directory

### **Test & Debug Scripts (Should Move or Delete)**

**Move to `fraud-detection-app/tests/`:**
- `test_llm.py` - LLM testing
- `test_mcp.py` - MCP testing
- `test_providers.py` - Provider testing
- `test_graph_import.py` - Graph import testing
- `verify_analyst_logic.py` - Analyst verification
- `verify_workflow_fix.py` - Workflow verification

**Move to `fraud-detection-app/scripts/`:**
- `debug_nan.py` - Debug NaN values
- `debug_npi.py` - Debug specific NPI
- `debug_mcp_server.py` - MCP server debugging
- `debug_mcp_server_lowlevel.py` - Low-level MCP debugging
- `inspect_clusters.py` - Cluster inspection
- `inspect_mcp.py` - MCP inspection
- `reproduce_crash.py` - Crash reproduction
- `raw_client.py` - Raw client testing

### **Data Analysis Scripts (Should Move)**

**Move to `fraud-detection-app/scripts/analytics/`:**
- `analyze_data_overlap.py` - Data overlap analysis
- `analyze_data_skewness.py` - Skewness analysis
- `analyze_risk_thresholds.py` - Risk threshold analysis
- `check_clusters.py` - Cluster checking
- `clean_dataset.py` - Dataset cleaning
- `generate_data_report.py` - Data report generation
- `visualize_skewness.py` - Skewness visualization

### **Integration Testing (Keep in Root or Move)**

**Keep in Root (Project-level):**
- `test_mcp_integration.py` - Tests both apps together
- `reorganize_project.sh` - Reorganization script (archive)

### **Documentation Files (Should Stay)**

**Keep in Root:**
- `README.md` - Main project README ✅
- `QUICK_START.md` - Quick start guide ✅
- `REORGANIZATION_COMPLETE.md` - Reorganization summary ✅
- `ALGORITHM_DESIGN.md` - Algorithm docs (move to docs/)
- `ARCHITECTURE.md` - Architecture docs (move to docs/)
- `MCP_TESTING.md` - MCP testing docs (move to docs/)

**Move to `docs/`:**
- `ALGORITHM_DESIGN.md`
- `ARCHITECTURE.md`
- `MCP_TESTING.md`

### **HTML Files (Should Move or Delete)**

**Move to `fraud-detection-app/templates/` or archive:**
- `fraud_workbench_ui.html` - Old UI prototype

### **Configuration & Environment (Keep in Root)**

**Keep in Root (Project-level):**
- `.dockerignore` ✅
- `.env` ✅
- `.env.example` ✅
- `.gitignore` ✅
- `Dockerfile` ✅
- `docker-compose.yml` ✅
- `LICENSE` ✅
- `run_docker.sh` ✅

### **Log & Output Files (Should Delete)**

**Delete (temporary files):**
- `output.txt`
- `response.json`
- `server.log`
- `server_stderr.log`
- `test_output.txt`
- `monitor_state.json` (21MB!)
- `healthcare_fraud.db` (if duplicate)

### **Directories (Review)**

**Keep:**
- `docs/` ✅
- `fraud-detection-app/` ✅
- `finance-app/` ✅
- `shared-data/` ✅

**Review/Move:**
- `tests/` - Should move to `fraud-detection-app/tests/`
- `notebooks/` - Should move to `fraud-detection-app/notebooks/`
- `analysis_output/` - Should move to `fraud-detection-app/analysis/` or delete
- `logs/` - Keep in root or move to app-specific
- `saved_models/` - Legacy? Move to `fraud-detection-app/models/` if needed

---

## 🎯 Recommended Actions

### **Action 1: Move Test Files**
```bash
mkdir -p fraud-detection-app/tests/unit
mv test_*.py fraud-detection-app/tests/unit/
mv verify_*.py fraud-detection-app/tests/unit/
```

### **Action 2: Move Debug Scripts**
```bash
mkdir -p fraud-detection-app/scripts/debug
mv debug_*.py fraud-detection-app/scripts/debug/
mv inspect_*.py fraud-detection-app/scripts/debug/
mv reproduce_crash.py fraud-detection-app/scripts/debug/
mv raw_client.py fraud-detection-app/scripts/debug/
```

### **Action 3: Move Analysis Scripts**
```bash
mkdir -p fraud-detection-app/scripts/analytics
mv analyze_*.py fraud-detection-app/scripts/analytics/
mv check_clusters.py fraud-detection-app/scripts/analytics/
mv clean_dataset.py fraud-detection-app/scripts/analytics/
mv generate_data_report.py fraud-detection-app/scripts/analytics/
mv visualize_skewness.py fraud-detection-app/scripts/analytics/
```

### **Action 4: Move Documentation**
```bash
mv ALGORITHM_DESIGN.md docs/
mv ARCHITECTURE.md docs/
mv MCP_TESTING.md docs/
```

### **Action 5: Move Directories**
```bash
mv tests fraud-detection-app/
mv notebooks fraud-detection-app/
mv analysis_output fraud-detection-app/
```

### **Action 6: Delete Temporary Files**
```bash
rm -f output.txt response.json server.log server_stderr.log test_output.txt
rm -f monitor_state.json  # 21MB temp file
```

### **Action 7: Archive or Delete**
```bash
mkdir -p archive
mv fraud_workbench_ui.html archive/  # Old prototype
mv saved_models archive/  # If not needed
mv reorganize_project.sh archive/  # Keep for reference
```

---

## 📊 Summary

### **Files to Keep in Root**
- `README.md`
- `QUICK_START.md`
- `REORGANIZATION_COMPLETE.md`
- `test_mcp_integration.py` (tests both apps)
- `.env`, `.gitignore`, `Dockerfile`, etc.
- `.git/` directory

### **Files to Move**
- **30 Python scripts** → `fraud-detection-app/tests/` or `scripts/`
- **3 Markdown files** → `docs/`
- **3 Directories** → `fraud-detection-app/`
- **1 HTML file** → Archive

### **Files to Delete**
- **6 temporary files** (logs, outputs)
- **1 large JSON file** (21MB monitor state)

---

## ✅ Expected Final Root Structure

```
HealthCareFraudDetection-master/
├── .env
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── README.md
├── QUICK_START.md
├── REORGANIZATION_COMPLETE.md
├── run_docker.sh
├── test_mcp_integration.py       # Integration test for both apps
├── fraud-detection-app/          # Fraud Detection (organized)
├── finance-app/                  # Finance (organized)
├── shared-data/                  # Shared data
├── docs/                         # All documentation
└── archive/                      # OLD - Archived files
```

**Clean, organized, professional!** ✨

---

## 🚀 Automated Cleanup Script

I can create a script to do all this automatically. Would you like me to:

1. Create `cleanup_root.sh` script
2. Review and approve the moves
3. Execute the cleanup

This will make the root directory much cleaner with only essential project files!
