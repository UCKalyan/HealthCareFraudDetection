"""
Recovery workflow timeline and details fetching
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime


def get_recovery_workflow_details(db_path: str, recovery_id: str) -> Dict:
    """
    Get complete recovery workflow details including timeline, emails, and approval status.
    
    Args:
        db_path: Path to finance database
        recovery_id: Recovery request ID
        
    Returns:
        Dictionary with complete workflow information
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get recovery request details
        cursor.execute("""
            SELECT r.*, p.provider_name, t.payment_amount, t.payment_status
            FROM payment_recovery_requests r
            LEFT JOIN provider_financial_profiles p ON r.npi = p.npi
            LEFT JOIN payment_transactions t ON r.transaction_id = t.transaction_id
            WHERE r.recovery_id = ?
        """, (recovery_id,))
        
        recovery = cursor.fetchone()
        if not recovery:
            return {"error": "Recovery request not found"}
        
        recovery_dict = dict(recovery)
        
        # Get workflow logs (timeline)
        cursor.execute("""
            SELECT stage, status, notes, actor, timestamp
            FROM recovery_workflow_logs
            WHERE recovery_id = ?
            ORDER BY timestamp ASC
        """, (recovery_id,))
        
        timeline = [dict(row) for row in cursor.fetchall()]
        
        # Determine approval status and pending actions
        status = recovery_dict['recovery_status']
        approval_level = recovery_dict['approval_level']
        approver = recovery_dict.get('approver')
        
        # Determine who needs to approve
        pending_approvers = []
        emails_sent_to = []
        
        if status == 'PENDING':
            if approval_level == 'L1_REVIEW':
                pending_approvers = ['Finance Manager']
                emails_sent_to = ['finance_manager@company.com']
            elif approval_level == 'L2_APPROVAL':
                pending_approvers = ['CFO / Executive']
                emails_sent_to = ['cfo@company.com']
            elif approval_level == 'LEGAL_REVIEW':
                pending_approvers = ['Legal Team', 'CFO']
                emails_sent_to = ['legal@company.com', 'cfo@company.com']
        
        # Build comprehensive response
        workflow_details = {
            **recovery_dict,
            'timeline': timeline,
            'pending_approvers': pending_approvers,
            'emails_sent_to': emails_sent_to,
            'workflow_summary': build_workflow_summary(recovery_dict, timeline, status, approver),
            'next_action': determine_next_action(status, approval_level, approver),
            'email_notifications_sent': len(timeline) > 0,  # Check if any workflow logs exist
            'approval_reason': recovery_dict.get('approval_notes', 'N/A'),
            'auto_approved': approver == 'ai_agent_auto'
        }
        
        return workflow_details
        
    finally:
        conn.close()


def build_workflow_summary(recovery: Dict, timeline: List[Dict], status: str, approver: Optional[str]) -> List[Dict]:
    """
    Build human-readable workflow summary.
    
    Returns:
        List of workflow events with timestamps and descriptions
    """
    summary = []
    
    # Event 1: Initiation
    summary.append({
        'icon': '🚨',
        'event': 'Recovery Initiated',
        'description': f"Recovery request created for fraud score {recovery.get('fraud_risk_score', 0):.1%}",
        'timestamp': recovery.get('created_at'),
        'actor': recovery.get('initiated_by', 'System')
    })
    
    # Events from timeline
    for log in timeline:
        stage = log['stage']
        
        if 'email' in stage.lower() or 'notification' in stage.lower():
            summary.append({
                'icon': '📧',
                'event': 'Email Sent',
                'description': log['notes'],
                'timestamp': log['timestamp'],
                'actor': 'System'
            })
        elif 'approval' in stage.lower() or 'review' in stage.lower():
            summary.append({
                'icon': '👁️',
                'event': 'Under Review',
                'description': log['notes'],
                'timestamp': log['timestamp'],
                'actor': log.get('actor', 'System')
            })
    
    # Event: Approval/Rejection
    if status == 'APPROVED':
        summary.append({
            'icon': '✅',
            'event': 'Approved',
            'description': f"Approved by {approver or 'Unknown'}. " + (recovery.get('approval_notes', '') or 'No notes provided.'),
            'timestamp': recovery.get('updated_at'),
            'actor': approver or 'Unknown'
        })
        
        # Stakeholder notification
        summary.append({
            'icon': '📨',
            'event': 'Stakeholders Notified',
            'description': 'Recovery approval notification sent to Legal and Fraud Detection teams',
            'timestamp': recovery.get('updated_at'),
            'actor': 'System'
        })
        
    elif status == 'REJECTED':
        summary.append({
            'icon': '❌',
            'event': 'Rejected',
            'description': f"Rejected by {approver or 'Unknown'}. " + (recovery.get('approval_notes', '') or 'No notes provided.'),
            'timestamp': recovery.get('updated_at'),
            'actor': approver or 'Unknown'
        })
    elif status == 'PENDING':
        summary.append({
            'icon': '⏳',
            'event': 'Awaiting Approval',
            'description': f"Pending {recovery.get('approval_level', 'review')} approval",
            'timestamp': datetime.now().isoformat(),
            'actor': 'System'
        })
    
    return summary


def determine_next_action(status: str, approval_level: str, approver: Optional[str]) -> str:
    """Determine what the next action should be"""
    
    if status == 'APPROVED':
        return "Recovery approved - awaiting execution"
    elif status == 'REJECTED':
        return "Case closed - recovery rejected"
    elif status == 'PENDING':
        if approval_level == 'L1_REVIEW':
            return "Awaiting Finance Manager approval"
        elif approval_level == 'L2_APPROVAL':
            return "Awaiting CFO/Executive approval"
        elif approval_level == 'LEGAL_REVIEW':
            return "Awaiting Legal Team review and approval"
        else:
            return "Awaiting approval"
    else:
        return "Unknown status"
