# MCP Integration - Implementation Code

## Complete Implementation for Bidirectional MCP Demo

---

## 1. Finance API Endpoint (Already Partially Exists)

Add this to `/Users/kalyan/Documents/HealthCareFraudDetection-master/finance-app/api_server.py`:

```python
import uuid
import json

@app.post("/api/process_payment_hold")
async def process_payment_hold(data: dict):
    """
    Receives payment hold request from Fraud Detection
    Demonstrates MCP bidirectional communication
    """
    npi = data.get("npi")
    action = data.get("action")
    fraud_score = data.get("fraud_score", 0.0)
    confidence = data.get("confidence", 0.0)
    reasoning = data.get("reasoning", "")
    source = data.get("source", "unknown")
    analyst = data.get("analyst", "system")
    
    logger.info(f"📥 MCP Request from {source}: Hold payment for NPI {npi}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create a payment hold transaction
        transaction_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO payment_transactions 
            (transaction_id, npi, payment_amount, fraud_risk_score, 
             agent_decision, agent_confidence, agent_reasoning, 
             payment_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            transaction_id,
            npi,
            0.0,  # No specific amount for holds
            fraud_score,
            "HOLD",
            confidence,
            f"[MCP from {source} by {analyst}] {reasoning}",
            "PENDING"
        ))
        
        # Log the agent decision
        cursor.execute('''
            INSERT INTO agent_decision_logs
            (transaction_id, npi, decision, confidence, reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (
            transaction_id,
            npi,
            "HOLD",
            confidence,
            f"[MCP] {reasoning}"
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Payment hold processed: Transaction {transaction_id}")
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "npi": npi,
            "decision": "HOLD",
            "message": f"Payment hold processed for NPI {npi}"
        }
        
    except Exception as e:
        logger.error(f"Error processing payment hold: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 2. Fraud Detection UI Button

Add to `/Users/kalyan/Documents/HealthCareFraudDetection-master/templates/investigation_report.html`

After the supervisor recommendation section (around line 150), add:

```html
<!-- MCP Integration: Payment Hold Button -->
{% if finalScore >= 0.70 %}
<div class="mt-6 bg-red-50 border-l-4 border-red-500 p-6 rounded-lg shadow">
    <div class="flex items-center justify-between">
        <div>
            <h3 class="text-xl font-bold text-red-800 flex items-center">
                <span class="mr-2">⚠️</span> High Risk Detected!
            </h3>
            <p class="text-red-700 mt-2">
                This provider has a fraud score of <span class="font-mono font-bold text-lg">{{ "%.4f"|format(finalScore) }}</span>. 
                Consider holding all pending payments immediately.
            </p>
            <p class="text-red-600 text-sm mt-1">
                This action will communicate with the Finance system via MCP.
            </p>
        </div>
        <button 
            onclick="submitPaymentHold()"
            id="holdButton"
            class="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold transition-all transform hover:scale-105 shadow-lg">
            🛑 Hold All Payments
        </button>
    </div>
    
    <!-- Status message -->
    <div id="hold-status" class="mt-4"></div>
</div>

<script>
async function submitPaymentHold() {
    const button = document.getElementById('holdButton');
    const npi = '{{ npi }}';
    const fraudScore = {{ finalScore }};
    
    // Disable button
    button.disabled = true;
    button.innerHTML = '⏳ Submitting...';
    
    // Show loading
    document.getElementById('hold-status').innerHTML = `
        <div class="bg-blue-50 p-4 rounded border-l-4 border-blue-500">
            <p class="text-blue-700 flex items-center">
                <span class="animate-spin mr-2">⏳</span>
                Submitting payment hold request to Finance system via MCP...
            </p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/submit_payment_hold', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                npi: npi,
                fraud_score: fraudScore,
                reasoning: "High fraud risk detected during investigation - {{ risk }} risk level"
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('hold-status').innerHTML = `
                <div class="bg-green-50 p-4 rounded border-l-4 border-green-500 shadow">
                    <h4 class="font-bold text-green-800 text-lg flex items-center">
                        <span class="mr-2">✅</span> Payment Hold Successful!
                    </h4>
                    <p class="text-green-700 mt-2">${result.message}</p>
                    <p class="text-sm text-green-600 mt-2 font-mono">
                        <strong>Transaction ID:</strong> ${result.finance_response.transaction_id}
                    </p>
                    <div class="mt-3 p-3 bg-green-100 rounded">
                        <p class="text-green-800 font-semibold">
                            ➡️ Open Finance app at <a href="http://localhost:8001/payments" target="_blank" class="underline">http://localhost:8001/payments</a>
                        </p>
                        <p class="text-green-700 text-sm mt-1">
                            You'll see the hold transaction appear in real-time!
                        </p>
                    </div>
                </div>
            `;
            
            // Re-enable button with different text
            button.disabled = false;
            button.innerHTML = '✅ Hold Submitted';
            button.classList.remove('bg-red-600', 'hover:bg-red-700');
            button.classList.add('bg-green-600', 'cursor-not-allowed');
        } else {
            document.getElementById('hold-status').innerHTML = `
                <div class="bg-red-50 p-4 rounded border-l-4 border-red-500">
                    <h4 class="font-bold text-red-800">❌ Error</h4>
                    <p class="text-red-700 mt-1">${result.message}</p>
                    <p class="text-red-600 text-sm mt-2">
                        Make sure the Finance app is running on port 8001.
                    </p>
                </div>
            `;
            
            // Re-enable button
            button.disabled = false;
            button.innerHTML = '🛑 Hold All Payments';
        }
    } catch (error) {
        document.getElementById('hold-status').innerHTML = `
            <div class="bg-red-50 p-4 rounded border-l-4 border-red-500">
                <h4 class="font-bold text-red-800">❌ Connection Error</h4>
                <p class="text-red-700 mt-1">${error.message}</p>
                <p class="text-red-600 text-sm mt-2">
                    Ensure the Finance application is running on port 8001.
                </p>
            </div>
        `;
        
        // Re-enable button
        button.disabled = false;
        button.innerHTML = '🛑 Hold All Payments';
    }
}
</script>
{% endif %}
```

---

## 3. Additional MCP Scenarios

### Scenario 2: Fraud Score Query from Finance

**Use Case:** Finance user reviewing pending payment wants real-time fraud score

**Finance UI Button** (add to `finance-app/templates/payments.html`):

```html
<!-- Add to each payment row -->
<button onclick="queryFraudScore('${p.npi}')" 
        class="text-xs px-2 py-1 bg-blue-500 text-white rounded">
    🔍 Check Fraud Score
</button>

<script>
async function queryFraudScore(npi) {
    const response = await fetch('/api/query_fraud_score', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({npi: npi})
    });
    
    const result = await response.json();
    
    if (result.success) {
        alert(`Fraud Score for NPI ${npi}: ${(result.fraud_score * 100).toFixed(2)}%\nRisk Level: ${result.risk_level}`);
    }
}
</script>
```

**Finance API** (`finance-app/api_server.py`):

```python
@app.post("/api/query_fraud_score")
async def query_fraud_score(data: dict):
    """Query fraud score from Fraud Detection system"""
    npi = data.get("npi")
    
    try:
        # Call Fraud Detection API
        fraud_response = requests.get(
            f"http://localhost:8000/api/get_fraud_score/{npi}",
            timeout=5
        )
        
        if fraud_response.status_code == 200:
            result = fraud_response.json()
            return {
                "success": True,
                **result
            }
        else:
            return {"success": False, "message": "Fraud system unavailable"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}
```

**Fraud Detection API** (add to `src/routers/dashboard.py` or `investigation.py`):

```python
@router.get("/api/get_fraud_score/{npi}")
async def get_fraud_score(npi: int, ml_assets: dict = Depends(get_ml_assets)):
    """Provide fraud score via MCP to Finance system"""
    from src.database import get_db_connection
    import pandas as pd
    
    try:
        with get_db_connection() as conn:
            provider_df = pd.read_sql_query(
                "SELECT risk_score FROM providers WHERE provider_id = ?", 
                conn, 
                params=(npi,)
            )
            
        if provider_df.empty:
            raise HTTPException(status_code=404, detail="NPI not found")
            
        risk_score = float(provider_df.iloc[0]['risk_score'])
        
        # Determine risk level
        if risk_score >= 0.85:
            risk_level = "CRITICAL"
        elif risk_score >= 0.70:
            risk_level = "HIGH"
        elif risk_score >= 0.50:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        return {
            "npi": npi,
            "fraud_score": risk_score,
            "risk_level": risk_level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Scenario 3: Bulk Payment Holds

**Fraud Detection UI** (add to dashboard):

```html
<button onclick="bulkHoldHighRisk()" 
        class="px-4 py-2 bg-red-600 text-white rounded">
    🚨 Hold All High-Risk Payments (Score >0.80)
</button>

<script>
async function bulkHoldHighRisk() {
    if (!confirm('This will hold payments for ALL providers with fraud score >0.80. Continue?')) {
        return;
    }
    
    const response = await fetch('/api/bulk_payment_hold', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({threshold: 0.80})
    });
    
    const result = await response.json();
    alert(`Bulk hold complete:\n${result.holds_created} payments held\n${result.providers_affected} providers affected`);
}
</script>
```

---

### Scenario 4: Payment Outcome Reporting

**Finance UI** (after payment processed):

```html
<button onclick="reportOutcome('${transaction_id}', true)" 
        class="text-xs px-2 py-1 bg-green-500 text-white rounded">
    ✅ Mark as Legitimate
</button>
<button onclick="reportOutcome('${transaction_id}', false)" 
        class="text-xs px-2 py-1 bg-red-500 text-white rounded">
    ❌ Confirm Fraud
</button>

<script>
async function reportOutcome(transactionId, isLegitimate) {
    const response = await fetch('/api/report_payment_outcome', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            transaction_id: transactionId,
            is_fraud: !isLegitimate,
            notes: isLegitimate ? "Verified legitimate" : "Confirmed fraudulent activity"
        })
    });
    
    const result = await response.json();
    alert(result.message);
}
</script>
```

This feeds back to Fraud Detection for model retraining!

---

## Testing the Integration

### Step-by-Step Test:

1. **Start both servers:**
   - Fraud Detection: http://localhost:8000
   - Finance: http://localhost:8001

2. **Trigger Payment Hold:**
   - Login to Fraud Detection
   - Analyze NPI with high risk (>0.70)
   - Click "Hold All Payments"
   - See success message with transaction ID

3. **Verify in Finance:**
   - Switch to Finance app (http://localhost:8001)
   - Go to Payments page
   - See new HOLD transaction appear
   - Check reasoning shows "[MCP from fraud_detection by admin]"

4. **Check Audit Trail:**
   - Finance → Audit page
   - See decision logged
   - Timestamp matches

5. **Query Fraud Score (Reverse):**
   - In Finance, click "Check Fraud Score" on any payment
   - See fraud score retrieved from Fraud Detection

---

## Summary of MCP Scenarios

| # | Scenario | Direction | Trigger | Result |
|---|----------|-----------|---------|---------|
| 1 | **Payment Hold** | Fraud → Finance | High risk detected | Payment held in Finance |
| 2 | **Fraud Score Query** | Finance → Fraud | Review pending payment | Get real-time fraud score |
| 3 | **Bulk Holds** | Fraud → Finance | Threshold exceeded | Multiple payments held |
| 4 | **Outcome Reporting** | Finance → Fraud | Payment processed | Feed outcome for learning |
| 5 | **Risk Alert** | Fraud → Finance | Score change | Notify Finance team |
| 6 | **Whitelist Sync** | Bidirectional | Provider approved | Update both systems |

All scenarios demonstrate **real-time bidirectional integration** visible in both UIs!

---

**Ready to implement!** 🚀

The Fraud Detection API endpoint is already added. Just need to:
1. Add Finance endpoint
2. Add UI buttons
3. Test the integration!
