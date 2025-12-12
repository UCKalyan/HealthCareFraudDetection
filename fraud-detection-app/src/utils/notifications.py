import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.utils.config_loader import load_config

logger = logging.getLogger(__name__)

def send_decision_email(to_email, decision, case_details):
    """
    Sends an email notification using Gmail SMTP.
    """
    try:
        config = load_config('config.yaml')
        email_config = config.get('email', {})
        
        sender_email = email_config.get('sender_email')
        sender_password = email_config.get('sender_password')
        
        if not sender_email or not sender_password or sender_email == "${GMAIL_USER}":
            logger.warning("Email credentials not set. Skipping email notification.")
            return False

        subject = f"Payment Decision: {decision} - {case_details['provider_name']} (NPI: {case_details['npi']})"
        
        body = f"""
        Payment Decision Notification
        -----------------------------
        Provider: {case_details['provider_name']}
        NPI: {case_details['npi']}
        
        Decision: {decision}
        
        Supervisor Notes:
        {case_details.get('notes', 'No notes provided.')}
        
        Timestamp: {case_details.get('timestamp', 'Now')}
        
        Action Required:
        Please proceed with the above decision immediately.
        
        -----------------------------
        Payment Integrity Team
        """
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        
        logger.info(f"Email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
