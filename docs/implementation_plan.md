# Payment Control & Recovery System Implementation Plan

## Goal Description

Transform the fraud detection system from being purely analytical to actively managing payment lifecycles. The 2023 Medicare data represents **historical processed payments** (9,596 already processed), but the system needs to:

1. **Distinguish payment age**: Automatically classify payments as "historical/processed" vs "new/pending" based on payment dates and processing status
2. **Control new payments**: Implement STOP/HOLD capabilities for new payment transactions before they are processed
3. **Recover disputed funds**: Create a recovery workflow for legitimate claims that were flagged but already processed in 2023

## User Review Required

> [!IMPORTANT]
> **Payment Lifecycle Design Decision**
> 
> The system will classify payments based on two criteria:
> - **Date-based**: Payments with `payment_date < 2025-01-01` are considered "historical" 
> - **Status-based**: Payments with `payment_status = 'PROCESSED'` are immutable and require recovery workflow
> - **New payments**: Payments with `payment_date >= 2025-01-01` OR `payment_status IN ('PENDING', 'HELD')` can be stopped/held
>
> This means the existing 9,596 PROCESSED payments from 2023 will trigger the recovery workflow, while the 404 PENDING/HELD transactions can still be managed.

> [!WARNING]
> **Breaking Change**
> 
> The payment hold widget behavior will change:
> - **OLD**: All fraud detections trigger "Hold Payment" button
> - **NEW**: System checks payment status first:
>   - If PROCESSED → Shows "Initiate Recovery" button
>   - If PENDING/NEW → Shows "Hold Payment" button
>   - If HELD → Shows "Already Held" status

## Proposed Changes

### Component 1: Database Schema Extensions

#### [MODIFY] [finance.db Schema](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/shared-data/databases/finance.db)

Add new table for recovery workflow:

```sql
CREATE TABLE payment_recovery_requests (
    recovery_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    npi BIGINT NOT NULL,
    original_payment_amount REAL,
    recovery_amount REAL,
    
    -- Recovery reason
    fraud_risk_score REAL,
    fraud_evidence TEXT,  -- JSON with SHAP values, investigation findings
    initiator TEXT,  -- fraud_detection_agent, analyst_manual
    initiated_by TEXT,  -- username or system
    
    -- Recovery status
    recovery_status TEXT,  -- PENDING, APPROVED, REJECTED, IN_PROCESS, COMPLETED, FAILED
    approval_level TEXT,  -- L1_REVIEW, L2_APPROVAL, LEGAL_REVIEW
    approver TEXT,
    approval_notes TEXT,
    
    -- Recovery execution
    recovery_method TEXT,  -- RECOUPMENT, OFFSET, DEMAND_LETTER, LEGAL_ACTION
    recovery_initiated_date TIMESTAMP,
    recovery_completed_date TIMESTAMP,
    amount_recovered REAL,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (transaction_id) REFERENCES payment_transactions(transaction_id),
    FOREIGN KEY (npi) REFERENCES provider_financial_profiles(npi)
);

CREATE TABLE recovery_workflow_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recovery_id TEXT NOT NULL,
    stage TEXT,  -- INITIATED, REVIEW, APPROVED, EXECUTED, COMPLETED
    status TEXT,
    notes TEXT,
    actor TEXT,  -- system, username
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (recovery_id) REFERENCES payment_recovery_requests(recovery_id)
);

CREATE INDEX idx_recovery_npi ON payment_recovery_requests(npi);
CREATE INDEX idx_recovery_status ON payment_recovery_requests(recovery_status);
CREATE INDEX idx_recovery_transaction ON payment_recovery_requests(transaction_id);
```

Add indexes for payment classification:

```sql
CREATE INDEX IF NOT EXISTS idx_payment_date_status ON payment_transactions(payment_date, payment_status);
CREATE INDEX IF NOT EXISTS idx_payment_fraud_decision ON payment_transactions(fraud_decision, fraud_risk_score);
```

---

### Component 2: Backend - Finance App

#### [NEW] [payment_classifier.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/src/services/payment_classifier.py)

Payment lifecycle classifier service to determine if a payment can be held or requires recovery.

#### [NEW] [recovery_service.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/src/services/recovery_service.py)

Recovery workflow service to manage the complete recovery lifecycle from initiation through execution.

#### [MODIFY] [api_server.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/api_server.py)

Add new endpoints:
- `POST /api/initiate_recovery` - Initiate recovery for processed payment
- `GET /api/recovery/requests` - List recovery requests with optional status filter
- `POST /api/recovery/{recovery_id}/approve` - Approve recovery request
- `POST /api/recovery/{recovery_id}/reject` - Reject recovery request

Update existing endpoint:
- `POST /api/process_payment_hold` - Add payment category check, return error if PROCESSED with recovery suggestion

---

### Component 3: Backend - Fraud Detection App

#### [MODIFY] [investigation.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app/src/routers/investigation.py)

Update `submit_payment_hold` endpoint to:
- First attempt payment hold
- If response indicates payment is processed, automatically initiate recovery instead
- Return appropriate response indicating which action was taken

---

### Component 4: Frontend UI Updates

#### [MODIFY] [payment_hold_widget.html](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app/templates/payment_hold_widget.html)

Update widget to handle two workflows:
- Show "Hold Payment" button for PENDING payments
- Show "Initiate Recovery" button for PROCESSED payments
- Update alert colors and messaging appropriately
- Add recovery confirmation UI

#### [NEW] [recovery.html](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/templates/recovery.html)

New recovery management dashboard for finance team with:
- List of pending recovery requests
- Approval/rejection interface
- Recovery details viewer
- Status tracking

#### [MODIFY] [base.html](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/templates/base.html)

Add navigation link to Recovery page in finance app.

## Phase 8: Automated Payment Control (Auto-Pilot)
### Goal
Enable the Monitor Agent to autonomously hold payments and initiate recovery for critical fraud cases (Risk Score > 0.9).

### Changes
#### [MODIFY] [monitor.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app/src/agents/monitor.py)
- Add `CRITICAL_RISK_THRESHOLD = 0.9`
- Implement `take_autonomous_action(npi, score)`
- Add HTTP client to communicate with Finance App API (`http://localhost:8001`)
- Logic:
    - If Score > 0.9:
        - Fetch active transactions for NPI
        - If PENDING -> Call `/api/process_payment_hold`
        - If PROCESSED -> Call `/api/initiate_recovery`

## Phase 9: Realistic Data Simulation
### Goal
Generate realistic transaction history for ALL 1.7M providers where the sum of transactions equals the historical total payment.

### Constraints
- Total Services: 2.6 Billion (Too large for SQLite)
- Target Row Count: ~10-20 Million (Manageable)

### Strategy: "Smart Aggregation"
#### [MODIFY] [sync_providers.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/scripts/sync_providers.py)
- **High Risk Providers (>0.75):** Generate **Monthly** summary transactions (12 per year).
- **Standard Providers:** Generate **Quarterly** summary transactions (4 per year).
- **Logic:**
    - `total_payment` is split across the transactions with random variance.
    - Dates are distributed throughout 2023.
    - Status is set to 'PROCESSED' for all historical dates.
- **Performance:** Use bulk CSV export/import or batched SQL inserts to handle 10M+ rows efficiently.

## Phase 10: Analytics Data Quality
### Goal
Populate missing "State" and "Opioid Prescriber" data in `finance.db` to fix empty Analytics charts.

### Changes
#### [MODIFY] [sync_providers.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/scripts/sync_providers.py)
- **State Data:**
    - Read `Rndrng_Prvdr_State_Abrvtn` from raw CSV (`fraud-detection-app/data/raw/MUP_PHY_...csv`).
    - Create a mapping `NPI -> State`.
    - Populate `provider_state` in `finance.db`.
- **Opioid Data:**
    - Use `total_drug_cost > 0` as a proxy for `is_opioid_prescriber` (since specific opioid data is missing in simplified DB).
    - Populate `is_opioid_prescriber` flag.

## Phase 11: Performance Optimization (Summary Table)
### Goal
Implement a "Materialized View" pattern to cache dashboard statistics, reducing API latency to <10ms and eliminating database load during reads.

### Changes
#### [NEW] Database Schema
- Create table `dashboard_statistics`:
    - `id` (PK, Single Row)
    - `total_providers` (INT)
    - `total_payments` (REAL)
    - `high_risk_providers` (INT)
    - `transactions_today` (INT)
    - `avg_confidence` (REAL)
    - `autonomous_rate` (REAL)
    - `last_updated` (DATETIME)
    - `decisions_json` (TEXT) - JSON string for the breakdown

#### [MODIFY] [api_server.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/api_server.py)
- **Background Task:** Implement `refresh_dashboard_stats()` to run every 5 minutes (or on startup).
- **API Endpoint:** Update `get_dashboard_stats` to simply `SELECT * FROM dashboard_statistics`.

## Phase 12: Single Sign-On (SSO)
### Goal
Enable seamless navigation between Finance and Fraud apps without re-login.

### Changes
#### [NEW] Shared Auth Database
- Create `shared-data/databases/auth.db`:
    - `users` table: `username`, `password_hash`, `role`
    - `sessions` table: `session_id`, `username`, `created_at`, `expires_at`

#### [MODIFY] [finance-app/api_server.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/api_server.py) & [fraud-detection-app/api_server.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app/api_server.py)
- **Login:** Authenticate against `auth.db` users table.
- **Session:** Create/Validate sessions in `auth.db` sessions table.
- **Cookie:** Use a shared cookie name `hcfd_session` with `Path=/`.

## Verification Plan

### Automated Tests

**Backend Unit Tests:**

```bash
cd /Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app
python -m pytest tests/test_payment_classifier.py -v
python -m pytest tests/test_recovery_service.py -v
```

Create test files to verify:
- Payment classification logic (historical vs new)
- Recovery service initiation and status transitions
- Approval level determination based on amount and fraud score

**API Integration Tests:**

```bash
cd /Users/kalyan/Documents/HealthCareFraudDetection-master
python -m pytest tests/test_recovery_integration.py -v
```

Test end-to-end scenarios:
1. Hold request on PROCESSED payment returns recovery required
2. Hold request on PENDING payment succeeds
3. Recovery initiation creates proper records
4. Recovery approval updates all tables correctly

### Manual Verification

**Scenario 1: Historical Payment Recovery**

1. Start both servers:
   ```bash
   # Terminal 1
   cd fraud-detection-app && uvicorn api_server:app --port 8000
   
   # Terminal 2
   cd finance-app && python api_server.py
   ```
2. Navigate to http://localhost:8000
3. Analyze provider with existing 2023 processed payment
4. **Expected**: Widget shows "Initiate Recovery" button (not "Hold Payment")
5. Click button, verify success message with recovery ID
6. Navigate to http://localhost:8001/recovery
7. **Expected**: New recovery request appears in pending queue

**Scenario 2: New Payment Hold**

1. Create new pending payment in database
2. Analyze provider in fraud detection app
3. **Expected**: Widget shows "Hold Payment" button
4. Click button, verify payment status updates to HELD
5. Verify in payments dashboard that hold was recorded

**Scenario 3: Recovery Approval Workflow**

1. Complete Scenario 1 to create recovery request
2. Open finance app recovery dashboard
3. Find pending request, click "Approve"
4. **Expected**: Status changes to APPROVED
5. Verify workflow logs record approval with timestamp and actor
6. Check that provider financial profile is updated if needed

## Phase 13: Advanced AI Features
### Goal
Enhance the fraud detection capabilities with Nested Learning (HOPE), Dual-Speed models, and improved visualization.

### Changes
#### [NEW] Nested Learning Architecture
- **Dual-Speed Model**: Implement Fast (Recent) and Slow (Historical) weights.
- **HOPE (Hybrid Online & Periodic Estimation)**: Combine models for robust scoring.
- **Model Format**: Migrate from `.h5` to `.keras` for better compatibility.

#### [MODIFY] [dashboard.html](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app/templates/dashboard.html)
- **Scan Button**: Replace "Analyze" with "Scan" for real-time risk assessment.
- **Dual-Score Modal**: Show Stable vs Early Warning scores side-by-side.
- **Alerts**: Highlight significant deviations between models.

#### [MODIFY] [dependencies.py](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/fraud-detection-app/src/dependencies.py)
- **Feature Store**: Ensure `provider_features.csv` is correctly loaded.
- **Path Fix**: Handle relative paths for seamless execution.

#### [MODIFY] [README.md](file:///Users/kalyan/Documents/HealthCareFraudDetection-master/README.md)
- Update "Key Features" with Nested Learning.
- Update "Model Performance" with Dual-Speed details.
- Document new UI features.
