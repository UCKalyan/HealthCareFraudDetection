"""
Finance Application - Database Schema and Loader

Creates SQLite database for autonomous Finance application with tables for:
- Payment transactions
- Provider financial profiles
- Agent decision logs
- MCP communication logs

Author: Healthcare Fraud Detection Team
Date: 2024-11-30
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import json


class FinanceDatabase:
    """Manages Finance application database"""
    
    def __init__(self, db_path='../../data/finance.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        print("=" * 80)
        print("Finance Application - Database Setup")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        
    def create_schema(self):
        """Create all database tables"""
        print("\n[1/5] Creating Database Schema...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Provider Financial Profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS provider_financial_profiles (
                npi BIGINT PRIMARY KEY,
                provider_name TEXT,
                provider_city TEXT,
                provider_state TEXT,
                provider_type TEXT,
                
                -- NPPES data
                nppes_org_name TEXT,
                nppes_address TEXT,
                nppes_city TEXT,
                nppes_state TEXT,
                nppes_zip TEXT,
                nppes_taxonomy TEXT,
                
                -- Part B aggregated
                partb_total_payment REAL,
                partb_total_services INTEGER,
                partb_total_beneficiaries INTEGER,
                partb_procedure_count INTEGER,
                
                -- Part D aggregated
                partd_total_drug_cost REAL,
                partd_total_claims INTEGER,
                partd_total_beneficiaries INTEGER,
                
                -- Combined metrics
                total_payment_all REAL,
                annual_payment_velocity REAL,
                monthly_payment_estimate REAL,
                
                -- Risk indicators
                is_high_cost_provider BOOLEAN,
                is_opioid_prescriber BOOLEAN,
                opioid_prescriber_rate REAL,
                partd_opioid_claims INTEGER,
                partd_opioid_cost REAL,
                
                -- Financial ratios
                payment_to_submitted_ratio REAL,
                services_per_beneficiary REAL,
                partd_bene_avg_risk_score REAL,
                
                --Metadata
data_source TEXT,
                profile_created_date TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Created provider_financial_profiles table")
        
        # 2. Payment Transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_transactions (
                transaction_id TEXT PRIMARY KEY,
                npi BIGINT NOT NULL,
                claim_id TEXT,
                payment_date DATE,
                
                -- Payment amounts
                total_services INTEGER,
                submitted_charge REAL,
                allowed_amount REAL,
                payment_amount REAL,
                drug_cost REAL,
                total_amount REAL,
                
                -- Status tracking
                payment_status TEXT,  -- PENDING, PROCESSED, HELD, STOPPED
                fraud_risk_score REAL,
                fraud_decision TEXT,  -- STOP, HOLD, REVIEW, RELEASE
                fraud_reasoning TEXT,
                
                -- Autonomous agent decision
                agent_decision TEXT,  -- APPROVED, REJECTED, ESCALATED
                agent_confidence REAL,
                agent_reasoning TEXT,
                
                -- Audit fields
                processor TEXT,  -- autonomous_agent, human_override
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (npi) REFERENCES provider_financial_profiles(npi)
            )
        ''')
        print("✓ Created payment_transactions table")
        
        # 3. Agent Decision Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_decision_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT,
                agent_name TEXT,
                decision TEXT,
                confidence REAL,
                reasoning TEXT,
                input_signals TEXT,  -- JSON
                execution_time_ms INTEGER,
                outcome TEXT,  -- SUCCESS, FAILED, ESCALATED
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (transaction_id) REFERENCES payment_transactions(transaction_id)
            )
        ''')
        print("✓ Created agent_decision_logs table")
        
        # 4. MCP Communication Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mcp_communication_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_system TEXT,
                target_system TEXT,
                tool_name TEXT,
                request_payload TEXT,  -- JSON
                response_payload TEXT,  -- JSON
                latency_ms INTEGER,
                status TEXT,  -- SUCCESS, FAILED, TIMEOUT
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Created mcp_communication_logs table")
        
        # 5. Payment History (for temporal analysis)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                npi BIGINT NOT NULL,
                year INTEGER,
                month INTEGER,
                total_payments REAL,
                total_transactions INTEGER,
                fraud_flags INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (npi) REFERENCES provider_financial_profiles(npi),
                UNIQUE(npi, year, month)
            )
        ''')
        print("✓ Created payment_history table")
        
        conn.commit()
        conn.close()
        print("✓ Schema creation complete")
        
    def create_indexes(self):
        """Create indexes for performance"""
        print("\n[2/5] Creating Indexes...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_transactions_npi ON payment_transactions(npi)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON payment_transactions(payment_date)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_status ON payment_transactions(payment_status)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_fraud_score ON payment_transactions(fraud_risk_score)",
            "CREATE INDEX IF NOT EXISTS idx_profiles_high_cost ON provider_financial_profiles(is_high_cost_provider)",
            "CREATE INDEX IF NOT EXISTS idx_profiles_opioid ON provider_financial_profiles(is_opioid_prescriber)",
            "CREATE INDEX IF NOT EXISTS idx_profiles_state ON provider_financial_profiles(provider_state)",
            "CREATE INDEX IF NOT EXISTS idx_decision_logs_transaction ON agent_decision_logs(transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_decision_logs_agent ON agent_decision_logs(agent_name)",
            "CREATE INDEX IF NOT EXISTS idx_mcp_logs_tool ON mcp_communication_logs(tool_name)",
            "CREATE INDEX IF NOT EXISTS idx_payment_history_npi ON payment_history(npi)",
        ]
        
        for idx in indexes:
            cursor.execute(idx)
        
        conn.commit()
        conn.close()
        print(f"✓ Created {len(indexes)} indexes")
        
    def load_provider_profiles(self, csv_path='../../data/provider_financial_profiles.csv'):
        """Load provider financial profiles from CSV"""
        print(f"\n[3/5] Loading Provider Profiles from {Path(csv_path).name}...")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"  Loaded {len(df):,} provider profiles")
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        
        # Insert into database
        df.to_sql('provider_financial_profiles', conn, if_exists='replace', index=False)
        
        conn.close()
        print(f"✓ Inserted {len(df):,} provider profiles into database")
        
        return len(df)
    
    def generate_sample_transactions(self, num_transactions=10000):
        """Generate sample payment transactions for testing"""
        print(f"\n[4/5] Generating {num_transactions:,} Sample Transactions...")
        
        import numpy as np
        from datetime import timedelta
        
        conn = sqlite3.connect(self.db_path)
        
        # Get sample NPIs from profiles
        npis = pd.read_sql_query("SELECT npi, total_payment_all FROM provider_financial_profiles LIMIT 5000", conn)
        
        transactions = []
        base_date = datetime(2023, 1, 1)
        
        for i in range(num_transactions):
            # Random provider
            provider = npis.sample(1).iloc[0]
            npi = provider['npi']
            
            # Generate transaction
            payment_amount = np.random.gamma(2, provider['total_payment_all'] / 12 / 10)  # Monthly estimate
            payment_date = base_date + timedelta(days=np.random.randint(0, 365))
            
            # Fraud risk (most are low)
            fraud_risk = np.random.beta(2, 5)
            
            # Determine status based on risk
            if fraud_risk > 0.8:
                payment_status = 'HELD'
                fraud_decision = 'HOLD'
            elif fraud_risk > 0.6:
                payment_status = 'PENDING'
                fraud_decision = 'REVIEW'
            else:
                payment_status = 'PROCESSED'
                fraud_decision = 'RELEASE'
            
            transaction = {
                'transaction_id': f'TXN_{npi}_{i}',
                'npi': int(npi),
                'claim_id': f'CLM_{npi}_{i}',
                'payment_date': payment_date.strftime('%Y-%m-%d'),
                'payment_amount': float(payment_amount),
                'total_amount': float(payment_amount),
                'payment_status': payment_status,
                'fraud_risk_score': float(fraud_risk),
                'fraud_decision': fraud_decision,
                'processor': 'autonomous_agent',
                'created_at': datetime.now().isoformat()
            }
            
            transactions.append(transaction)
        
        # Insert transactions
        tx_df = pd.DataFrame(transactions)
        tx_df.to_sql('payment_transactions', conn, if_exists='append', index=False)
        
        conn.close()
        print(f"✓ Generated and inserted {len(transactions):,} sample transactions")
        
        return len(transactions)
    
    def verify_data(self):
        """Verify database integrity"""
        print("\n[5/5] Verifying Database Integrity...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Count records
        tables = ['provider_financial_profiles', 'payment_transactions', 
                  'agent_decision_logs', 'mcp_communication_logs', 'payment_history']
        
        print("\nTable Statistics:")
        print("-" * 60)
        for table in tables:
            count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
            print(f"  {table:.<40} {count:>10,} records")
        
        # Check data quality
        print("\nData Quality Checks:")
        print("-" * 60)
        
        # Check for NULL NPIs
        null_npis = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM provider_financial_profiles WHERE npi IS NULL", 
            conn
        ).iloc[0]['count']
        print(f"  NULL NPIs: {null_npis} (should be 0)")
        
        # Check payment amount validity
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) 
            FROM payment_transactions 
            WHERE payment_amount < 0 OR payment_amount IS NULL
        ''')
        invalid_payments = cursor.fetchone()[0]
        print(f"  Invalid payment amounts: {invalid_payments} (should be 0)")
        
        # Check foreign key integrity
        cursor.execute('''
            SELECT COUNT(*) 
            FROM payment_transactions t
            LEFT JOIN provider_financial_profiles p ON t.npi = p.npi
            WHERE p.npi IS NULL
        ''')
        orphan_transactions = cursor.fetchone()[0]
        print(f"  Orphaned transactions: {orphan_transactions} (should be 0)")
        
        conn.close()
        
        print("\n✓ Database verification complete")
        
    def get_summary_stats(self):
        """Get summary statistics from database"""
        conn = sqlite3.connect(self.db_path)
        
        stats = {}
        
        # Provider statistics
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM provider_financial_profiles")
        stats['total_providers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_payment_all) FROM provider_financial_profiles")
        stats['total_payments'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM provider_financial_profiles WHERE is_high_cost_provider = 1")
        stats['high_cost_providers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM provider_financial_profiles WHERE is_opioid_prescriber = 1")
        stats['opioid_prescribers'] = cursor.fetchone()[0]
        
        # Transaction statistics
        cursor.execute("SELECT COUNT(*) FROM payment_transactions")
        stats['total_transactions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payment_transactions WHERE payment_status = 'HELD'")
        stats['held_transactions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payment_transactions WHERE payment_status = 'PROCESSED'")
        stats['processed_transactions'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats
    
    def export_summary(self, output_path='../../data/database_summary.json'):
        """Export database summary to JSON"""
        stats = self.get_summary_stats()
        
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n✓ Exported database summary to: {output_path}")
        return stats
        
    def setup_complete_database(self):
        """Run complete database setup"""
        print("\nRunning complete database setup...\n")
        
        # Create schema
        self.create_schema()
        
        # Create indexes
        self.create_indexes()
        
        # Load provider profiles
        self.load_provider_profiles()
        
        # Generate sample transactions
        self.generate_sample_transactions(num_transactions=10000)
        
        # Verify data
        self.verify_data()
        
        # Export summary
        stats = self.export_summary()
        
        print("\n" + "=" * 80)
        print("DATABASE SETUP COMPLETE")
        print("=" * 80)
        print(f"\nDatabase Summary:")
        print(f"  Total Providers: {stats['total_providers']:,}")
        print(f"  Total Payments: ${stats['total_payments']:,.2f}")
        print(f"  High-Cost Providers: {stats['high_cost_providers']:,}")
        print(f"  Opioid Prescribers: {stats['opioid_prescribers']:,}")
        print(f"  Total Transactions: {stats['total_transactions']:,}")
        print(f"  Processed Transactions: {stats['processed_transactions']:,}")
        print(f"  Held Transactions: {stats['held_transactions']:,}")
        print(f"\n✅ Finance database ready at: {self.db_path}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Finance application database')
    parser.add_argument('--db-path', default='../../data/finance.db', help='Database path')
    parser.add_argument('--profiles-csv', default='../../data/provider_financial_profiles.csv', help='Provider profiles CSV')
    parser.add_argument('--num-transactions', type=int, default=10000, help='Number of sample transactions')
    
    args = parser.parse_args()
    
    # Create database
    db = FinanceDatabase(db_path=args.db_path)
    db.setup_complete_database()


if __name__ == '__main__':
    main()
