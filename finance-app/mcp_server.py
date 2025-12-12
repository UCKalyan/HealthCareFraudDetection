"""
Finance Application - MCP Server

Exposes payment processing tools via Model Context Protocol for M2M communication
with the Healthcare Fraud Detection application.

Author: Healthcare Fraud Detection Team
Date: 2024-11-30
"""

import sys
import os
from pathlib import Path

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from mcp.server.fastmcp import FastMCP
import sqlite3
import json
import pandas as pd
from datetime import datetime

# Initialize FastMCP Server
mcp = FastMCP("Finance Payment System")

# Configuration
DB_PATH = Path(__file__).parent.parent / "shared-data" / "databases" / "finance.db"

print(f"Finance MCP Server initializing...", file=sys.stderr)
print(f"Database: {DB_PATH}", file=sys.stderr)


# ==============================================================================
# MCP TOOLS - Payment Processing
# ==============================================================================

@mcp.tool()
def process_payment_request(npi: int, action: str, amount: float, 
                           fraud_confidence: float, reasoning: str) -> str:
    """
    Process payment request from Fraud Detection system.
    Uses autonomous Payment Agent logic.
    
    Args:
        npi: Provider National Provider Identifier
        action: STOP, HOLD, RELEASE
        amount: Payment amount
        fraud_confidence: Confidence score from fraud system (0.0-1.0)
        reasoning: Fraud detection reasoning
    
    Returns:
        JSON string with decision result
    """
    print(f"--- Tool Call: process_payment_request(npi={npi}, action={action}, amount={amount}) ---", file=sys.stderr)
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get provider financial profile
        cursor = conn.cursor()
        cursor.execute('''
            SELECT total_payment_all, is_high_cost_provider, is_opioid_prescriber, 
                   monthly_payment_estimate
            FROM provider_financial_profiles
            WHERE npi = ?
        ''', (npi,))
        
        provider = cursor.fetchone()
         
        if not provider:
            return json.dumps({
                "status": "error",
                "message": f"Provider {npi} not found in finance database"
            })
        
        total_payments, is_high_cost, is_opioid, monthly_estimate = provider
        
        # Autonomous Payment Agent decision logic
        payment_agent_confidence = 0.0
        agent_decision = ""
        agent_reasoning = ""
       
        # Factor 1: Fraud system recommendation
        if action == "STOP" and fraud_confidence > 0.85:
            payment_agent_confidence = 0.95
            agent_decision = "REJECT"
            agent_reasoning = f"High fraud confidence ({fraud_confidence:.2f}). Stopping payment."
            
        elif action == "HOLD" and fraud_confidence > 0.70:
            payment_agent_confidence = 0.85
            agent_decision = "HOLD"
            agent_reasoning = f"Medium-high fraud risk ({fraud_confidence:.2f}). Holding for review."
            
        elif action == "RELEASE" and fraud_confidence < 0.50:
            # Check payment patterns
            if amount > monthly_estimate * 2:
                payment_agent_confidence = 0.60
                agent_decision = "HOLD"
                agent_reasoning = f"Payment amount (${amount:,.2f}) exceeds typical monthly estimate (${monthly_estimate:,.2f}) by 2x. Holding for validation."
            else:
                payment_agent_confidence = 0.90
                agent_decision = "APPROVE"
                agent_reasoning = f"Low fraud risk ({fraud_confidence:.2f}), payment within normal range."
        
        else:
            # Medium confidence case - collaborative decision
            payment_agent_confidence = 0.70
            agent_decision = "REVIEW"
            agent_reasoning = f"Fraud confidence {fraud_confidence:.2f} requires additional validation."
        
        # Log decision
        transaction_id = f"TXN_{npi}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO payment_transactions 
            (transaction_id, npi, payment_amount, total_amount, payment_status, 
             fraud_risk_score, fraud_decision, fraud_reasoning,
             agent_decision, agent_confidence, agent_reasoning, processor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transaction_id, npi, amount, amount,
            agent_decision, fraud_confidence, action, reasoning,
            agent_decision, payment_agent_confidence, agent_reasoning,
            'autonomous_payment_agent'
        ))
        
        # Log agent decision
        cursor.execute('''
            INSERT INTO agent_decision_logs
            (transaction_id, agent_name, decision, confidence, reasoning, outcome)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            transaction_id, 'PaymentAgent', agent_decision, 
            payment_agent_confidence, agent_reasoning, 'SUCCESS'
        ))
        
        conn.commit()
        conn.close()
        
        result = {
            "status": "success",
            "transaction_id": transaction_id,
            "agent_decision": agent_decision,
            "confidence": payment_agent_confidence,
            "reasoning": agent_reasoning,
            "fraud_input": {
                "action": action,
                "confidence": fraud_confidence,
                "reasoning": reasoning
            }
        }
        
        print(f"Payment processed: {transaction_id} - {agent_decision}", file=sys.stderr)
        
        return json.dumps(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
def get_payment_history(npi: int, months: int = 12) -> str:
    """
    Get payment history for a provider.
    
    Args:
        npi: Provider NPI
        months: Number of months to retrieve (default 12)
    
    Returns:
        JSON string with payment history
    """
    print(f"--- Tool Call: get_payment_history(npi={npi}, months={months}) ---", file=sys.stderr)
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get payment transactions
        df = pd.read_sql_query('''
            SELECT transaction_id, payment_date, payment_amount, payment_status,
                   fraud_risk_score, agent_decision, agent_confidence
            FROM payment_transactions
            WHERE npi = ?
            ORDER BY created_at DESC
            LIMIT 100
        ''', conn, params=(npi,))
        
        conn.close()
        
        if len(df) == 0:
            return json.dumps({
                "npi": npi,
                "transaction_count": 0,
                "total_payments": 0.0,
                "transactions": []
            })
        
        result = {
            "npi": npi,
            "transaction_count": len(df),
            "total_payments": float(df['payment_amount'].sum()),
            "average_payment": float(df['payment_amount'].mean()),
            "transactions": df.to_dict(orient='records')
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "status": "error",            "message": str(e)
        })


@mcp.tool()
def get_payment_risk_signals(npi: int) -> str:
    """
    Get payment-specific risk signals for a provider.
    
    Args:
        npi: Provider NPI
    
    Returns:
        JSON string with risk signals
    """
    print(f"--- Tool Call: get_payment_risk_signals(npi={npi}) ---", file=sys.stderr)
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get provider profile
        df = pd.read_sql_query('''
            SELECT is_high_cost_provider, is_opioid_prescriber, opioid_prescriber_rate,
                   total_payment_all, monthly_payment_estimate, services_per_beneficiary,
                   payment_to_submitted_ratio
            FROM provider_financial_profiles
            WHERE npi = ?
        ''', conn, params=(npi,))
        
        if len(df) == 0:
            conn.close()
            return json.dumps({"status": "error", "message": "Provider not found"})
        
        profile = df.iloc[0]
        
        # Get recent payment pattern
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count, SUM(payment_amount) as total
            FROM payment_transactions
            WHERE npi = ? AND payment_status = 'HELD'
        ''', (npi,))
        
        held_info = cursor.fetchone()
        held_count = held_info[0] if held_info else 0
        
        conn.close()
        
        result = {
            "npi": npi,
            "risk_signals": {
                "is_high_cost_provider": bool(profile['is_high_cost_provider']),
                "is_opioid_prescriber": bool(profile['is_opioid_prescriber']),
                "opioid_prescriber_rate": float(profile['opioid_prescriber_rate']) if pd.notna(profile['opioid_prescriber_rate']) else 0.0,
                "high_services_per_beneficiary": float(profile['services_per_beneficiary']) > 10 if pd.notna(profile['services_per_beneficiary']) else False,
                "payment_pattern_anomaly": held_count > 5,
                "total_annual_payments": float(profile['total_payment_all']) if pd.notna(profile['total_payment_all']) else 0.0,
                "monthly_payment_estimate": float(profile['monthly_payment_estimate']) if pd.notna(profile['monthly_payment_estimate']) else 0.0
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
def report_payment_outcome(transaction_id: str, actual_fraud: bool, notes: str = "") -> str:
    """
    Report actual payment outcome for learning (future RL integration).
    
    Args:
        transaction_id: Transaction ID
        actual_fraud: Was this actually fraudulent?
        notes: Additional notes
    
    Returns:
        JSON confirmation
    """
    print(f"--- Tool Call: report_payment_outcome(id={transaction_id}, fraud={actual_fraud}) ---", file=sys.stderr)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Log the outcome for future learning
        cursor.execute('''
            INSERT INTO agent_decision_logs
            (transaction_id, agent_name, decision, reasoning, outcome)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            transaction_id, 'OutcomeReporter', 
            'FRAUD' if actual_fraud else 'LEGITIMATE',
            notes, 'REPORTED'
        ))
        
        conn.commit()
        conn.close()
        
        return json.dumps({
            "status": "success",
            "transaction_id": transaction_id,
            "outcome_recorded": True
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


# ==============================================================================
# MCP RESOURCES - Provider Financial Profiles
# ==============================================================================

@mcp.resource("finance://providers/high-risk")
def list_high_risk_providers() -> str:
    """List high-risk providers based on payment patterns"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        df = pd.read_sql_query('''
            SELECT npi, provider_name, provider_state, total_payment_all, 
                   is_high_cost_provider, is_opioid_prescriber
            FROM provider_financial_profiles
            WHERE is_high_cost_provider = 1 OR is_opioid_prescriber = 1
            LIMIT 50
        ''', conn)
        
        conn.close()
        
        return df.to_markdown(index=False)
        
    except Exception as e:
        return f"Error: {e}"


@mcp.resource("finance://providers/{npi}")
def get_provider_financial_profile(npi: str) -> str:
    """Get complete financial profile for a provider"""
    try:
        npi_int = int(npi)
        conn = sqlite3.connect(DB_PATH)
        
        df = pd.read_sql_query('''
            SELECT * FROM provider_financial_profiles
            WHERE npi = ?
        ''', conn, params=(npi_int,))
        
        conn.close()
        
        if len(df) == 0:
            return f"Provider {npi} not found"
        
        return df.iloc[0].to_json(indent=2)
        
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    print("Finance MCP Server ready", file=sys.stderr)
    mcp.run()
