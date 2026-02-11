import sqlite3
import httpx
import logging
import os

logger = logging.getLogger(__name__)

class ActionService:
    """
    Service for executing high-stakes actions like approving providers or flagging transactions.
    Used by both the MCP Server (backend) and the API Server (frontend widget).
    """

    def __init__(self, providers_db_path: str, finance_db_path: str, finance_api_url: str):
        self.providers_db_path = providers_db_path
        self.finance_db_path = finance_db_path
        self.finance_api_url = finance_api_url

    def approve_provider(self, npi: int, reason: str) -> dict:
        """Approves a provider, resetting risk score and status."""
        try:
            conn = sqlite3.connect(self.providers_db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE providers SET status = 'verified', risk_score = 0.0 WHERE provider_id = ?", (npi,))
            rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows == 0:
                return {"success": False, "message": f"Provider {npi} not found."}
                
            return {"success": True, "message": f"✅ Provider {npi} APPROVED. Risk score reset to 0.0."}
        except Exception as e:
            logger.error(f"Error approving provider: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def flag_transaction(self, transaction_id: str, reason: str) -> dict:
        """Flags a transaction by placing a payment hold."""
        try:
            # 1. Find NPI and current score
            conn = sqlite3.connect(self.finance_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT npi, fraud_risk_score FROM payment_transactions WHERE transaction_id = ?", (transaction_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {"success": False, "message": f"Transaction {transaction_id} not found."}
                
            npi, current_score = row
            
            # 2. Call Finance API
            payload = {
                "npi": npi,
                "transaction_id": transaction_id,
                "fraud_score": current_score or 1.0,
                "confidence": 1.0,
                "reasoning": f"MANUAL FLAG via AI Widget: {reason}",
                "action": "HOLD"
            }
            
            with httpx.Client() as client:
                resp = client.post(f"{self.finance_api_url}/api/process_payment_hold", json=payload)
                
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return {"success": True, "message": f"✅ Transaction {transaction_id} FLAGGED and HELD."}
                else:
                    return {"success": False, "message": f"⚠️ Could not flag: {data.get('message')}"}
            else:
                return {"success": False, "message": f"Failed to call Finance API: {resp.text}"}
                
        except Exception as e:
            logger.error(f"Error flagging transaction: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
