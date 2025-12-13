"""
User and notification configuration management for Finance App
"""

import sqlite3
import logging
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "databases" / "users.db"

# Import config system
try:
    from .config import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.warning("Config module not available, using hardcoded defaults")


def get_default_users():
    """Get default users from config or fallback to hardcoded"""
    if CONFIG_AVAILABLE:
        config = get_config()
        users_cfg = config.get_users_config()
        return users_cfg.get('defaults', [])
    else:
        # Fallback hardcoded defaults
        return [
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
                'department': 'Finance  '
            },
            {
                'username': 'fraud_team',
                'email': 'fraud-team@company.com',
                'role': 'analyst',
                'department': 'Fraud Detection'
            }
        ]


def init_users_db():
    """Initialize users database with email addresses for notifications"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create users table with email
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create notification preferences table
        c.execute('''
            CREATE TABLE IF NOT EXISTS notification_preferences (
                pref_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Insert default users if table is empty
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            default_users = get_default_users()
            
            # Convert to tuples for executemany
            user_tuples = [
                (u['username'], u['email'], u['role'], u.get('department'))
                for u in default_users
            ]
            
            c.executemany('''
                INSERT INTO users (username, email, role, department)
                VALUES (?, ?, ?, ?)
            ''', user_tuples)
            
            logger.info(f"Initialized users database with {len(user_tuples)} default users")
        
        conn.commit()
        conn.close()
        logger.info("Users database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize users database: {e}")
        return False


def get_user_email(username: str) -> Optional[str]:
    """Get user's email address by username"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT email FROM users WHERE username = ? AND active = 1", (username,))
        result = c.fetchone()
        conn.close()
        
        return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Failed to get user email: {e}")
        return None


def get_emails_by_role(role: str) -> List[str]:
    """Get all email addresses for users with specific role"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT email FROM users WHERE role = ? AND active = 1", (role,))
        results = c.fetchall()
        conn.close()
        
        return [r[0] for r in results]
        
    except Exception as e:
        logger.error(f"Failed to get emails by role: {e}")
        return []


def get_emails_by_department(department: str) -> List[str]:
    """Get all email addresses for users in specific department"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT email FROM users WHERE department = ? AND active = 1", (department,))
        results = c.fetchall()
        conn.close()
        
        return [r[0] for r in results]
        
    except Exception as e:
        logger.error(f"Failed to get emails by department: {e}")
        return []


def add_user(username: str, email: str, role: str, department: Optional[str] = None) -> bool:
    """Add a new user to the system"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO users (username, email, role, department)
            VALUES (?, ?, ?, ?)
        ''', (username, email, role, department))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added user: {username} ({email})")
        return True
        
    except sqlite3.IntegrityError:
        logger.warning(f"User {username} already exists")
        return False
    except Exception as e:
        logger.error(f"Failed to add user: {e}")
        return False


def update_user_email(username: str, new_email: str) -> bool:
    """Update user's email address"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, username))
        
        conn.commit()
        affected = c.rowcount
        conn.close()
        
        if affected > 0:
            logger.info(f"Updated email for {username} to {new_email}")
            return True
        else:
            logger.warning(f"User {username} not found")
            return False
            
    except Exception as e:
        logger.error(f"Failed to update user email: {e}")
        return False


# Initialize database on module import
init_users_db()
