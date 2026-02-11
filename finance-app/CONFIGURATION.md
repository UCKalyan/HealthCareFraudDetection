# Finance App Configuration Guide

## Overview

All hardcoded values have been extracted to a configuration system with sensible defaults. The system uses:
- **Config file** (optional): `config.yaml` in the finance-app directory
- **Environment variables**: Override config file values
- **Default fallbacks**: Built into the code if no config exists

## Configuration Structure

### Creating config.yaml (Optional)

The config file is optional. If not present, the system uses built-in defaults. Create `config.yaml` in the `finance-app/` directory:

```yaml
# Email Notification Configuration
email:
  enabled: true
  smtp:
    server: "smtp.gmail.com"
    port: 587
    use_tls: true

# Default Users (created on first run)
users:
  defaults:
    - username: "finance_manager"
      email: "finance-manager@company.com"
      role: "manager"
      department: "Finance"
    - username: "legal_admin"
      email: "legal@company.com"
      role: "legal"
      department: "Legal"
    - username: "cfo"
      email: "cfo@company.com"
      role: "executive"
      department: "Finance"
    - username: "fraud_team"
      email: "fraud-team@company.com"
      role: "analyst"
      department: "Fraud Detection"

# Recovery Workflow Configuration
recovery:
  # Approval level thresholds
  approval_levels:
    legal_review:
      min_amount: 100000      # >= $100,000
      min_fraud_score: 0.95    # >= 95% fraud risk
    l2_approval:
      min_amount: 10000        # >= $10,000
      min_fraud_score: 0.85    # >= 85% fraud risk
    # L1_REVIEW is default for everything else
  
  # AI recommendation thresholds
  ai_recommendations:
    approve_threshold: 0.85    # >= 85% → APPROVE
    review_threshold: 0.70     # >= 70% → REVIEW
    # < 70% → REJECT
  
  # Email notifications
  notifications:
    send_manager_approval_emails: true
    send_stakeholder_notifications: true

# Alert Configuration
alerts:
  auto_hold:
    enabled: true
    risk_threshold: 0.75       # Auto-hold if >= 75% risk
```

## Environment Variables

Environment variables **always override** config file values:

```bash
# Email SMTP (required for email functionality)
export SENDER_EMAIL="fraudguard@company.com"
export SENDER_PASSWORD="your-app-password"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export EMAIL_ENABLED="true"
```

## Configuration Priority

1. **Environment Variables** (highest priority)
2. **config.yaml file** (if exists)
3. **Built-in defaults** (fallback)

## Accessing Configuration in Code

```python
from src.utils.config import get_config

# Get config instance
config = get_config()

# Get specific values
email_cfg = config.get_email_config()
users_cfg = config.get_users_config()
recovery_cfg = config.get_recovery_config()

# Or use dot notation
smtp_server = config.get('email.smtp.server', 'smtp.gmail.com')
min_amount = config.get('recovery.approval_levels.l2_approval.min_amount', 10000)
```

## Configurable Values

### Email Settings
- SMTP server, port, TLS
- Email enabled/disabled globally

### Default Users
- Username, email, role, department
- Can add unlimited users to the list

### Recovery Thresholds
- **Legal Review**: Amount and fraud score minimums
- **L2 Approval**: Amount and fraud score minimums
- **L1 Review**: Everything else (no config needed)

### AI Recommendations
- **Approve threshold**: Fraud score for APPROVE recommendation
- **Review threshold**: Fraud score for REVIEW recommendation
- Below review threshold → REJECT

### Auto-Hold
- Risk threshold for automatic payment holds
- Enable/disable auto-hold feature

## Example Customizations

### Change Legal Review threshold to $50K:
```yaml
recovery:
  approval_levels:
    legal_review:
      min_amount: 50000
```

### Make AI more conservative (higher bar for approval):
```yaml
recovery:
  ai_recommendations:
    approve_threshold: 0.90  # Changed from 0.85
    review_threshold: 0.75   # Changed from 0.70
```

### Add custom users:
```yaml
users:
  defaults:
    - username: "regional_manager"
      email: "region1@company.com"
      role: "manager"
      department: "Finance"
    # ... other users
```

## Validation

The system validates configuration on startup:
- Email credentials checked before sending
- Config file syntax validated on load
- Invalid values fall back to defaults  
- All errors logged to application logs

## No Config File Needed

The system works perfectly fine without a `config.yaml` file. All defaults are sensible for production use. Simply set the required environment variables:

```bash
export SENDER_EMAIL="your-email@company.com"
export SENDER_PASSWORD="your-app-password"
```

And the system is ready to go!
