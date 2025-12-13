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
from pathlib import Path
import sys

# Add src/utils to path for notifications import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.notifications import send_recovery_approval_email, send_stakeholder_notification
    from utils.users import get_user_email, get_emails_by_role, get_emails_by_department
    from utils.config import get_config
    EMAIL_ENABLED = True
except ImportError as e:
    logger.warning(f"Email notifications or config not available: {e}")
    EMAIL_ENABLED = False

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
            
            # Send email notification to finance manager
            if EMAIL_ENABLED and approval_level in ["L1_REVIEW", "L2_APPROVAL"]:
                try:
                    # Get provider name
                    cursor_temp = conn.cursor()
                    cursor_temp.execute("SELECT provider_name FROM provider_financial_profiles WHERE npi = ?", (npi,))
                    provider_result = cursor_temp.fetchone()
                    provider_name = provider_result[0] if provider_result else f"Provider {npi}"
                    
                    # Get manager email based on approval level
                    if approval_level == "L2_APPROVAL":
                        manager_emails = get_emails_by_role("executive")  # CFO for L2
                    else:
                        manager_emails = get_emails_by_role("manager")  # Finance manager for L1
                    
                    # Determine AI recommendation based on fraud score (from config)
                    try:
                        config = get_config()
                        recovery_cfg = config.get_recovery_config()
                        ai_cfg = recovery_cfg.get('ai_recommendations', {})
                        approve_threshold = ai_cfg.get('approve_threshold', 0.85)
                        review_threshold = ai_cfg.get('review_threshold', 0.70)
                    except:
                        approve_threshold, review_threshold = 0.85, 0.70
                    
                    if fraud_score >= approve_threshold:
                        ai_recommendation = "APPROVE"
                    elif fraud_score >= review_threshold:
                        ai_recommendation = "REVIEW"
                    else:
                        ai_recommendation = "REJECT"
                    
                    # Send email to each manager
                    for manager_email in manager_emails:
                        send_recovery_approval_email(
                            to_email=manager_email,
                            case_id=recovery_id,
                            provider_name=provider_name,
                            npi=str(npi),
                            amount=original_amount,
                            risk_score=fraud_score,
                            ai_recommendation=ai_recommendation
                        )
                    
                    logger.info(f"📧 Recovery approval emails sent to {len(manager_emails)} managers")
                    
                except Exception as e:
                    logger.error(f"Failed to send recovery approval email: {e}")
            
            # Check if eligible for auto-approval
            if EMAIL_ENABLED:
                try:
                    config = get_config()
                    auto_cfg = config.get('auto_approval', {})
                    
                    if auto_cfg.get('enabled', False):
                        l1_auto_cfg = auto_cfg.get('l1_auto_approve', {})
                        
                        # Check if meets auto-approval criteria
                        if (l1_auto_cfg.get('enabled', False) and
                            approval_level == "L1_REVIEW" and
                            fraud_score >= l1_auto_cfg.get('min_fraud_score', 0.90) and
                            original_amount < l1_auto_cfg.get('max_amount', 5000)):
                            
                            # Auto-approve!
                            recovery_method = l1_auto_cfg.get('recovery_method', 'RECOUPMENT')
                            auto_result = self.approve_recovery(
                                recovery_id=recovery_id,
                                approver="ai_agent_auto",
                                notes=f"Auto-approved: High confidence ({fraud_score:.2%}), low amount (${original_amount:,.2f}), L1 criteria met",
                                recovery_method=recovery_method
                            )
                            
                            logger.info(f"🤖 Auto-approved recovery {recovery_id}: ${original_amount:,.2f} at {fraud_score:.2%} confidence")
                            
                            return {
                                "recovery_id": recovery_id,
                                "transaction_id": transaction_id,
                                "npi": npi,
                                "amount": original_amount,
                                "status": "AUTO_APPROVED",
                                "approval_level": approval_level,
                                "auto_approved": True
                            }
                            
                except Exception as e:
                    logger.error(f"Failed to check auto-approval: {e}")
            
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
            
            # Send stakeholder notifications
            if EMAIL_ENABLED:
                try:
                    # Get recovery details
                    cursor_temp = conn.cursor()
                    cursor_temp.execute("""
                        SELECT r.recovery_amount, r.npi, p.provider_name
                        FROM payment_recovery_requests r
                        LEFT JOIN provider_financial_profiles p ON r.npi = p.npi
                        WHERE r.recovery_id = ?
                    """, (recovery_id,))
                    result = cursor_temp.fetchone()
                    
                    if result:
                        amount, npi, provider_name = result
                        
                        # Notify legal team
                        legal_emails = get_emails_by_department("Legal")
                        if legal_emails:
                            send_stakeholder_notification(
                                to_emails=legal_emails,
                                subject=f"Recovery Approved - ${amount:,.2f}",
                                message=f"Recovery request for Provider {provider_name} (NPI: {npi}) has been approved for ${amount:,.2f} using {recovery_method}.\n\nApprover: {approver}\nNotes: {notes}",
                                case_id=recovery_id
                            )
                        
                        # Notify fraud team
                        fraud_emails = get_emails_by_department("Fraud Detection")
                        if fraud_emails:
                            send_stakeholder_notification(
                                to_emails=fraud_emails,
                                subject=f"Recovery Approved - Case #{recovery_id}",
                                message=f"Your fraud case has resulted in approved recovery of ${amount:,.2f} from Provider {provider_name} (NPI: {npi}).",
                                case_id=recovery_id
                            )
                        
                        logger.info(f"📧 Stakeholder notifications sent for recovery {recovery_id}")
                        
                except Exception as e:
                    logger.error(f"Failed to send stakeholder notifications: {e}")
            
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
        # Get thresholds from config
        if EMAIL_ENABLED:
            try:
                config = get_config()
                recovery_cfg = config.get_recovery_config()
                levels = recovery_cfg.get('approval_levels', {})
                
                # Legal review thresholds
                legal_cfg = levels.get('legal_review', {})
                legal_amount = legal_cfg.get('min_amount', 100000)
                legal_score = legal_cfg.get('min_fraud_score', 0.95)
                
                # L2 approval thresholds
                l2_cfg = levels.get('l2_approval', {})
                l2_amount = l2_cfg.get('min_amount', 10000)
                l2_score = l2_cfg.get('min_fraud_score', 0.85)
            except:
                # Fallback to defaults
                legal_amount, legal_score = 100000, 0.95
                l2_amount, l2_score = 10000, 0.85
        else:
            # Defaults when config not available
            legal_amount, legal_score = 100000, 0.95
            l2_amount, l2_score = 10000, 0.85
        
        # Determine level based on thresholds
        # Legal review: High amount OR very high risk (either condition)
        if amount > legal_amount or fraud_score > legal_score:
            return "LEGAL_REVIEW"
        # L2 approval: High amount AND high risk (both conditions required)
        elif amount > l2_amount and fraud_score > l2_score:
            return "L2_APPROVAL"
        # L1 review: Everything else
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
