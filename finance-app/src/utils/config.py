"""
Configuration loader for Finance Application
Loads and provides access to all configurable parameters
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Default configuration values (fallback if config.yaml doesn't exist)
DEFAULT_CONFIG = {
    'email': {
        'enabled': True,
        'smtp': {
            'server': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True
        },
        'templates': {
            'recovery_approval_subject': 'Recovery Approval Required - Case #{case_id}',
            'stakeholder_notification_subject': 'Recovery Update - Case #{case_id}',
            'daily_summary_subject': 'FraudGuard Daily Summary - Automated Payment Holds'
        }
    },
    'users': {
        'defaults': [
            {
                'username': 'finance_manager',
                'email': 'finance-manager@company.com',
                'role': 'manager',
                'department': 'Finance'
            },
            {
                'username': 'legal_admin',
                'email': 'legal@company.com',
                'role': 'legal',
                'department': 'Legal'
            },
            {
                'username': 'cfo',
                'email': 'cfo@company.com',
                'role': 'executive',
                'department': 'Finance'
            },
            {
                'username': 'fraud_team',
                'email': 'fraud-team@company.com',
                'role': 'analyst',
                'department': 'Fraud Detection'
            }
        ]
    },
    'recovery': {
        'approval_levels': {
            'legal_review': {
                'min_amount': 100000,
                'min_fraud_score': 0.95
            },
            'l2_approval': {
                'min_amount': 10000,
                'min_fraud_score': 0.85
            }
        },
        'ai_recommendations': {
            'approve_threshold': 0.85,
            'review_threshold': 0.70
        },
        'notifications': {
            'send_manager_approval_emails': True,
            'send_stakeholder_notifications': True,
            'approval_email_recipients': {
                'L1_REVIEW': 'manager',
                'L2_APPROVAL': 'executive',
                'LEGAL_REVIEW': 'legal'
            },
            'stakeholder_departments': ['Legal', 'Fraud Detection']
        }
    },
    'alerts': {
        'daily_summary': {
            'enabled': True,
            'send_time': '08:00',
            'recipients_by_role': ['executive', 'manager']
        },
        'auto_hold': {
            'enabled': True,
            'risk_threshold': 0.75,
            'notification_recipients': ['manager', 'executive']
        }
    },
    'auto_approval': {
        'enabled': True,
        'l1_auto_approve': {
            'enabled': True,
            'min_fraud_score': 0.90,
            'max_amount': 5000,
            'recovery_method': 'RECOUPMENT'
        },
        'notification_tiers': {
            'l1_manual': {
                'min_fraud_score': 0.85,
                'max_fraud_score': 0.89,
                'min_amount': 5000,
                'max_amount': 10000,
                'recipients': ['manager']
            },
            'l2_approval': {
                'min_fraud_score': 0.85,
                'max_fraud_score': 0.95,
                'min_amount': 10000,
                'max_amount': 100000,
                'recipients': ['executive']
            },
            'legal_review': {
                'min_fraud_score': 0.95,
                'min_amount': 100000,
                'recipients': ['legal', 'executive']
            }
        },
        'daily_summary': {
            'enabled': True,
            'send_time': '08:00',
            'recipients_by_role': ['executive', 'manager', 'legal'],
            'include_stats': [
                'total_recoveries_initiated',
                'auto_approved_count',
                'pending_manual_review',
                'total_amount_recovered',
                'auto_approval_rate'
            ]
        }
    }
}


class Config:
    """Configuration manager with fallback to defaults"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config.yaml file. If None, looks in standard locations.
        """
        self.config = DEFAULT_CONFIG.copy()
        
        if config_path is None:
            # Try standard locations
            possible_paths = [
                Path(__file__).parent.parent / 'config.yaml',
                Path(__file__).parent.parent.parent / 'config.yaml',
                Path('config.yaml')
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                    # Deep merge user config with defaults
                    self.config = self._deep_merge(self.config, user_config)
                    logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")
        else:
            logger.info("No config file found. Using default configuration.")
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., 'email.smtp.server')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_email_config(self) -> Dict:
        """Get email configuration"""
        return self.config.get('email', {})
    
    def get_users_config(self) -> Dict:
        """Get users configuration"""
        return self.config.get('users', {})
    
    def get_recovery_config(self) -> Dict:
        """Get recovery workflow configuration"""
        return self.config.get('recovery', {})
    
    def get_alerts_config(self) -> Dict:
        """Get alerts configuration"""
        return self.config.get('alerts', {})


# Global config instance
_config = None

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get global configuration instance.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reload_config(config_path: Optional[str] = None):
    """Reload configuration from file"""
    global _config
    _config = Config(config_path)
    return _config
