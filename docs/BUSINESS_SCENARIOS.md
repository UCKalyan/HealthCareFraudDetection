# Business Scenarios for Healthcare Fraud Detection System

This document outlines key business scenarios to test the integration between the **Fraud Detection App** (Analysis & Risk Scoring) and the **Finance App** (Payment Processing & Recovery).

## System Overview
- **Fraud Detection App (Port 8000)**: Analyzes provider data, calculates risk scores, and uses AI agents to investigate suspicious activity.
- **Finance App (Port 8001)**: Manages provider payments, financial profiles, and processes payment holds/releases based on risk assessments.
- **Integration Point**: The Fraud App (via MCP Server) communicates with the Finance App API to execute actions like **Stopping Payments** or **Flagging Transactions**.

---

## Scenario 1: High-Risk Provider Detection & Payment Hold (Automated)
**Goal**: Verify that a high-risk provider identified by the Fraud App automatically triggers a payment hold in the Finance App.

### Workflow
1.  **Trigger**: User (or automated batch process) initiates an analysis for a known high-risk provider (e.g., NPI with high opioid prescribing rates) in the **Fraud App**.
2.  **Process**:
    *   Fraud App calculates a high risk score (> 0.9).
    *   AI Investigator Agent generates a report recommending "STOP PAYMENT".
    *   **Integration**: The Agent calls the `flag_transaction` tool (MCP), which sends a request to the Finance App's `/api/process_payment_hold` endpoint.
3.  **Verification**:
    *   **Fraud App UI**: Shows the provider as "High Risk" with a "STOP PAYMENT" recommendation.
    *   **Finance App UI**:
        *   Go to **Payments** page.
        *   Verify a new transaction appears with status **HELD**.
        *   The "Agent Decision" column should show "HOLD" with the reason provided by the AI.

## Scenario 2: Low-Risk Provider Verification & Payment Release (Happy Path)
**Goal**: Ensure that low-risk providers are verified and their payments are processed normally.

### Workflow
1.  **Trigger**: User analyzes a low-risk provider (e.g., standard general practitioner) in the **Fraud App**.
2.  **Process**:
    *   Fraud App calculates a low risk score (< 0.3).
    *   AI Investigator Agent recommends "RELEASE" or "NO ACTION".
    *   **Integration**: The Agent might call `approve_provider` (if configured) or simply log the low risk.
3.  **Verification**:
    *   **Fraud App UI**: Shows the provider as "Low Risk".
    *   **Finance App UI**:
        *   Go to **Providers** page.
        *   Verify the provider's status is **Active** or **Verified**.
        *   Ensure no new "HELD" transactions are created for this provider.

## Scenario 3: Manual Supervisor Review (Human-in-the-Loop)
**Goal**: Test the workflow where an AI decision is ambiguous and requires human intervention.

### Workflow
1.  **Trigger**: User analyzes a medium-risk provider (score 0.4 - 0.7) in the **Fraud App**.
2.  **Process**:
    *   AI Investigator Agent is unsure and flags the case for **Supervisor Review**.
    *   A case is created in the **Case Management System** (shared DB).
3.  **Action**:
    *   Log in to **Fraud App** as a Supervisor (if applicable) or use the **Finance App** Audit/Case view.
    *   Review the case details and manually select "Approve" or "Reject".
4.  **Verification**:
    *   **Finance App**: Verify that the manual decision updates the transaction status (e.g., changing from "PENDING REVIEW" to "PAID" or "REJECTED").
    *   Check **Audit Log** in Finance App to see the human decision recorded.

## Scenario 4: Emerging Threat Detection (Real-Time Analytics)
**Goal**: Verify that the system detects sudden changes in behavior (e.g., a dormant provider suddenly billing millions).

### Workflow
1.  **Trigger**: Simulate a sudden spike in billing for a previously dormant provider (this might require manipulating the underlying data or using a specific test NPI).
2.  **Process**:
    *   **Fraud App**: The "Fast Model" (Early Warning System) detects the anomaly even if the "Slow Model" (Historical) hasn't fully updated.
    *   Alert is generated: "⚠️ EMERGING THREAT".
3.  **Verification**:
    *   **Fraud App**: Verify the "Emerging Threat" flag is visible on the dashboard.
    *   **Finance App**: Verify that the provider is added to the **High Risk Providers** list in the Analytics view.

## Scenario 5: Payment Recovery for Processed Transactions
**Goal**: Test the "Clawback" mechanism when fraud is detected *after* a payment has already been processed.

### Workflow
1.  **Pre-condition**: A transaction exists in the **Finance App** with status **PAID**.
2.  **Trigger**: Fraud App analyzes the provider associated with this transaction and determines it was fraudulent.
3.  **Process**:
    *   AI Agent attempts to `flag_transaction` for the past transaction ID.
    *   **Integration**: Finance App detects the status is already **PAID**.
    *   Finance App rejects the simple "HOLD" but triggers a **Recovery Workflow** (or returns an error indicating recovery is needed).
4.  **Verification**:
    *   **Finance App**: Go to the **Recovery** page.
    *   Verify a new **Recovery Case** has been opened for that transaction.
    *   Status should be "OPEN" or "RECOVERY INITIATED".

## Data Flow Summary
| Step | Source System | Action | Destination System | Data Transferred |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Fraud App** | Analyze Provider | **Shared DB** | Reads Provider Features |
| 2 | **Fraud App** | Calculate Risk | **Internal** | Risk Score, SHAP Values |
| 3 | **Fraud App (Agent)** | Decide Action | **Finance App API** | NPI, Transaction ID, Decision, Reason |
| 4 | **Finance App** | Process Request | **Finance DB** | Updates Transaction Status (HOLD/PAID) |
| 5 | **Finance App** | Dashboard Update | **Finance UI** | Aggregated Stats (Total Holds, Risk Counts) |
