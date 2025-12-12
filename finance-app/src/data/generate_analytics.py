"""
Finance Application - Analytics Generator

Generates comprehensive analytics and insights from payment data.

Author: Healthcare Fraud Detection Team
Date: 2024-11-30
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime


class FinanceAnalytics:
    """Generate analytics from Finance database"""
    
    def __init__(self, db_path='../../data/finance.db', output_dir='../../data/analytics'):
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_all_analytics(self):
        """Generate all analytics reports"""
        print("="*80)
        print("Finance Application - Analytics Generation")
        print("="*80)
        
        conn = sqlite3.connect(self.db_path)
        
        # 1. Overall Payment Statistics
        payment_stats = self.get_payment_statistics(conn)
        self.export_json(payment_stats, 'payment_statistics.json')
        
        # 2. Fraud-Payment Correlation
        fraud_correlation = self.analyze_fraud_correlation(conn)
        self.export_json(fraud_correlation, 'fraud_correlation.json')
        
        # 3. High-Risk Provider Analysis
        high_risk = self.analyze_high_risk_providers(conn)
        self.export_csv(high_risk, 'high_risk_providers.csv')
        
        # 4. Agent Performance Metrics
        agent_metrics = self.get_agent_performance(conn)
        self.export_json(agent_metrics, 'agent_performance.json')
        
        conn.close()
        
        print("\n✅ Analytics generation complete!")
        print(f"Output directory: {self.output_dir}")
        
    def get_payment_statistics(self, conn):
        """Calculate overall payment statistics"""
        stats = {}
        
        # Total payments
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(total_payment_all) FROM provider_financial_profiles")
        stats['total_payments_all_time'] = float(cursor.fetchone()[0])
        
        cursor.execute("SELECT COUNT(*) FROM provider_financial_profiles")
        stats['total_providers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(total_payment_all) FROM provider_financial_profiles")
        stats['average_payment_per_provider'] = float(cursor.fetchone()[0])
        
        # By risk category
        cursor.execute("SELECT COUNT(*), SUM(total_payment_all) FROM provider_financial_profiles WHERE is_high_cost_provider = 1")
        row = cursor.fetchone()
        stats['high_cost_providers'] = {'count': row[0], 'total_payments': float(row[1])}
        
        cursor.execute("SELECT COUNT(*), SUM(total_payment_all) FROM provider_financial_profiles WHERE is_opioid_prescriber = 1")
        row = cursor.fetchone()
        stats['opioid_prescribers'] = {'count': row[0], 'total_payments': float(row[1]) if row[1] else 0.0}
        
        print("\n✓ Payment statistics calculated")
        return stats
    
    def analyze_fraud_correlation(self, conn):
        """Analyze correlation between fraud scores and payment amounts"""
        df = pd.read_sql_query('''
            SELECT npi, total_payment_all, is_high_cost_provider, is_opioid_prescriber,
                   partd_opioid_cost
            FROM provider_financial_profiles
        ''', conn)
        
        correlation = {
            'high_cost_payment_correlation': float(df[df['is_high_cost_provider'] == 1]['total_payment_all'].mean() / df['total_payment_all'].mean()),
            'opioid_payment_correlation': float(df[df['is_opioid_prescriber'] == 1]['total_payment_all'].mean() / df['total_payment_all'].mean()) if df[df['is_opioid_prescriber'] == 1]['total_payment_all'].mean() > 0 else 0.0,
            'total_high_risk_payments': float(df[(df['is_high_cost_provider'] == 1) | (df['is_opioid_prescriber'] == 1)]['total_payment_all'].sum())
        }
        
        print("✓ Fraud correlation analysis complete")
        return correlation
    
    def analyze_high_risk_providers(self, conn):
        """Identify and analyze high-risk providers"""
        df = pd.read_sql_query('''
            SELECT npi, provider_name, provider_state, total_payment_all,
                   is_high_cost_provider, is_opioid_prescriber,
                   opioid_prescriber_rate, partd_opioid_cost
            FROM provider_financial_profiles
            WHERE is_high_cost_provider = 1 OR is_opioid_prescriber = 1
            ORDER BY total_payment_all DESC
            LIMIT 100
        ''', conn)
        
        print(f"✓ Identified {len(df)} high-risk providers")
        return df
    
    def get_agent_performance(self, conn):
        """Calculate agent decision performance metrics"""
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM agent_decision_logs WHERE agent_name = 'PaymentAgent'")
        total_decisions = cursor.fetchone()[0]
        
        cursor.execute("SELECT decision, COUNT(*) FROM agent_decision_logs WHERE agent_name = 'PaymentAgent' GROUP BY decision")
        decisions = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT AVG(confidence) FROM agent_decision_logs WHERE agent_name = 'PaymentAgent'")
        avg_confidence = cursor.fetchone()[0]
        
        metrics = {
            'total_decisions': total_decisions,
            'decisions_by_type': decisions,
            'average_confidence': float(avg_confidence) if avg_confidence else 0.0
        }
        
        print("✓ Agent performance metrics calculated")
        return metrics
    
    def export_json(self, data, filename):
        """Export data to JSON"""
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Exported: {filename}")
    
    def export_csv(self, df, filename):
        """Export DataFrame to CSV"""
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        print(f"  Exported: {filename}")


if __name__ == '__main__':
    analytics = FinanceAnalytics()
    analytics.generate_all_analytics()
