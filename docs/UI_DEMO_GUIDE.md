# Finance & Fraud Detection - UI Demo Guide

**Step-by-Step Demonstration Scenarios**

---

## 🎯 Prerequisites

**Ensure both servers are running:**
- Fraud Detection: http://localhost:8000
- Finance Application: http://localhost:8001

**Demo Credentials:**
- Fraud Detection: `admin` / `fraud2025`
- Finance App: `admin` / `finance2024`

---

## 📊 Scenario 1: Finance Dashboard Overview

**Objective:** Demonstrate the Finance application's comprehensive financial monitoring capabilities

### Steps:

1. **Navigate to Finance Dashboard**
   - Open browser: http://localhost:8001
   - Login with: `admin` / `finance2024`
   - You'll land on the Dashboard page

2. **Review KPI Cards** (Top Row)
   - **Total Providers:** Should show `104,002`
   - **Total Payments:** Should show `$20.7B`
   - **Transactions Today:** Shows recent activity
   - **High-Risk Providers:** Shows count with average confidence

3. **Inspect Payment Decisions Chart** (Bottom Left)
   - Donut chart showing breakdown of:
     - APPROVE (green)
     - HOLD (yellow)
     - REJECT (red)
   - Hover over segments to see exact counts

4. **Check Agent Confidence Trend** (Bottom Right)
   - Line chart showing confidence over time
   - Should show trend of autonomous decisions

5. **Review Recent Payments Table** (Bottom)
   - Last 10 payment transactions
   - Auto-refreshes every 30 seconds
   - Note the NPI, amount, fraud score, and decision

### ✅ Validation Points:
- [ ] All KPI cards display numeric values (not dashes)
- [ ] Charts render properly with data
- [ ] Recent payments table shows 10 transactions
- [ ] Page auto-refreshes (watch the time)

### 📸 What Success Looks Like:
```
✓ KPI cards show: 104K providers, $20.7B payments
✓ Payment decisions chart has 3 colored segments
✓ Confidence trend shows line graph
✓ Table shows transaction details with fraud scores
```

---

## 🔍 Scenario 2: Provider Financial Explorer

**Objective:** Search and analyze individual provider financial profiles

### Steps:

1. **Navigate to Provider Explorer**
   - Click "Providers" in the navigation bar
   - Or go to: http://localhost:8001/providers

2. **Search for California Providers**
   - Type `CA` in the search box
   - Results filter automatically as you type
   - Note how many CA providers appear

3. **Examine a Provider Card**
   - Look at the first provider card
   - **Check for:**
     - Provider NPI (10-digit number)
     - Provider state (CA)
     - Total Payment amount
     - Monthly payment estimate
     - Risk badges (High-Cost Provider / Opioid Prescriber)

4. **Search by Specific NPI**
   - Clear search box
   - Enter: `1003000126`
   - Should show 1 result (if exists in dataset)

5. **Try Name Search**
   - Clear search
   - Type any common name (e.g., "John", "Smith")
   - See providers matching that name

### ✅ Validation Points:
- [ ] Search works in real-time (no submit button needed)
- [ ] Provider cards show financial summaries
- [ ] Risk badges appear for high-risk providers
- [ ] Can search by NPI, name, or state

### 📸 What Success Looks Like:
```
✓ Search "CA" shows California providers
✓ Each card displays: NPI, state, payments, risk flags
✓ Red/Yellow badges appear for high-risk providers
✓ Search updates instantly as you type
```

---

## 💳 Scenario 3: Payment Processing Center

**Objective:** Monitor and filter autonomous payment decisions

### Steps:

1. **Navigate to Payments Page**
   - Click "Payments" in navigation
   - Or go to: http://localhost:8001/payments

2. **Review Transaction Table**
   - Note the columns:
     - Transaction ID (UUID)
     - Provider (NPI + State)
     - Amount (USD)
     - Fraud Score (%)
     - Decision (APPROVE/HOLD/REJECT)
     - Confidence (%)
     - Reasoning (Agent's explanation)

3. **Test Search Filter**
   - In "Search by NPI" box, type: `1003`
   - Table filters to show only matching NPIs
   - Clear search to see all transactions

4. **Test Status Filter**
   - Click "All Statuses" dropdown
   - Select "APPROVE"
   - Table shows only approved payments
   - Try "HOLD" and "REJECT" as well

5. **Inspect Agent Reasoning**
   - Look at the "Reasoning" column
   - Read why the agent made each decision
   - Note confidence levels (85-95%)

6. **Test Manual Refresh**
   - Click the "Refresh" button
   - Table reloads with latest data
   - Auto-refresh happens every 15 seconds

### ✅ Validation Points:
- [ ] Search filters by NPI instantly
- [ ] Status dropdown filters by decision
- [ ] Both filters work together
- [ ] All transactions show fraud scores
- [ ] Agent reasoning is displayed
- [ ] Refresh button works

### 📸 What Success Looks Like:
```
✓ Table shows 100 transactions with all columns populated
✓ Search "1003" filters to matching NPIs
✓ Status filter "APPROVE" shows only green badges
✓ Each row has fraud score and agent decision
✓ Confidence scores range 85-95%
```

---

## 📈 Scenario 4: Analytics & Insights

**Objective:** Visualize risk distribution and payment patterns

### Steps:

1. **Navigate to Analytics**
   - Click "Analytics" in navigation
   - Or go to: http://localhost:8001/analytics

2. **Analyze Risk Distribution Chart** (Top Left)
   - Bar chart showing provider categories:
     - High-Cost Only (red)
     - Opioid Only (yellow)
     - Both Flags (purple)
   - Note the counts for each category
   - Subtitle shows "from top 100 providers"

3. **Review Top States Chart** (Top Right)
   - Horizontal bar chart
   - Shows top 10 states by payment volume
   - Amounts in millions ($M)
   - Note which state has highest payments

4. **Examine High-Risk Providers Table** (Bottom)
   - Top 100 high-risk providers
   - Columns:
     - Rank (#1-100)
     - NPI
     - Provider Name
     - Total Payments (millions)
     - Opioid Prescriber (Yes/No)
   - Sorted by total payment amount

5. **Identify Patterns**
   - Which states dominate top payments?
   - What % are opioid prescribers?
   - How many have "Both Flags"?

### ✅ Validation Points:
- [ ] Risk Distribution chart shows 3 bars
- [ ] Top States chart shows 10 horizontal bars
- [ ] Table shows 100 providers
- [ ] All dollar amounts formatted properly ($XXM)
- [ ] Opioid prescriber badges (Yes/No) display

### 📸 What Success Looks Like:
```
✓ Risk chart: ~7 high-cost only, ~0 opioid only, ~13 both
✓ States chart: CA, TX, FL typically in top 3
✓ Table: Top provider has $XXX million in payments
✓ Charts are sized properly (not extending)
```

---

## 📋 Scenario 5: Agent Audit Trail

**Objective:** Review autonomous agent decision history

### Steps:

1. **Navigate to Audit Trail**
   - Click "Audit" in navigation
   - Or go to: http://localhost:8001/audit

2. **Review Summary Statistics** (Top)
   - Total Decisions count
   - Approved count (green)
   - Held count (yellow)
   - Rejected count (red)

3. **Examine Decision Log Table**
   - Columns:
     - Timestamp
     - Transaction ID
     - NPI
     - Amount
     - Fraud Score
     - Decision
     - Confidence
     - Agent Reasoning
   - Sorted by most recent first

4. **Read Agent Reasoning**
   - Pick a high fraud score transaction (>70%)
   - Read the detailed reasoning
   - Note multi-factor analysis mentioned

5. **Check Confidence Levels**
   - Find decisions with different confidence levels
   - Higher fraud scores → higher confidence in REJECT
   - Lower fraud scores → higher confidence in APPROVE

### ✅ Validation Points:
- [ ] Summary stats sum correctly
- [ ] Log shows all recent decisions
- [ ] Timestamps are in order (newest first)
- [ ] All decisions have reasoning
- [ ] Confidence levels make sense with decisions

### 📸 What Success Looks Like:
```
✓ Summary: X total decisions broken down by type
✓ Each log entry has complete information
✓ High fraud scores (>85%) → REJECT decisions
✓ Low fraud scores (<30%) → APPROVE decisions
✓ Confidence levels 85-95% consistently
```

---

## 🔗 Scenario 6: Cross-Application Integration Demo

**Objective:** Demonstrate data consistency between Fraud Detection and Finance apps

### Steps:

1. **Pick a Specific NPI for Testing**
   - Use: `1003000126` (or any NPI from Finance app)

2. **Check Provider in Finance**
   - Go to Finance → Providers
   - Search for NPI: `1003000126`
   - Note:
     - Total payments
     - Risk badges
     - State
   - **Screenshot this for comparison**

3. **Analyze Same Provider in Fraud Detection**
   - Open Fraud Detection: http://localhost:8000
   - Login: `admin` / `fraud2025`
   - Click "Investigation" in nav
   - Enter NPI: `1003000126`
   - Click "Analyze Provider"

4. **Wait for Fraud Analysis**
   - Watch the agent cards progress:
     - Analyst (calculating risk)
     - Investigator (network analysis)
     - Supervisor (decision)
     - Reporter (final report)
   - Analysis takes 10-30 seconds

5. **Review Fraud Detection Results**
   - **Fraud Risk Score** (0.0 - 1.0)
   - **Risk Level** (Low/Medium/High/Critical)
   - **SHAP Feature Importance** (what drives the score)
   - **Network Analysis** (provider connections)
   - **Supervisor Decision** (payment recommendation)

6. **Compare Data Between Apps**
   - Go to Finance → Payments
   - Search for same NPI
   - Look for recent transaction
   - **Validate:**
     - Does fraud score match Fraud Detection?
     - Does payment decision align with risk level?
     - Is reasoning consistent?

### ✅ Validation Points:
- [ ] Same NPI exists in both applications
- [ ] Fraud scores are consistent
- [ ] High risk in Fraud Detection → HOLD/REJECT in Finance
- [ ] Low risk in Fraud Detection → APPROVE in Finance
- [ ] Payment amounts match financial profiles

### 📸 What Success Looks Like:
```
✓ Finance shows provider with total payments
✓ Fraud Detection calculates risk score
✓ High fraud score (>0.7) → "STOP PAYMENT" recommendation
✓ Finance payment log shows corresponding decision
✓ Both apps show same provider details (NPI, state)
```

---

## 🎬 Scenario 7: Full Workflow Demo (End-to-End)

**Objective:** Demonstrate complete fraud-to-payment workflow

### Complete Demo Script:

**Step 1: Establish Baseline (Finance Dashboard)**
```
1. Open Finance: http://localhost:8001
2. Note current "Transactions Today" count: ___
3. Note "High-Risk Providers" count: ___
```

**Step 2: Investigate High-Risk Provider (Fraud Detection)**
```
1. Open Fraud Detection: http://localhost:8000
2. Go to Investigation page
3. Find a high-risk NPI from Finance Analytics (score >0.8)
4. Enter that NPI and click "Analyze"
5. Wait for complete analysis (all 4 agents)
6. Note the fraud score: ___
7. Note Supervisor decision: ___
```

**Step 3: Check Payment Status (Finance)**
```
1. Return to Finance app
2. Go to Payments page
3. Search for the same NPI
4. Find the most recent transaction
5. Verify:
   - Fraud score matches? ___
   - Payment decision aligns? ___
   - Agent reasoning present? ___
```

**Step 4: Review Audit Trail (Finance)**
```
1. Go to Finance → Audit
2. Find the decision log for this NPI
3. Timestamp should be recent
4. Full reasoning should be documented
```

**Step 5: Analytics Validation (Finance)**
```
1. Go to Finance → Analytics
2. Check if provider appears in High-Risk table
3. Verify total payment amount
4. Check state distribution
```

### ✅ Full Validation Checklist:
- [ ] Fraud analysis completes successfully
- [ ] Risk score calculated (0.0-1.0 range)
- [ ] Payment decision made autonomously
- [ ] Decision logged in audit trail
- [ ] Both apps show consistent data
- [ ] Charts update with new data
- [ ] All pages accessible and functional

### 📸 Success Criteria:
```
✓ Fraud Detection: Analysis complete, risk score displayed
✓ Finance Payments: Transaction shows matching fraud score
✓ Finance Audit: Decision logged with reasoning
✓ Finance Analytics: Provider in high-risk table
✓ Data consistency: Same NPI, same risk assessment
```

---

## 🎥 Demo Tips & Best Practices

### Preparation:
1. **Clear Browser Cache** - Ensure fresh data loads
2. **Have NPIs Ready** - Pre-select 2-3 NPIs for demo
3. **Open Both Apps** - Side-by-side windows for comparison
4. **Screenshot Tool** - Ready to capture evidence

### During Demo:
1. **Narrate Actions** - Explain what you're clicking
2. **Point Out Key Features** - Highlight auto-refresh, filtering
3. **Show Failed Cases** - Not just successful approvals
4. **Mention Confidence** - Agent certainty in decisions
5. **Reference Dollar Amounts** - Emphasize $20.7B scale

### Common Issues:
- **Slow Loading?** Feature store is large (1.7M providers)
- **Empty Tables?** Check that sample data was generated
- **Charts Not Rendering?** Refresh page, check browser console
- **Different Fraud Scores?** Model may have retrained

---

## 📊 Demo Data Points to Mention

**Scale:**
- 104,002 providers in Finance database
- 1,767,599 providers in Fraud feature store
- $20.7 billion in total payments analyzed
- 10,000 sample transactions generated

**Risk Statistics:**
- 5,201 high-cost providers (5%)
- 32,497 opioid prescribers (31%)
- Average fraud score: ~0.15
- Threshold for REJECT: >0.85

**Autonomous Agent:**
- Decision confidence: 85-95%
- Processing time: <500ms per payment
- Multi-factor analysis (fraud score, payment history, risk signals)

---

## 🎯 Key Selling Points to Highlight

1. **Autonomous Operation** - No human needed for standard cases
2. **Real-time Monitoring** - All pages auto-refresh
3. **Explainable AI** - Agent provides reasoning for every decision
4. **Comprehensive Coverage** - 104K providers, $20.7B watched
5. **Risk-Based Approach** - Higher risk = more scrutiny
6. **Audit Trail** - Complete log of all decisions
7. **Integration** - Seamless fraud-to-finance workflow
8. **Modern UI/UX** - Glassmorphism, charts, responsive design

---

## 📝 Demo Scenario Summary Table

| Scenario | Time | Complexity | Key Validation |
|----------|------|------------|----------------|
| 1. Finance Dashboard | 2 min | Easy | KPIs populated, charts render |
| 2. Provider Explorer | 3 min | Easy | Search works, cards display |
| 3. Payment Processing | 4 min | Medium | Filters work, reasoning shown |
| 4. Analytics | 3 min | Easy | Both charts, table loads |
| 5. Audit Trail | 3 min | Easy | Logs complete, stats accurate |
| 6. Cross-App Integration | 5 min | Medium | Data consistency verified |
| 7. Full Workflow | 10 min | Hard | End-to-end flow works |

**Total Demo Time:** 30 minutes (all scenarios)  
**Quick Demo:** Scenarios 1, 2, 6 (10 minutes)  
**Comprehensive:** All 7 scenarios (30 minutes)

---

## ✅ Post-Demo Checklist

After completing demos:
- [ ] Showed all 5 Finance pages
- [ ] Demonstrated search & filtering
- [ ] Explained autonomous decisions
- [ ] Showed agent reasoning
- [ ] Validated data consistency
- [ ] Highlighted key metrics ($20.7B, 104K providers)
- [ ] Demonstrated real-time updates
- [ ] Showed audit trail for accountability

---

**Ready to Demo!** 🚀

Use this guide to showcase the complete Finance & Fraud Detection integration. Focus on the autonomous decision-making, real-time monitoring, and seamless integration between both applications.

For questions or issues during demo, refer to:
- `docs/INTEGRATION_GUIDE.md` - Technical details
- `QUICK_START.md` - Startup commands
- `docs/FINANCE_APP_DATA_ANALYSIS.md` - Data specifications
