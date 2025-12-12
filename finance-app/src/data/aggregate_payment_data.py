"""
Finance Application - Payment Data Aggregation Script

This script aggregates payment data from Part B and Part D Medicare files,
merges with NPPES provider registry, and generates provider financial profiles
for the autonomous Finance application.

Author: Healthcare Fraud Detection Team
Date: 2024-11-30
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

class PaymentDataAggregator:
    """Aggregates payment data from Medicare datasets for Finance application"""
    
    def __init__(self, data_dir='../../../data/raw_data', output_dir='../../data'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.part_b_file = self.data_dir / 'MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv'
        self.part_d_provider_file = self.data_dir / 'MUP_DPR_RY25_P04_V10_DY23_NPI.csv'
        self.part_d_drug_file = self.data_dir / 'MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv'
        self.nppes_file = self.data_dir / 'npidata_pfile_20050523-20251109.csv'
        
        print("=" * 80)
        print("Finance Application - Payment Data Aggregation")
        print("=" * 80)
        
    def load_part_b_data(self, sample_size=None):
        """
        Load Part B payment data
        
        Key columns:
        - Rndrng_NPI: Provider NPI
        - Tot_Srvcs: Total services
        - Avg_Mdcr_Pymt_Amt: Average Medicare payment amount
        """
        print("\n[1/6] Loading Part B Payment Data...")
        print(f"File: {self.part_b_file.name}")
        
        # Define columns to load for efficiency
        cols_to_load = [
            'Rndrng_NPI',
            'Rndrng_Prvdr_Last_Org_Name',
            'Rndrng_Prvdr_First_Name',
            'Rndrng_Prvdr_City',
            'Rndrng_Prvdr_State_Abrvtn',
            'Rndrng_Prvdr_Type',
            'HCPCS_Cd',
            'Place_Of_Srvc',
            'Tot_Benes',
            'Tot_Srvcs',
            'Tot_Bene_Day_Srvcs',
            'Avg_Sbmtd_Chrg',
            'Avg_Mdcr_Alowd_Amt',
            'Avg_Mdcr_Pymt_Amt',
            'Avg_Mdcr_Stdzd_Amt'
        ]
        
        # Load data (optionally sample for testing)
        if sample_size:
            df = pd.read_csv(self.part_b_file, usecols=cols_to_load, nrows=sample_size)
            print(f"✓ Loaded {len(df):,} records (SAMPLE)")
        else:
            df = pd.read_csv(self.part_b_file, usecols=cols_to_load, low_memory=False)
            print(f"✓ Loaded {len(df):,} records")
        
        print(f"  Unique Providers: {df['Rndrng_NPI'].nunique():,}")
        
        return df
    
    def aggregate_part_b_by_provider(self, part_b_df):
        """Aggregate Part B data by provider NPI"""
        print("\n[2/6] Aggregating Part B Data by Provider...")
        
        # Calculate total payments per provider
        part_b_df['total_payment'] = part_b_df['Avg_Mdcr_Pymt_Amt'] * part_b_df['Tot_Srvcs']
        part_b_df['total_submitted_charge'] = part_b_df['Avg_Sbmtd_Chrg'] * part_b_df['Tot_Srvcs']
        part_b_df['total_allowed_amount'] = part_b_df['Avg_Mdcr_Alowd_Amt'] * part_b_df['Tot_Srvcs']
        
        # Group by provider
        agg_dict = {
            'Rndrng_Prvdr_Last_Org_Name': 'first',
            'Rndrng_Prvdr_First_Name': 'first',
            'Rndrng_Prvdr_City': 'first',
            'Rndrng_Prvdr_State_Abrvtn': 'first',
            'Rndrng_Prvdr_Type': 'first',
            'Tot_Benes': 'sum',
            'Tot_Srvcs': 'sum',
            'Tot_Bene_Day_Srvcs': 'sum',
            'total_payment': 'sum',
            'total_submitted_charge': 'sum',
            'total_allowed_amount': 'sum',
            'HCPCS_Cd': 'count'  # Count of procedure codes
        }
        
        aggregated = part_b_df.groupby('Rndrng_NPI').agg(agg_dict).reset_index()
        
        # Rename for clarity
        aggregated.rename(columns={
            'Rndrng_NPI': 'npi',
            'Rndrng_Prvdr_Last_Org_Name': 'provider_last_name',
            'Rndrng_Prvdr_First_Name': 'provider_first_name',
            'Rndrng_Prvdr_City': 'provider_city',
            'Rndrng_Prvdr_State_Abrvtn': 'provider_state',
            'Rndrng_Prvdr_Type': 'provider_type',
            'Tot_Benes': 'partb_total_beneficiaries',
            'Tot_Srvcs': 'partb_total_services',
            'Tot_Bene_Day_Srvcs': 'partb_total_bene_day_services',
            'total_payment': 'partb_total_payment',
            'total_submitted_charge': 'partb_total_submitted_charge',
            'total_allowed_amount': 'partb_total_allowed_amount',
            'HCPCS_Cd': 'partb_procedure_count'
        }, inplace=True)
        
        print(f"✓ Aggregated to {len(aggregated):,} unique providers")
        print(f"  Total Part B Payments: ${aggregated['partb_total_payment'].sum():,.2f}")
        
        return aggregated
    
    def load_part_d_data(self, sample_size=None):
        """Load Part D drug cost data"""
        print("\n[3/6] Loading Part D Payment Data...")
        print(f"File: {self.part_d_provider_file.name}")
        
        cols_to_load = [
            'PRSCRBR_NPI',
            'Prscrbr_Last_Org_Name',
            'Prscrbr_First_Name',
            'Prscrbr_Type',
            'Tot_Clms',
            'Tot_30day_Fills',
            'Tot_Drug_Cst',
            'Tot_Day_Suply',
            'Tot_Benes',
            'Opioid_Tot_Clms',
            'Opioid_Tot_Drug_Cst',
            'Opioid_Tot_Benes',
            'Antbtc_Tot_Clms',
            'Antbtc_Tot_Drug_Cst',
            'Bene_Avg_Risk_Scre'
        ]
        
        if sample_size:
            df = pd.read_csv(self.part_d_provider_file, usecols=cols_to_load, nrows=sample_size)
            print(f"✓ Loaded {len(df):,} records (SAMPLE)")
        else:
            df = pd.read_csv(self.part_d_provider_file, usecols=cols_to_load, low_memory=False)
            print(f"✓ Loaded {len(df):,} records")
        
        print(f"  Unique Prescribers: {df['PRSCRBR_NPI'].nunique():,}")
        
        # Rename for consistency
        df.rename(columns={'PRSCRBR_NPI': 'npi'}, inplace=True)
        
        # Rename Part D columns
        df.rename(columns={
            'Prscrbr_Last_Org_Name': 'partd_provider_last_name',
            'Prscrbr_First_Name': 'partd_provider_first_name',
            'Prscrbr_Type': 'partd_provider_type',
            'Tot_Clms': 'partd_total_claims',
            'Tot_30day_Fills': 'partd_total_fills',
            'Tot_Drug_Cst': 'partd_total_drug_cost',
            'Tot_Day_Suply': 'partd_total_day_supply',
            'Tot_Benes': 'partd_total_beneficiaries',
            'Opioid_Tot_Clms': 'partd_opioid_claims',
            'Opioid_Tot_Drug_Cst': 'partd_opioid_cost',
            'Opioid_Tot_Benes': 'partd_opioid_beneficiaries',
            'Antbtc_Tot_Clms': 'partd_antibiotic_claims',
            'Antbtc_Tot_Drug_Cst': 'partd_antibiotic_cost',
            'Bene_Avg_Risk_Scre': 'partd_bene_avg_risk_score'
        }, inplace=True)
        
        print(f"  Total Part D Drug Costs: ${df['partd_total_drug_cost'].sum():,.2f}")
        
        return df
    
    def merge_payment_data(self, part_b_agg, part_d_df):
        """Merge Part B and Part D data by NPI"""
        print("\n[4/6] Merging Part B and Part D Data...")
        
        # Outer join to include all providers
        merged = pd.merge(
            part_b_agg,
            part_d_df,
            on='npi',
            how='outer',
            suffixes=('_b', '_d')
        )
        
        # Coalesce provider names (prefer Part B, fallback to Part D)
        merged['provider_name'] = merged['provider_last_name'].fillna(
            merged['partd_provider_last_name']
        ) + ', ' + merged['provider_first_name'].fillna(
            merged['partd_provider_first_name']
        ).fillna('')
        
        print(f"✓ Merged to {len(merged):,} unique providers")
        print(f"  Providers with Part B data: {merged['partb_total_payment'].notna().sum():,}")
        print(f"  Providers with Part D data: {merged['partd_total_drug_cost'].notna().sum():,}")
        print(f"  Providers with both: {(merged['partb_total_payment'].notna() & merged['partd_total_drug_cost'].notna()).sum():,}")
        
        return merged
    
    def calculate_financial_metrics(self, merged_df):
        """Calculate additional financial metrics and risk indicators"""
        print("\n[5/6] Calculating Financial Metrics...")
        
        # Fill NaN values with 0 for calculations
        merged_df['partb_total_payment'] = merged_df['partb_total_payment'].fillna(0)
        merged_df['partd_total_drug_cost'] = merged_df['partd_total_drug_cost'].fillna(0)
        
        # Total combined payment
        merged_df['total_payment_all'] = (
            merged_df['partb_total_payment'] + 
            merged_df['partd_total_drug_cost']
        )
        
        # Payment velocity (annual)
        merged_df['annual_payment_velocity'] = merged_df['total_payment_all']
        merged_df['monthly_payment_estimate'] = merged_df['annual_payment_velocity'] / 12
        
        # Risk indicators
        merged_df['is_high_cost_provider'] = merged_df['total_payment_all'] > merged_df['total_payment_all'].quantile(0.95)
        merged_df['is_opioid_prescriber'] = merged_df['partd_opioid_claims'].fillna(0) > 0
        merged_df['opioid_prescriber_rate'] = (
            merged_df['partd_opioid_claims'].fillna(0) / 
            merged_df['partd_total_claims'].fillna(1).replace(0, 1)
        )
        
        # Payment ratios (for fraud detection)
        merged_df['payment_to_submitted_ratio'] = (
            merged_df['partb_total_payment'] / 
            merged_df['partb_total_submitted_charge'].replace(0, np.nan)
        )
        merged_df['allowed_to_submitted_ratio'] = (
            merged_df['partb_total_allowed_amount'] / 
            merged_df['partb_total_submitted_charge'].replace(0, np.nan)
        )
        
        # Service intensity
        merged_df['services_per_beneficiary'] = (
            merged_df['partb_total_services'].fillna(0) / 
            merged_df['partb_total_beneficiaries'].fillna(1).replace(0, 1)
        )
        
        print(f"✓ Calculated financial metrics")
        print(f"  High-cost providers (top 5%): {merged_df['is_high_cost_provider'].sum():,}")
        print(f"  Opioid prescribers: {merged_df['is_opioid_prescriber'].sum():,}")
        print(f"  Average payment per provider: ${merged_df['total_payment_all'].mean():,.2f}")
        print(f"  Median payment per provider: ${merged_df['total_payment_all'].median():,.2f}")
        
        return merged_df
    
    def load_nppes_sample(self, npis_to_match):
        """Load NPPES data for providers in our dataset (memory-efficient)"""
        print("\n[6/6] Loading NPPES Provider Registry (sample matching)...")
        
        # NPPES file is very large (10GB+), so we'll load only NPIs we need
        print(f"  Matching against {len(npis_to_match):,} NPIs...")
        
        # Load in chunks and filter
        nppes_cols = [
            'NPI',
            'Provider Organization Name (Legal Business Name)',
            'Provider Business Mailing Address Line One',
            'Provider Business Mailing Address City Name',
            'Provider Business Mailing Address State Name',
            'Provider Business Mailing Address Postal Code',
            'Healthcare Provider Taxonomy Code_1',
            'Provider Enumeration Date'
        ]
        
        matched_providers = []
        chunk_size = 100000
        chunks_processed = 0
        
        try:
            for chunk in pd.read_csv(self.nppes_file, usecols=nppes_cols, chunksize=chunk_size, low_memory=False):
                chunks_processed += 1
                # Filter to only NPIs in our dataset
                matched = chunk[chunk['NPI'].isin(npis_to_match)]
                if len(matched) > 0:
                    matched_providers.append(matched)
                
                if chunks_processed % 10 == 0:
                    print(f"  Processed {chunks_processed * chunk_size:,} NPPES records...")
                
                # Stop if we've matched all NPIs
                if len(matched_providers) > 0:
                    matched_so_far = pd.concat(matched_providers, ignore_index=True)
                    if len(matched_so_far) >= len(npis_to_match) * 0.95:  # 95% match rate
                        print(f"  Reached 95% match rate, stopping early")
                        break
        
        except Exception as e:
            print(f"  Warning: Error reading NPPES file: {e}")
            print(f"  Continuing without NPPES data...")
            return pd.DataFrame()
        
        if len(matched_providers) > 0:
            nppes_df = pd.concat(matched_providers, ignore_index=True)
            
            # Rename for clarity
            nppes_df.rename(columns={
                'NPI': 'npi',
                'Provider Organization Name (Legal Business Name)': 'nppes_org_name',
                'Provider Business Mailing Address Line One': 'nppes_address',
                'Provider Business Mailing Address City Name': 'nppes_city',
                'Provider Business Mailing Address State Name': 'nppes_state',
                'Provider Business Mailing Address Postal Code': 'nppes_zip',
                'Healthcare Provider Taxonomy Code_1': 'nppes_taxonomy',
                'Provider Enumeration Date': 'nppes_enumeration_date'
            }, inplace=True)
            
            print(f"✓ Matched {len(nppes_df):,} providers from NPPES registry")
            return nppes_df
        else:
            print("  No NPPES matches found")
            return pd.DataFrame()
    
    def integrate_nppes_data(self, payment_df, nppes_df):
        """Integrate NPPES data with payment data"""
        if len(nppes_df) == 0:
            print("  Skipping NPPES integration (no data)")
            return payment_df
        
        print("  Merging NPPES data...")
        integrated = pd.merge(
            payment_df,
            nppes_df,
            on='npi',
            how='left'
        )
        
        print(f"✓ Integrated NPPES data for {integrated['nppes_org_name'].notna().sum():,} providers")
        return integrated
    
    def generate_provider_financial_profiles(self, integrated_df):
        """Generate final provider financial profiles"""
        print("\n" + "=" * 80)
        print("Generating Provider Financial Profiles")
        print("=" * 80)
        
        # Select final columns
        profile_columns = [
            'npi',
            'provider_name',
            'provider_city',
            'provider_state',
            'provider_type',
            'nppes_org_name',
            'nppes_address',
            'nppes_city',
            'nppes_state',
            'nppes_zip',
            'nppes_taxonomy',
            'partb_total_payment',
            'partb_total_services',
            'partb_total_beneficiaries',
            'partb_procedure_count',
            'partd_total_drug_cost',
            'partd_total_claims',
            'partd_total_beneficiaries',
            'total_payment_all',
            'annual_payment_velocity',
            'monthly_payment_estimate',
            'is_high_cost_provider',
            'is_opioid_prescriber',
            'opioid_prescriber_rate',
            'partd_opioid_claims',
            'partd_opioid_cost',
            'payment_to_submitted_ratio',
            'services_per_beneficiary',
            'partd_bene_avg_risk_score'
        ]
        
        # Filter to columns that exist
        existing_cols = [col for col in profile_columns if col in integrated_df.columns]
        profiles = integrated_df[existing_cols].copy()
        
        # Add metadata
        profiles['data_source'] = 'CMS Medicare 2023'
        profiles['profile_created_date'] = datetime.now().strftime('%Y-%m-%d')
        
        return profiles
    
    def export_data(self, profiles_df):
        """Export aggregated data to CSV files"""
        print("\n" + "=" * 80)
        print("Exporting Data")
        print("=" * 80)
        
        # Export provider financial profiles
        output_file = self.output_dir / 'provider_financial_profiles.csv'
        profiles_df.to_csv(output_file, index=False)
        print(f"✓ Exported provider financial profiles to: {output_file}")
        print(f"  Records: {len(profiles_df):,}")
        print(f"  File size: {output_file.stat().st_size / (1024*1024):.2f} MB")
        
        # Export summary statistics
        summary = {
            'total_providers': int(len(profiles_df)),
            'providers_with_partb': int(profiles_df['partb_total_payment'].notna().sum()),
            'providers_with_partd': int(profiles_df['partd_total_drug_cost'].notna().sum()),
            'total_partb_payments': float(profiles_df['partb_total_payment'].sum()),
            'total_partd_costs': float(profiles_df['partd_total_drug_cost'].sum()),
            'total_combined_payments': float(profiles_df['total_payment_all'].sum()),
            'high_cost_providers': int(profiles_df['is_high_cost_provider'].sum()),
            'opioid_prescribers': int(profiles_df['is_opioid_prescriber'].sum()),
            'avg_payment_per_provider': float(profiles_df['total_payment_all'].mean()),
            'median_payment_per_provider': float(profiles_df['total_payment_all'].median()),
            'generated_date': datetime.now().isoformat()
        }
        
        summary_file = self.output_dir / 'payment_data_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✓ Exported summary statistics to: {summary_file}")
        
        print("\n" + "=" * 80)
        print("AGGREGATION COMPLETE")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  Total Providers: {summary['total_providers']:,}")
        print(f"  Total Part B Payments: ${summary['total_partb_payments']:,.2f}")
        print(f"  Total Part D Costs: ${summary['total_partd_costs']:,.2f}")
        print(f"  Combined Total: ${summary['total_combined_payments']:,.2f}")
        print(f"  High-Cost Providers: {summary['high_cost_providers']:,}")
        print(f"  Opioid Prescribers: {summary['opioid_prescribers']:,}")
        
        return output_file
    
    def run(self, sample_size=None):
        """Run complete aggregation pipeline"""
        print(f"\nStarting aggregation pipeline...")
        if sample_size:
            print(f"NOTE: Running in SAMPLE mode ({sample_size:,} records per file)")
        
        # Step 1: Load Part B
        part_b_df = self.load_part_b_data(sample_size)
        
        # Step 2: Aggregate Part B by provider
        part_b_agg = self.aggregate_part_b_by_provider(part_b_df)
        
        # Step 3: Load Part D
        part_d_df = self.load_part_d_data(sample_size)
        
        # Step 4: Merge Part B and Part D
        merged_df = self.merge_payment_data(part_b_agg, part_d_df)
        
        # Step 5: Calculate financial metrics
        enriched_df = self.calculate_financial_metrics(merged_df)
        
        # Step 6: Load and integrate NPPES (optional, memory-intensive)
        npis_to_match = enriched_df['npi'].unique()
        nppes_df = self.load_nppes_sample(npis_to_match)
        integrated_df = self.integrate_nppes_data(enriched_df, nppes_df)
        
        # Step 7: Generate final profiles
        profiles_df = self.generate_provider_financial_profiles(integrated_df)
        
        # Step 8: Export
        output_file = self.export_data(profiles_df)
        
        return profiles_df, output_file


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Aggregate payment data for Finance application')
    parser.add_argument('--sample', type=int, help='Sample size for testing (e.g., 10000)')
    parser.add_argument('--data-dir', default='../../../data/raw_data', help='Input data directory')
    parser.add_argument('--output-dir', default='../../data', help='Output directory')
    
    args = parser.parse_args()
    
    # Create aggregator
    aggregator = PaymentDataAggregator(
        data_dir=args.data_dir,
        output_dir=args.output_dir
    )
    
    # Run aggregation
    profiles_df, output_file = aggregator.run(sample_size=args.sample)
    
    print(f"\n✅ Success! Data ready for Finance application")
    print(f"📁 Output: {output_file}")


if __name__ == '__main__':
    main()
