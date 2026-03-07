import sqlite3
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseQueryService:
    """
    Provides read-only database query capabilities for the chatbot.
    Enables natural language queries about providers, transactions, investigations, and statistics.
    """

    def __init__(self, providers_db_path: str, finance_db_path: str):
        self.providers_db_path = providers_db_path
        self.finance_db_path = finance_db_path

    # ========================================
    # PROVIDER QUERIES
    # ========================================

    def get_provider_info(self, npi: int) -> Dict[str, Any]:
        """Get comprehensive provider information by NPI."""
        try:
            conn = sqlite3.connect(self.providers_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT provider_id, Prscrbr_First_Name, Prscrbr_Last_Org_Name, specialty, 
                       risk_score, status
                FROM providers 
                WHERE provider_id = ?
            """, (str(npi),))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {"success": False, "message": f"Provider {npi} not found in database."}
            
            return {
                "success": True,
                "npi": row["provider_id"],
                "name": f"Dr. {row['Prscrbr_First_Name']} {row['Prscrbr_Last_Org_Name']}" if row["Prscrbr_First_Name"] else f"Provider {npi}",
                "specialty": row["specialty"],
                "risk_score": row["risk_score"],
                "status": row["status"]
            }
        except Exception as e:
            logger.error(f"Error getting provider info: {e}")
            return {"success": False, "message": f"Database error: {str(e)}"}

    def get_provider_score(self, npi: int) -> Dict[str,Any]:
        """Get risk score for a specific provider."""
        try:
            conn = sqlite3.connect(self.providers_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT risk_score, status, specialty 
                FROM providers 
                WHERE provider_id = ?
            """, (str(npi),))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {"success": False, "message": f"Provider {npi} not found."}
            
            risk_score, status, specialty = row
            risk_level = "High Risk" if risk_score >= 0.75 else "Medium Risk" if risk_score >= 0.5 else "Low Risk"
            
            return {
                "success": True,
                "npi": npi,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "status": status,
                "specialty": specialty
            }
        except Exception as e:
            logger.error(f"Error getting provider score: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_high_risk_providers(self, threshold: float = 0.75, limit: int = 10) -> Dict[str, Any]:
        """Get list of high-risk providers above threshold."""
        try:
            conn = sqlite3.connect(self.providers_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT provider_id, Prscrbr_First_Name, Prscrbr_Last_Org_Name, specialty, 
                       risk_score, status 
                FROM providers 
                WHERE risk_score >= ?
                ORDER BY risk_score DESC
                LIMIT ?
            """, (threshold, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            providers = []
            for row in rows:
                providers.append({
                    "npi": row["provider_id"],
                    "name": f"Dr. {row['Prscrbr_First_Name']} {row['Prscrbr_Last_Org_Name']}" if row["Prscrbr_First_Name"] else f"Provider {row['provider_id']}",
                    "specialty": row["specialty"],
                    "risk_score": row["risk_score"],
                    "status": row["status"]
                })
            
            return {
                "success": True,
                "count": len(providers),
                "threshold": threshold,
                "providers": providers
            }
        except Exception as e:
            logger.error(f"Error getting high-risk providers: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def count_providers_by_status(self) -> Dict[str, Any]:
        """Count providers by status (flagged/verified/pending)."""
        try:
            conn = sqlite3.connect(self.providers_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM providers 
                GROUP BY status
            """)
            
            rows = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) FROM providers")
            total = cursor.fetchone()[0]
            
            conn.close()
            
            status_counts = {status: count for status, count in rows}
            
            return {
                "success": True,
                "total": total,
                "by_status": status_counts
            }
        except Exception as e:
            logger.error(f"Error counting providers: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_provider_statistics(self) -> Dict[str, Any]:
        """Get overall provider statistics."""
        try:
            conn = sqlite3.connect(self.providers_db_path)
            cursor = conn.cursor()
            
            # Total providers
            cursor.execute("SELECT COUNT(*) FROM providers")
            total = cursor.fetchone()[0]
            
            # High risk count
            cursor.execute("SELECT COUNT(*) FROM providers WHERE risk_score >= 0.75")
            high_risk = cursor.fetchone()[0]
            
            # Average risk score
            cursor.execute("SELECT AVG(risk_score) FROM providers")
            avg_score = cursor.fetchone()[0]
            
            # Status breakdown
            cursor.execute("SELECT status, COUNT(*) FROM providers GROUP BY status")
            status_rows = cursor.fetchall()
            
            conn.close()
            
            return {
                "success": True,
                "total_providers": total,
                "high_risk_count": high_risk,
                "high_risk_percentage": (high_risk / total * 100) if total > 0 else 0,
                "average_risk_score": avg_score,
                "status_breakdown": {status: count for status, count in status_rows}
            }
        except Exception as e:
            logger.error(f"Error getting provider statistics: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    # ========================================
    # TRANSACTION QUERIES
    # ========================================

    def get_transactions_by_npi(self, npi: int, limit: int = 5) -> Dict[str, Any]:
        """Get last N transactions for a provider."""
        try:
            conn = sqlite3.connect(self.finance_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT transaction_id, npi, total_amount, payment_date, 
                       payment_status, fraud_risk_score, created_at
                FROM payment_transactions 
                WHERE npi = ?
                ORDER BY payment_date DESC
                LIMIT ?
            """, (str(npi), limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            transactions = []
            for row in rows:
                transactions.append({
                    "transaction_id": row["transaction_id"],
                    "npi": row["npi"],
                    "amount": row["total_amount"],
                    "date": row["payment_date"],
                    "status": row["payment_status"],
                    "fraud_risk_score": row["fraud_risk_score"]
                })
            
            return {
                "success": True,
                "npi": npi,
                "count": len(transactions),
                "transactions": transactions
            }
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def count_transactions_by_status(self, status: Optional[str] = None) -> Dict[str, Any]:
        """Count transactions by status (HELD/PROCESSED/PENDING) or all."""
        try:
            conn = sqlite3.connect(self.finance_db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(total_amount), 0) 
                    FROM payment_transactions 
                    WHERE payment_status = ?
                """, (status.upper(),))
                count, total_amount = cursor.fetchone()
                result = {
                    "success": True,
                    "status": status,
                    "count": count,
                    "total_amount": total_amount
                }
            else:
                cursor.execute("""
                    SELECT payment_status, COUNT(*), COALESCE(SUM(total_amount), 0) 
                    FROM payment_transactions 
                    GROUP BY payment_status
                """)
                rows = cursor.fetchall()
                
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_amount), 0) FROM payment_transactions")
                total_count, total_amount = cursor.fetchone()
                
                status_breakdown = {status: {"count": count, "total_amount": amount} 
                                  for status, count, amount in rows}
                
                result = {
                    "success": True,
                    "total_count": total_count,
                    "total_amount": total_amount,
                    "by_status": status_breakdown
                }
            
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error counting transactions: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_held_transactions(self, limit: int = 10) -> Dict[str, Any]:
        """Get all transactions currently on hold."""
        try:
            conn = sqlite3.connect(self.finance_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT transaction_id, npi, total_amount, payment_date, 
                       fraud_risk_score, created_at
                FROM payment_transactions 
                WHERE payment_status = 'HELD'
                ORDER BY fraud_risk_score DESC, created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(total_amount), 0) 
                FROM payment_transactions 
                WHERE payment_status = 'HELD'
            """)
            total_count, total_amount = cursor.fetchone()
            
            conn.close()
            
            transactions = []
            for row in rows:
                transactions.append({
                    "transaction_id": row["transaction_id"],
                    "npi": row["npi"],
                    "amount": row["total_amount"],
                    "date": row["payment_date"],
                    "fraud_risk_score": row["fraud_risk_score"]
                })
            
            return {
                "success": True,
                "total_held_count": total_count,
                "total_held_amount": total_amount,
                "showing": len(transactions),
                "transactions": transactions
            }
        except Exception as e:
            logger.error(f"Error getting held transactions: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_recent_transactions(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent transactions across all providers."""
        try:
            conn = sqlite3.connect(self.finance_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT transaction_id, npi, total_amount, payment_date, 
                       payment_status, fraud_risk_score
                FROM payment_transactions 
                ORDER BY payment_date DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            transactions = []
            for row in rows:
                transactions.append({
                    "transaction_id": row["transaction_id"],
                    "npi": row["npi"],
                    "amount": row["total_amount"],
                    "date": row["payment_date"],
                    "status": row["payment_status"],
                    "fraud_risk_score": row["fraud_risk_score"]
                })
            
            return {
                "success": True,
                "count": len(transactions),
                "transactions": transactions
            }
        except Exception as e:
            logger.error(f"Error getting recent transactions: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

    # ========================================
    # SYSTEM STATISTICS
    # ========================================

    def get_system_summary(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        try:
            # Get provider stats
            provider_stats = self.get_provider_statistics()
            
            # Get transaction stats
            transaction_stats = self.count_transactions_by_status()
            
            # Get held transaction details
            conn = sqlite3.connect(self.finance_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(total_amount), 0) 
                FROM payment_transactions 
                WHERE payment_status = 'HELD'
            """)
            held_count, held_amount = cursor.fetchone()
            conn.close()
            
            return {
                "success": True,
                "providers": {
                    "total": provider_stats.get("total_providers", 0),
                    "high_risk": provider_stats.get("high_risk_count", 0),
                    "high_risk_percentage": provider_stats.get("high_risk_percentage", 0),
                    "average_risk_score": provider_stats.get("average_risk_score", 0),
                    "flagged": provider_stats.get("status_breakdown", {}).get("flagged", 0),
                    "verified": provider_stats.get("status_breakdown", {}).get("verified", 0)
                },
                "transactions": {
                    "total_count": transaction_stats.get("total_count", 0),
                    "total_amount": transaction_stats.get("total_amount", 0),
                    "held_count": held_count,
                    "held_amount": held_amount
                }
            }
        except Exception as e:
            logger.error(f"Error getting system summary: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
