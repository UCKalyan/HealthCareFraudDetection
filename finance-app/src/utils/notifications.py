"""
Email Notification Service for Finance Application
Handles sending emails for recovery approvals, stakeholder notifications, and alerts.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Import config system
try:
    from .config import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.warning("Config module not available, using environment variables only")


def load_email_config():
    """Load email configuration from config file or environment variables"""
    if CONFIG_AVAILABLE:
        config = get_config()
        email_cfg = config.get_email_config()
        
        # Get SMTP settings from config
        smtp_cfg = email_cfg.get('smtp', {})
        
        return {
            'smtp_server': os.getenv('SMTP_SERVER', smtp_cfg.get('server', 'smtp.gmail.com')),
            'smtp_port': int(os.getenv('SMTP_PORT', smtp_cfg.get('port', 587))),
            'sender_email': os.getenv('SENDER_EMAIL'),
            'sender_password': os.getenv('SENDER_PASSWORD'),
            'enabled': os.getenv('EMAIL_ENABLED', str(email_cfg.get('enabled', 'true'))).lower() == 'true',
            'use_tls': smtp_cfg.get('use_tls', True)
        }
    else:
        # Fallback to environment variables only
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'sender_email': os.getenv('SENDER_EMAIL'),
            'sender_password': os.getenv('SENDER_PASSWORD'),
            'enabled': os.getenv('EMAIL_ENABLED', 'true').lower() == 'true',
            'use_tls': True
        }
    
    # Validate required fields
    if not config['sender_email'] or not config['sender_password']:
        logger.warning("Email credentials not configured. Email notifications will be disabled.")
        config['enabled'] = False
    
    return config



def send_recovery_approval_email(
    to_email: str,
    case_id: str,
    provider_name: str,
    npi: str,
    amount: float,
    risk_score: float,
    ai_recommendation: str,
    evidence_path: Optional[str] = None
) -> bool:
    """
    Send recovery approval request email to finance manager.
    
    Args:
        to_email: Manager's email address
        case_id: Recovery case ID
        provider_name: Provider name
        npi: Provider NPI
        amount: Recovery amount
        risk_score: Fraud risk score
        ai_recommendation: AI agent recommendation
        evidence_path: Optional path to fraud report PDF
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    config = load_email_config()
    
    if not config['enabled']:
        logger.info(f"Email notifications disabled. Skipping recovery approval email for {case_id}")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config['sender_email']
        msg['To'] = to_email
        msg['Subject'] = f"Recovery Approval Required - Case #{case_id}"
        
        # Email body
        body = f"""
Recovery Approval Required
========================================

CASE INFORMATION:
- Case ID: {case_id}
- Provider: {provider_name} (NPI: {npi})
- Amount: ${amount:,.2f}
- Risk Score: {risk_score:.2f}

AI RECOMMENDATION: {ai_recommendation}

ACTIONS:
To approve this recovery, please log into the Finance App:
https://localhost:8001/recovery

Evidence: {'Attached' if evidence_path else 'View in Finance App'}

========================================
This is an automated message from the FraudGuard Finance System.
Please review and respond within 48 hours.
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach evidence if provided
        if evidence_path and Path(evidence_path).exists():
            try:
                with open(evidence_path, 'rb') as f:
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={Path(evidence_path).name}')
                    msg.attach(part)
            except Exception as e:
                logger.warning(f"Could not attach evidence file: {e}")
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        logger.info(f"Recovery approval email sent to {to_email} for case {case_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send recovery approval email: {e}")
        return False


def send_stakeholder_notification(
    to_emails: List[str],
    subject: str,
    message: str,
    case_id: Optional[str] = None
) -> bool:
    """
    Send notification to stakeholders (legal team, executives, etc.)
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject
        message: Email body message
        case_id: Optional case ID for reference
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    config = load_email_config()
    
    if not config['enabled']:
        logger.info("Email notifications disabled. Skipping stakeholder notification.")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config['sender_email']
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        body = f"""
{message}

{'Case ID: ' + case_id if case_id else ''}

========================================
FraudGuard Finance System - Automated Notification
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        logger.info(f"Stakeholder notification sent to {len(to_emails)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send stakeholder notification: {e}")
        return False


def send_daily_summary_email(
    to_emails: List[str],
    holds_successful: int,
    holds_failed: int,
    total_amount_held: float,
    high_risk_providers: int
) -> bool:
    """
    Send daily summary email for automated payment holds.
    
    Args:
        to_emails: List of recipient emails
        holds_successful: Number of successful holds
        holds_failed: Number of failed holds
        total_amount_held: Total amount of payments held
        high_risk_providers: Number of high-risk providers detected
        
    Returns:
        bool: True if sent successfully
    """
    config = load_email_config()
    
    if not config['enabled']:
        logger.info("Email notifications disabled. Skipping daily summary.")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config['sender_email']
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = "FraudGuard Daily Summary - Automated Payment Holds"
        
        body = f"""
Daily Payment Hold Summary
========================================

SUMMARY:
- Successful Holds: {holds_successful}
- Failed Holds: {holds_failed}
- Total Amount Held: ${total_amount_held:,.2f}
- High-Risk Providers Detected: {high_risk_providers}

Success Rate: {(holds_successful / (holds_successful + holds_failed) * 100):.1f}%

ACTION REQUIRED:
Please review held payments in the Finance App:
https://localhost:8001/payments?status=HELD

========================================
FraudGuard Finance System - Daily Report
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        logger.info(f"Daily summary email sent to {len(to_emails)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send daily summary email: {e}")
        return False
