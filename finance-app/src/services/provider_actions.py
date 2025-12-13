"""
Provider Actions API - Query all finance actions for a provider
"""

from fastapi import APIRouter
import sqlite3
from pathlib import Path

def get_provider_finance_actions(db_path: str, npi: int) -> dict:
    """
    Get all payment holds and recovery requests for a provider.
    
    Returns:
        {
            "payment_holds": [...],
            "recovery_requests": [...],
            "total_actions": int
        }
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    
    try:
        # Get payment holds from payment_transactions table (status='HELD')
        cursor.execute("""
            SELECT transaction_id, npi, payment_amount, payment_status, 
                   created_at, updated_at
            FROM payment_transactions
            WHERE npi = ? AND payment_status = 'HELD'
            ORDER BY created_at DESC
        """, (npi,))
        payment_holds = [dict(row) for row in cursor.fetchall()]
        
        # Get recovery requests
        cursor.execute("""
            SELECT * FROM payment_recovery_requests
            WHERE npi = ?
            ORDER BY created_at DESC
        """, (npi,))
        recovery_requests = [dict(row) for row in cursor.fetchall()]
        
        return {
            "payment_holds": payment_holds,
            "recovery_requests": recovery_requests,
            "total_actions": len(payment_holds) + len(recovery_requests)
        }
        
    finally:
        conn.close()
