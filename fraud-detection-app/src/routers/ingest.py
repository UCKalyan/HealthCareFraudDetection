import logging
import pandas as pd
import numpy as np
import io
import requests
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from src.dependencies import get_ml_assets
from src.database import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter()

FINANCE_API_URL = "http://localhost:8001/api/process_payment_hold"

def process_ingestion(df: pd.DataFrame, ml_assets: dict):
    """
    Background task to process the ingested dataframe:
    1. Update DB
    2. Calculate Risk
    3. Auto-Hold High Risk
    """
    try:
        logger.info(f"Processing ingestion for {len(df)} providers...")
        
        # 1. Prepare Features
        feature_columns = ml_assets['final_feature_columns']
        model = ml_assets['fraud_model']
        scaler = ml_assets['scaler']
        
        # Ensure all required columns exist
        # 0. Column Mapping (CMS -> Internal)
        # Handled in ingest_csv endpoint before background task
        # column_map = { ... }
        # df.rename(columns=column_map, inplace=True)
        
        # 1. Feature Engineering
        # Calculate Ratios
        # Note: CMS data usually has Avg_Sbmtd_Chrg, so total_service_cost = Avg * Tot_Srvcs
        if 'total_service_cost' not in df.columns:
            if 'avg_submitted_charge' in df.columns and 'total_services' in df.columns:
                df['total_service_cost'] = df['avg_submitted_charge'] * df['total_services']
            else:
                df['total_service_cost'] = 0.0

        df['cost_per_service'] = df.apply(lambda row: row['total_service_cost'] / row['total_services'] if row.get('total_services', 0) > 0 else 0, axis=1)
        df['services_per_bene'] = df.apply(lambda row: row['total_services'] / row['total_benes_phys'] if row.get('total_benes_phys', 0) > 0 else 0, axis=1)

        
        # Calculate SPB Z-Score (using global stats from ml_assets)
        spb_stats = ml_assets.get('spb_stats')
        if spb_stats is not None:
            # We need to map specialty to mean/std. 
            # For efficiency, we can do this via map if spb_stats is a DF indexed by specialty
            # But spb_stats might be a simple DF. Let's check structure in dependencies.py or assume it's usable.
            # In dependencies.py: ml_assets['spb_stats'] = pd.DataFrame(stats['spb_stats'])
            # It likely has 'specialty', 'mean', 'std' columns.
            
            # Create a lookup dictionary for faster mapping
            spb_mean_map = spb_stats.set_index('specialty')['mean'].to_dict()
            spb_std_map = spb_stats.set_index('specialty')['std'].to_dict()
            
            global_mean = spb_stats['mean'].mean()
            global_std = spb_stats['std'].mean()
            
            def get_z_score(row):
                spec = row.get('specialty', 'Unknown')
                mean = spb_mean_map.get(spec, global_mean)
                std = spb_std_map.get(spec, global_std)
                if std == 0 or pd.isna(std): return 0
                return (row['services_per_bene'] - mean) / std

            df['spb_z'] = df.apply(get_z_score, axis=1)
            df['spb_z_tanh'] = np.tanh(0.5 * df['spb_z'])
        else:
            df['spb_z_tanh'] = 0.0
            
        # Default/Placeholder Features
        df['has_part_b'] = 1 # Assume yes for now
        df['has_part_d'] = 1 # Assume yes for now
        df['pagerank_centrality'] = ml_assets.get('median_pagerank', 1e-6)
        
        for i in range(5):
             df[f'provider_archetype_{i}'] = 0.0
             
        # Ensure all required columns exist (safety check)
        feature_columns = ml_assets['final_feature_columns']
        for col in feature_columns:
            if col not in df.columns:
                df[col] = 0.0
                
        # 2. Calculate Risk Scores
        X = df[feature_columns]
        X_scaled = scaler.transform(X)
        risk_scores = model.predict(X_scaled, verbose=0).flatten()
        df['risk_score'] = risk_scores
        
        logger.info("Risk scores calculated.")

        # 2.1 Update In-Memory Feature Store (for Real-Time Risk Checks)
        # We need to add the new rows to the feature_store dataframe in ml_assets
        if 'feature_store' in ml_assets:
            # Create a dataframe with the features and set index to provider_id
            new_features_df = df.set_index('provider_id')[feature_columns]
            
            # Update existing or append new
            # Combine_first or update is tricky with index, let's just use concat and drop duplicates
            # keeping the new one (last)
            current_store = ml_assets['feature_store']
            updated_store = pd.concat([current_store, new_features_df])
            # Remove duplicates, keeping the last (newest) one
            updated_store = updated_store[~updated_store.index.duplicated(keep='last')]
            
            ml_assets['feature_store'] = updated_store
            logger.info(f"In-memory feature store updated. Total size: {len(updated_store)}")
        
        # 3. Update Database (Upsert)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # We need to handle potential new columns in the CSV that match DB schema
            # For now, we focus on updating risk_score and inserting new providers
            # A full UPSERT in SQLite is INSERT OR REPLACE or INSERT ... ON CONFLICT
            
            # Let's use pandas to_sql with if_exists='append' but that fails on duplicates
            # So we'll iterate and UPSERT. This is slower but safer for this MVP.
            
            # First, ensure we have provider_id
            if 'provider_id' not in df.columns:
                logger.error("CSV missing provider_id column")
                return

            for index, row in df.iterrows():
                npi = row['provider_id']
                score = float(row['risk_score'])
                
                # Update Risk Score in DB
                # We assume the provider exists or we insert them. 
                # For simplicity in this MVP, we'll try to update, if 0 rows, we insert.
                # Actually, let's just update the risk_score for existing and insert new ones.
                # But inserting requires matching all DB columns.
                
                # Strategy: Check if exists
                cursor.execute("SELECT 1 FROM providers WHERE provider_id = ?", (npi,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute("UPDATE providers SET risk_score = ? WHERE provider_id = ?", (score, npi))
                else:
                    # Insert new provider with available data
                    # We need to construct an INSERT statement dynamically based on available columns
                    # that match the DB table.
                    # For now, let's just insert the minimal required + risk_score
                    # Or better: use pandas to_sql to a temp table and then merge?
                    # Let's stick to updating risk score for now as "Ingest" often implies "Update Analysis"
                    # If the user wants to ADD new providers, they need to provide all columns.
                    
                    # Let's try to insert what we have.
                    cols = [c for c in df.columns if c in ['provider_id', 'risk_score', 'Prscrbr_First_Name', 'Prscrbr_Last_Org_Name', 'specialty']]
                    placeholders = ', '.join(['?'] * len(cols))
                    col_names = ', '.join(cols)
                    values = [row[c] for c in cols]
                    
                    sql = f"INSERT INTO providers ({col_names}) VALUES ({placeholders})"
                    try:
                        cursor.execute(sql, values)
                    except Exception as e:
                        logger.warning(f"Failed to insert NPI {npi}: {e}")

            conn.commit()
            
        logger.info("Database updated.")
        
        # 4. Auto-Hold High Risk
        high_risk_df = df[df['risk_score'] >= 0.85]
        logger.info(f"Found {len(high_risk_df)} high-risk providers.")
        
        for index, row in high_risk_df.iterrows():
            npi = row['provider_id']
            score = row['risk_score']
            name = f"{row.get('Prscrbr_First_Name', '')} {row.get('Prscrbr_Last_Org_Name', '')}".strip()
            
            payload = {
                "npi": int(npi),
                "transaction_id": str(uuid.uuid4()),
                "action": "HOLD",
                "fraud_score": float(score),
                "confidence": 1.0,
                "reasoning": f"Automated Ingestion: Risk Score {score:.4f} >= 0.85",
                "source": "ingest_pipeline",
                "analyst": "system_automation",
                "auto_triggered": True,
                "amount": float(row.get('total_service_cost', 0.0))
            }
            
            try:
                requests.post(FINANCE_API_URL, json=payload, timeout=5)
                logger.info(f"Triggered hold for {npi}")
            except Exception as e:
                logger.error(f"Failed to trigger hold for {npi}: {e}")

    except Exception as e:
        logger.error(f"Error in ingestion process: {e}")

@router.post("/api/ingest/csv")
async def ingest_csv(
    file: UploadFile = File(...), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    ml_assets: dict = Depends(get_ml_assets)
):
    """
    Upload a CSV file with provider data.
    The system will:
    1. Parse the CSV
    2. Calculate Fraud Risk Scores
    3. Update the Database
    4. Automatically Hold Payments for High Risk Providers (>0.85)
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
        
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # 0. Column Mapping (CMS -> Internal)
        # We need to standardize column names before feature engineering
        column_map = {
            'Rndrng_NPI': 'provider_id',
            'PRSCRBR_NPI': 'provider_id',
            'Rndrng_Prvdr_First_Name': 'Prscrbr_First_Name',
            'Rndrng_Prvdr_Last_Org_Name': 'Prscrbr_Last_Org_Name',
            'Rndrng_Prvdr_Type': 'specialty',
            'Prscrbr_Type': 'specialty',
            'Avg_Sbmtd_Chrg': 'avg_submitted_charge',
            'Tot_Srvcs': 'total_services',
            'Tot_Benes': 'total_benes_phys',
            'Tot_Drug_Cst': 'total_drug_cost',
            'Tot_Clms': 'total_scripts',
            'Tot_Benes_Presc': 'total_benes_presc'
        }
        df.rename(columns=column_map, inplace=True)
        
        if 'provider_id' not in df.columns:
             raise HTTPException(status_code=400, detail="CSV must contain 'provider_id' (or 'Rndrng_NPI'/'PRSCRBR_NPI') column")
             
        # Trigger background processing
        background_tasks.add_task(process_ingestion, df, ml_assets)
        
        return {
            "success": True,
            "message": f"Ingestion started for {len(df)} providers. Check logs for progress.",
            "file": file.filename
        }
        
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
