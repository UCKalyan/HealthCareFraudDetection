"""
Add Recovery Tables to Finance Database

Adds missing payment_recovery_requests and recovery_workflow_logs tables
to the existing finance database.

Author: Healthcare Fraud Detection Team
Date: 2025-12-12
"""

import sqlite3
from pathlib import Path
import sys

def add_recovery_tables(db_path):
    """Add recovery management tables to finance database"""
    print("=" * 80)
    print("Adding Recovery Tables to Finance Database")
    print("=" * 80)
    print(f"Database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Payment Recovery Requests Table
        print("\n[1/3] Creating payment_recovery_requests table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_recovery_requests (
                recovery_id TEXT PRIMARY KEY,
                transaction_id TEXT NOT NULL,
                npi BIGINT NOT NULL,
                
                -- Financial details
                original_payment_amount REAL,
                recovery_amount REAL,
                
                -- Fraud assessment
                fraud_risk_score REAL,
                fraud_evidence TEXT,  -- JSON with investigation findings, SHAP values, etc.
                
                -- Initiator info
                initiator TEXT,  -- 'fraud_detection_agent' or 'analyst_manual'
                initiated_by TEXT,  -- Username or 'system'
                
                -- Recovery status
                recovery_status TEXT,  -- PENDING, APPROVED, REJECTED, IN_PROCESS, COMPLETED
                approval_level TEXT,  -- L1_REVIEW, L2_APPROVAL, LEGAL_REVIEW
                
                -- Approval details
                approver TEXT,
                approval_notes TEXT,
                recovery_method TEXT,  -- RECOUPMENT, OFFSET, DEMAND_LETTER, LEGAL_ACTION
                
                -- Dates
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recovery_initiated_date TIMESTAMP,
                recovery_completed_date TIMESTAMP,
                
                FOREIGN KEY (transaction_id) REFERENCES payment_transactions(transaction_id),
                FOREIGN KEY (npi) REFERENCES provider_financial_profiles(npi)
            )
        ''')
        print("✓ Created payment_recovery_requests table")
        
        # 2. Recovery Workflow Logs Table
        print("\n[2/3] Creating recovery_workflow_logs table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recovery_workflow_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recovery_id TEXT NOT NULL,
                stage TEXT,  -- INITIATED, EMAIL_SENT, APPROVED, REJECTED, IN_PROCESS, COMPLETED
                status TEXT,  -- SUCCESS, FAILED, PENDING
                notes TEXT,
                actor TEXT,  -- Username or 'system' or 'ai_agent_auto'
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (recovery_id) REFERENCES payment_recovery_requests(recovery_id)
            )
        ''')
        print("✓ Created recovery_workflow_logs table")
        
        # 3. Create indexes for performance
        print("\n[3/3] Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_recovery_requests_transaction ON payment_recovery_requests(transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_recovery_requests_npi ON payment_recovery_requests(npi)",
            "CREATE INDEX IF NOT EXISTS idx_recovery_requests_status ON payment_recovery_requests(recovery_status)",
            "CREATE INDEX IF NOT EXISTS idx_recovery_workflow_recovery ON recovery_workflow_logs(recovery_id)",
            "CREATE INDEX IF NOT EXISTS idx_recovery_workflow_stage ON recovery_workflow_logs(stage)"
        ]
        
        for idx in indexes:
            cursor.execute(idx)
        
        print(f"✓ Created {len(indexes)} indexes")
        
        conn.commit()
        
        # Verify tables exist
        print("\n" + "=" * 80)
        print("Verification")
        print("=" * 80)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%recovery%'")
        tables = cursor.fetchall()
        print("\nRecovery tables in database:")
        for table in tables:
            print(f"  ✓ {table[0]}")
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"    Records: {count:,}")
        
        print("\n" + "=" * 80)
        print("✅ Recovery tables added successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add recovery tables to finance database')
    parser.add_argument('--db-path', default='../../shared-data/finance_app.db', 
                       help='Database path (default: ../../shared-data/finance_app.db)')
    
    args = parser.parse_args()
    
    db_path = Path(args.db_path)
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Please provide the correct path using --db-path argument")
        sys.exit(1)
    
    add_recovery_tables(db_path)

if __name__ == '__main__':
    main()
