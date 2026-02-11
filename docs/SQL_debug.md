# SQL Debugging Guide

This document lists SQL statements used in the Health Care Fraud Detection system and provides commands to execute them from the terminal to check values.

## Database Locations

All databases are located in the `shared-data/databases/` directory relative to the project root.

| Database | Path | Description |
|----------|------|-------------|
| **Auth DB** | `shared-data/databases/auth.db` | Stores user credentials and active sessions. |
| **Finance DB** | `shared-data/databases/finance.db` | Stores payment transactions, provider financial profiles, and analytics. |
| **Providers DB** | `shared-data/databases/providers.db` | Stores provider risk scores and details for the Fraud Detection App. |
| **Feedback DB** | `shared-data/databases/feedback.db` | Stores human feedback for RL training. |
| **Cases DB** | `shared-data/databases/cases.db` | Stores case management data for supervisors. |

---

## SQL Statements & Commands

You can execute these commands from the project root directory.

### 1. Auth Database (`auth.db`)

#### Check Active Session
Retrieve the username and role for a given session ID.
```bash
sqlite3 shared-data/databases/auth.db "SELECT s.username, u.role FROM sessions s JOIN users u ON s.username = u.username WHERE s.session_id = 'YOUR_SESSION_ID'"
```

#### Verify User Credentials
Check if a user exists with the given username and password.
```bash
sqlite3 shared-data/databases/auth.db "SELECT * FROM users WHERE username = 'admin' AND password = 'password'"
```

#### List All Active Sessions
```bash
sqlite3 shared-data/databases/auth.db "SELECT * FROM sessions"
```

---

### 2. Finance Database (`finance.db`)

#### Dashboard Statistics
View the current dashboard statistics (cached).
```bash
sqlite3 shared-data/databases/finance.db "SELECT * FROM dashboard_statistics WHERE id = 1"
```

#### Provider Financial Profiles
**Count total providers:**
```bash
sqlite3 shared-data/databases/finance.db "SELECT COUNT(*) FROM provider_financial_profiles"
```

**Find a specific provider by NPI:**
```bash
sqlite3 shared-data/databases/finance.db "SELECT * FROM provider_financial_profiles WHERE npi = 1234567890"
```

**List High-Risk Providers:**
```bash
sqlite3 shared-data/databases/finance.db "SELECT npi, provider_name, total_payment_all FROM provider_financial_profiles WHERE is_high_cost_provider = 1 OR is_opioid_prescriber = 1 LIMIT 10"
```

#### Payment Transactions
**List recent transactions:**
```bash
sqlite3 shared-data/databases/finance.db "SELECT * FROM payment_transactions ORDER BY created_at DESC LIMIT 10"
```

**Check status of a specific transaction:**
```bash
sqlite3 shared-data/databases/finance.db "SELECT payment_status, fraud_risk_score, fraud_decision FROM payment_transactions WHERE transaction_id = 'TXN_ID'"
```

**Count transactions by status (Today):**
```bash
sqlite3 shared-data/databases/finance.db "SELECT payment_status, COUNT(*) FROM payment_transactions WHERE created_at >= date('now') GROUP BY payment_status"
```

#### Agent Decision Logs
View recent decisions made by the autonomous agent.
```bash
sqlite3 shared-data/databases/finance.db "SELECT * FROM agent_decision_logs ORDER BY created_at DESC LIMIT 10"
```

---

### 3. Providers Database (`providers.db`)

#### Check Provider Risk Score
Get the current risk score and status for a provider.
```bash
sqlite3 shared-data/databases/providers.db "SELECT provider_id, risk_score, status FROM providers WHERE provider_id = '1234567890'"
```

#### List Top High-Risk Providers
```bash
sqlite3 shared-data/databases/providers.db "SELECT provider_id, risk_score FROM providers ORDER BY risk_score DESC LIMIT 10"
```

---

### 4. Cases Database (`cases.db`)

#### List Pending Cases
View all cases waiting for supervisor review.
```bash
sqlite3 shared-data/databases/cases.db "SELECT * FROM cases WHERE status = 'PENDING' ORDER BY timestamp DESC"
```

#### View Case Details
```bash
sqlite3 shared-data/databases/cases.db "SELECT * FROM cases WHERE id = 1"
```

---

### 5. Feedback Database (`feedback.db`)

#### View Recent Feedback
See the latest human feedback entries.
```bash
sqlite3 shared-data/databases/feedback.db "SELECT * FROM feedback ORDER BY timestamp DESC LIMIT 10"
```

---

## Schema Reference

To see the schema of any table, you can use the `.schema` command in sqlite3.

**Example:**
```bash
sqlite3 shared-data/databases/finance.db ".schema payment_transactions"
```
