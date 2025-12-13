"""
Daily Summary Scheduler for Finance App
Sends daily recovery summary emails to stakeholders
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

try:
    from utils.config import get_config
    from utils.notifications import send_daily_summary_email
    from utils.users import get_emails_by_role
    CONFIG_AVAILABLE = True
except ImportError:
    logger.warning("Config or notifications not available for daily summary")
    CONFIG_AVAILABLE = False


class DailySummaryScheduler:
    """Schedules and sends daily recovery summary emails"""
    
    def __init__(self, db_path: str):
        """
        Initialize daily summary scheduler.
        
        Args:
            db_path: Path to Finance database
        """
        self.db_path = db_path
        self.scheduler_thread = None
        self.running = False
    
    def get_daily_stats(self) -> Dict:
        """Get recovery statistics for the past 24 hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get stats from last 24 hours
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Total recoveries initiated
            cursor.execute("""
                SELECT COUNT(*) FROM payment_recovery_requests 
                WHERE created_at >= ?
            """, (yesterday,))
            total_initiated = cursor.fetchone()[0]
            
            # Auto-approved count
            cursor.execute("""
                SELECT COUNT(*) FROM payment_recovery_requests 
                WHERE created_at >= ? AND approver = 'ai_agent_auto'
            """, (yesterday,))
            auto_approved = cursor.fetchone()[0]
            
            # Pending manual review
            cursor.execute("""
                SELECT COUNT(*) FROM payment_recovery_requests 
                WHERE recovery_status = 'PENDING'
            """)
            pending_review = cursor.fetchone()[0]
            
            # Total amount recovered (approved cases)
            cursor.execute("""
                SELECT COALESCE(SUM(recovery_amount), 0) 
                FROM payment_recovery_requests 
                WHERE recovery_status = 'APPROVED' AND created_at >= ?
            """, (yesterday,))
            total_recovered = cursor.fetchone()[0]
            
            # Auto-approval rate
            auto_approval_rate = (auto_approved / total_initiated * 100) if total_initiated > 0 else 0
            
            return {
                'total_recoveries_initiated': total_initiated,
                'auto_approved_count': auto_approved,
                'pending_manual_review': pending_review,
                'total_amount_recovered': float(total_recovered),
                'auto_approval_rate': auto_approval_rate,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
        finally:
            conn.close()
    
    def send_daily_summary(self):
        """Send daily summary email to all stakeholders"""
        if not CONFIG_AVAILABLE:
            logger.warning("Cannot send daily summary - config not available")
            return
        
        try:
            config = get_config()
            auto_cfg = config.get('auto_approval', {})
            summary_cfg = auto_cfg.get('daily_summary', {})
            
            if not summary_cfg.get('enabled', False):
                logger.info("Daily summary disabled in config")
                return
            
            # Get statistics
            stats = self.get_daily_stats()
            
            # Get recipient emails
            recipient_roles = summary_cfg.get('recipients_by_role', ['executive', 'manager'])
            all_emails = []
            
            for role in recipient_roles:
                emails = get_emails_by_role(role)
                all_emails.extend(emails)
            
            # Remove duplicates
            all_emails = list(set(all_emails))
            
            if not all_emails:
                logger.warning("No recipient emails found for daily summary")
                return
            
            # Prepare email content
            subject = f"FraudGuard Daily Recovery Summary - {stats['date']}"
            
            message = f"""
Daily Recovery Summary for {stats['date']}
========================================

RECOVERY STATISTICS (Last 24 Hours):
- Total Recoveries Initiated: {stats['total_recoveries_initiated']}
- Auto-Approved Cases: {stats['auto_approved_count']}
- Pending Manual Review: {stats['pending_manual_review']}
- Total Amount Recovered: ${stats['total_amount_recovered']:,.2f}
- Auto-Approval Rate: {stats['auto_approval_rate']:.1f}%

HIGHLIGHTS:
- {stats['auto_approved_count']} low-risk cases were automatically approved
- {stats['pending_manual_review']} cases require manual review
- Automation handling {stats['auto_approval_rate']:.1f}% of L1 cases

ACTION REQUIRED:
Please review pending cases in the Finance App:
https://localhost:8001/recovery

========================================
This is an automated daily summary from FraudGuard Finance System.
"""
            
            # Send email (using stakeholder notification function)
            from utils.notifications import send_stakeholder_notification
            send_stakeholder_notification(
                to_emails=all_emails,
                subject=subject,
                message=message,
                case_id=None
            )
            
            logger.info(f"📊 Daily summary sent to {len(all_emails)} recipients: {stats}")
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
    
    def start(self):
        """Start the daily summary scheduler"""
        if not CONFIG_AVAILABLE:
            logger.warning("Daily summary scheduler disabled - config not available")
            return
        
        try:
            config = get_config()
            auto_cfg = config.get('auto_approval', {})
            summary_cfg = auto_cfg.get('daily_summary', {})
            
            if not summary_cfg.get('enabled', False):
                logger.info("Daily summary scheduler disabled in config")
                return
            
            send_time = summary_cfg.get('send_time', '08:00')
            
            # Schedule daily summary
            schedule.every().day.at(send_time).do(self.send_daily_summary)
            
            # Start scheduler thread
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info(f"📅 Daily summary scheduler started - will send at {send_time} daily")
            
        except Exception as e:
            logger.error(f"Failed to start daily summary scheduler: {e}")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the daily summary scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("📅 Daily summary scheduler stopped")


# Global scheduler instance
_scheduler = None

def get_scheduler(db_path: str = None) -> DailySummaryScheduler:
    """Get global scheduler instance"""
    global _scheduler
    if _scheduler is None and db_path:
        _scheduler = DailySummaryScheduler(db_path)
    return _scheduler
