"""
Recovery Service

Manages payment recovery workflow for processed payments flagged as fraudulent.
Handles recovery request initiation, approval workflow, and execution tracking.

Author: Healthcare Fraud Detection Team
Date: 2025-12-01
"""

import uuid
from datetime import datetime
import sqlite3
import json
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class RecoveryService:
    """Manages payment recovery workflow for processed payments flagged as fraudulent"""
    
    def __init__(self, db_path: str):
        """
        Initialize recovery service.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
    
    def initiate_recovery(
        self, 
        transaction_id: str, 
        npi: int, 
        fraud_score: float,
        fraud_evidence: dict, 
        initiator: str, 
        initiated_by: str
    ) -> Dict:
        """
        Initiate recovery request for a processed payment.
        
        Args:
            transaction_id: Original payment transaction ID
            npi: Provider NPI
            fraud_score: Fraud risk score (0-1)
            fraud_evidence: Dict with investigation findings, SHAP values, etc.
            initiator: 'fraud_detection_agent' or 'analyst_manual'
            initiated_by: Username or 'system'
        
        Returns:
            Recovery request details including recovery_id and approval_level
            
        Raises:
            ValueError: If transaction not found
        """
        recovery_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get original transaction details
            cursor.execute("""
                SELECT payment_amount, npi 
                FROM payment_transactions 
                WHERE transaction_id = ?
            """, (transaction_id,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Transaction {transaction_id} not found")

            # Check for existing recovery request
            cursor.execute("""
                SELECT recovery_id FROM payment_recovery_requests WHERE transaction_id = ?
            """, (transaction_id,))
            existing = cursor.fetchone()
            if existing:
                logger.info(f"Recovery request already exists for {transaction_id}")
                return {
                    "recovery_id": existing[0],
                    "transaction_id": transaction_id,
                    "status": "ALREADY_EXISTS"
                }
            
            original_amount, _ = result
            
            # Determine approval level based on amount and fraud score
            approval_level = self._determine_approval_level(original_amount, fraud_score)
            
            # Insert recovery request
            cursor.execute("""
                INSERT INTO payment_recovery_requests
                (recovery_id, transaction_id, npi, original_payment_amount, recovery_amount,
                 fraud_risk_score, fraud_evidence, initiator, initiated_by, recovery_status,
                 approval_level, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                recovery_id, transaction_id, npi, original_amount, original_amount,
                fraud_score, json.dumps(fraud_evidence), initiator, initiated_by,
                "PENDING", approval_level
            ))
            
            # Log workflow stage
            self._log_workflow_stage(
                cursor,
                recovery_id,
                "INITIATED",
                "SUCCESS",
                f"Recovery initiated for ${original_amount:.2f} payment with {fraud_score:.1%} fraud risk",
                initiated_by
            )
            
            conn.commit()
            
            logger.info(f"✅ Recovery {recovery_id} initiated for transaction {transaction_id}")
            
            return {
                "recovery_id": recovery_id,
                "transaction_id": transaction_id,
                "npi": npi,
                "amount": original_amount,
                "status": "PENDING",
                "approval_level": approval_level
            }
            
        finally:
            conn.close()
    
    def approve_recovery(
        self,
        recovery_id: str,
        approver: str,
        notes: str = "",
        recovery_method: str = "RECOUPMENT"
    ) -> Dict:
        """
        Approve a recovery request.
        
        Args:
            recovery_id: Recovery request ID
            approver: Username of approver
            notes: Approval notes
            recovery_method: Method to use (RECOUPMENT, OFFSET, DEMAND_LETTER, LEGAL_ACTION)
            
        Returns:
            Updated recovery request details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE payment_recovery_requests
                SET recovery_status = 'APPROVED',
                    approver = ?,
                    approval_notes = ?,
                    recovery_method = ?,
                    recovery_initiated_date = datetime('now'),
                    updated_at = datetime('now')
                WHERE recovery_id = ?
            """, (approver, notes, recovery_method, recovery_id))
            
            self._log_workflow_stage(
                cursor,
                recovery_id,
                "APPROVED",
                "SUCCESS",
                f"Approved by {approver}. Method: {recovery_method}. Notes: {notes}",
                approver
            )
            
            conn.commit()
            
            logger.info(f"✅ Recovery {recovery_id} approved by {approver}")
            
            return {
                "recovery_id": recovery_id,
                "status": "APPROVED",
                "approver": approver,
                "recovery_method": recovery_method
            }
            
        finally:
            conn.close()
    
    def reject_recovery(
        self,
        recovery_id: str,
        rejector: str,
        notes: str = ""
    ) -> Dict:
        """
        Reject a recovery request.
        
        Args:
            recovery_id: Recovery request ID
            rejector: Username of rejector
            notes: Rejection reason
            
        Returns:
            Updated recovery request details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE payment_recovery_requests
                SET recovery_status = 'REJECTED',
                    approver = ?,
                    approval_notes = ?,
                    updated_at = datetime('now')
                WHERE recovery_id = ?
            """, (rejector, notes, recovery_id))
            
            self._log_workflow_stage(
                cursor,
                recovery_id,
                "REJECTED",
                "SUCCESS",
                f"Rejected by {rejector}. Reason: {notes}",
                rejector
            )
            
            conn.commit()
            
            logger.info(f"❌ Recovery {recovery_id} rejected by {rejector}")
            
            return {
                "recovery_id": recovery_id,
                "status": "REJECTED",
                "rejector": rejector
            }
            
        finally:
            conn.close()
    
    def get_recovery_requests(
        self,
        status: Optional[str] = None,
        npi: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recovery requests with optional filters.
        
        Args:
            status: Filter by status (PENDING, APPROVED, etc.)
            npi: Filter by provider NPI
            limit: Maximum number of results
            
        Returns:
            List of recovery request dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT r.*, p.provider_name, p.provider_state,
                       t.payment_date, t.payment_status, t.payment_processed_date
                FROM payment_recovery_requests r
                LEFT JOIN provider_financial_profiles p ON r.npi = p.npi
                LEFT JOIN payment_transactions t ON r.transaction_id = t.transaction_id
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND r.recovery_status = ?"
                params.append(status)
            
            if npi:
                query += " AND r.npi = ?"
                params.append(npi)
            
            query += " ORDER BY r.created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
            
        finally:
            conn.close()
    
    def _determine_approval_level(self, amount: float, fraud_score: float) -> str:
        """
        Determine required approval level based on amount and fraud score.
        
        Args:
            amount: Payment amount
            fraud_score: Fraud risk score (0-1)
            
        Returns:
            Approval level string
        """
        if amount > 100000 or fraud_score > 0.95:
            return "LEGAL_REVIEW"
        elif amount > 10000 or fraud_score > 0.85:
            return "L2_APPROVAL"
        else:
            return "L1_REVIEW"
    
    def _log_workflow_stage(
        self,
        cursor: sqlite3.Cursor,
        recovery_id: str,
        stage: str,
        status: str,
        notes: str,
        actor: str
    ):
        """
        Log a workflow stage transition.
        
        Args:
            cursor: Database cursor
            recovery_id: Recovery request ID
            stage: Workflow stage
            status: Stage status
            notes: Stage notes
            actor: Actor who performed action
        """
        cursor.execute("""
            INSERT INTO recovery_workflow_logs
            (recovery_id, stage, status, notes, actor, timestamp)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (recovery_id, stage, status, notes, actor))
