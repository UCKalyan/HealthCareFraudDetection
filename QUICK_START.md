# Quick Start Guide - Finance & Fraud Detection Integration

## 🚀 **Starting the Servers**

### **Option 1: Start Web Apps Only (Simplest)**

**Terminal 1 - Fraud Detection:**
```bash
cd /Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app
uvicorn api_server:app --host 0.0.0.0 --port 8000
```
→ Access at: http://localhost:8000 (login: admin / fraud2025)

**Terminal 2 - Finance:**
```bash
cd /Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app  
python api_server.py
```
→ Access at: http://localhost:8001 (login: admin / finance2024)

### **Option 2: Start with MCP Servers (Full Integration)**

**Terminal 1 - Fraud Detection Web App:**
```bash
cd /Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Finance Web App:**
```bash
cd /Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app
python api_server.py
```

**Terminal 3 - Fraud Detection MCP Server:**
```bash
cd /Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app
./start_mcp_server.sh
```

**Terminal 4 - Finance MCP Server:**
```bash
cd /Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app
python mcp_server.py
```

---

## 📂 **New Project Structure**

```
HealthCareFraudDetection-master/
├── fraud-detection-app/    # Fraud Detection application
├── finance-app/            # Finance application
├── shared-data/            # Common data directory
│   ├── raw/               # Raw CMS datasets
│   ├── processed/         # Processed features
│   └── databases/         # SQLite databases
└── docs/                   # Documentation
```

Both apps access shared data via symlinks:
- `fraud-detection-app/data` → `../shared-data`
- `finance-app/data` → `../shared-data`


---

## 📊 **What to Test**

### **Finance Application** (Port 8001)

1. **Dashboard** - View 104K providers, $20.7B in payments
2. **Payment Processing** - Search & filter 10K transactions
3. **Provider Explorer** - Search providers by NPI, name, state
4. **Analytics** - Risk distribution & top states charts
5. **Audit Trail** - View agent decision logs

### **Fraud Detection** (Port 8000)

1. **Investigation** - Analyze provider NPI 1003000126
2. **Dashboard** - View provider directory & risk scores
3. **Search** - Semantic search across providers

---

## 🛑 **Stop All Servers**

```bash
# Run this to stop everything
pkill -f "uvicorn api_server:app"
pkill -f "python api_server.py"
pkill -f "python mcp_server.py"
```

---

## 📝 **Notes**

- **MCP servers are optional** - Web apps work independently
- Both web apps are fully functional on their own
- MCP integration enables machine-to-machine communication
- Start with Option 1 for simplest testing

---

**Created:** 2024-11-30  
**Status:** Ready ✅
