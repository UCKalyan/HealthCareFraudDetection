import logging
import pandas as pd
import numpy as np
import io
import requests
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from src.dependencies import get_ml_assets
from src.database import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter()

FINANCE_API_URL = "http://localhost:8001/api/process_payment_hold"

def detect_file_format(df: pd.DataFrame) -> str:
    """
    Detect if uploaded CSV is a test batch or raw CMS data.
    
    Returns:
        'batch' - Pre-aggregated test batch file with feature engineering done
        'raw' - Raw CMS claims data requiring full processing
    """
    batch_indicators = ['has_part_b', 'has_part_d', 'cost_per_service', 'services_per_bene']
    
    if all(col in df.columns for col in batch_indicators):
        logger.info("Detected BATCH file format (pre-aggregated test data)")
        return 'batch'
    
    logger.info("Detected RAW CMS data format")
    return 'raw'

def process_batch_file(df: pd.DataFrame, ml_assets: dict, filename: str = None) -> pd.DataFrame:
    """
    Process pre-aggregated batch files with MINIMAL feature engineering.
    
    Batch files already have:
    - cost_per_service, services_per_bene (ratios calculated)
    - has_part_b, has_part_d (merge indicators)
    - specialty, total_claim_cost, total_benes (aggregated data)
    
    This function adds MISSING ML features:
    - spb_z_tanh (calculated from services_per_bene)
    - pagerank_centrality (placeholder: median value)
    - provider_archetype_0-4 (placeholder: zeros)
    
    Returns:
        DataFrame with all features and risk scores calculated
    """
    logger.info(f"Processing batch file with {len(df)} providers...")
    
    # Ensure provider_id exists
    if 'provider_id' not in df.columns:
        raise ValueError("Batch file must contain 'provider_id' column")
    
    # 1. ALWAYS recalculate spb_z_tanh from production specialty stats
    # Batch files may carry stale values from a different data vintage
    # (e.g. 2022 Family Practice mean is much lower → inflated z-scores)
    if 'services_per_bene' in df.columns:
        spb_stats = ml_assets.get('spb_stats')
        if spb_stats is not None:
            logger.info("Recalculating spb_z_tanh using production specialty statistics")
            spb_mean_map = spb_stats.set_index('specialty')['mean'].to_dict()
            spb_std_map = spb_stats.set_index('specialty')['std'].to_dict()
            
            global_mean = spb_stats['mean'].mean()
            global_std = spb_stats['std'].mean()
            
            def get_z_score(row):
                spec = row.get('specialty', 'Unknown')
                mean = spb_mean_map.get(spec, global_mean)
                std = spb_std_map.get(spec, global_std)
                if std == 0 or pd.isna(std): 
                    return 0
                return (row['services_per_bene'] - mean) / std
            
            df['spb_z'] = df.apply(get_z_score, axis=1)
            df['spb_z_tanh'] = np.tanh(0.5 * df['spb_z'])
        else:
            logger.warning("No specialty stats available, using simple normalization")
            df['spb_z_tanh'] = np.tanh(0.1 * df['services_per_bene'])
    elif 'spb_z_tanh' not in df.columns:
        logger.warning("services_per_bene not found, setting spb_z_tanh to 0")
        df['spb_z_tanh'] = 0.0
    
    # 2. Set pagerank_centrality to production median
    # ALWAYS override — batch files may carry a stale median from a different
    # data vintage (e.g. 2022 median=3.68e-07 vs 2023 median=7.36e-07).
    # The RobustScaler IQR for this feature is ~1e-11, so even a tiny raw
    # difference produces scaled values of -28,000+, saturating predictions to 1.0.
    median_pr = ml_assets.get('median_pagerank', 1e-6)
    df['pagerank_centrality'] = median_pr
    logger.info(f"Set pagerank_centrality to production median: {median_pr}")
    
    # 3. Add provider archetypes (placeholder - requires clustering model)
    for i in range(5):
        col_name = f'provider_archetype_{i}'
        if col_name not in df.columns:
            df[col_name] = 0.0
    logger.info("Added provider archetype placeholders (0-4)")
    
    # 4. Calculate risk scores with complete feature set
    feature_columns = ml_assets['final_feature_columns']
    
    # Ensure all features exist
    missing_features = []
    for col in feature_columns:
        if col not in df.columns:
            logger.warning(f"Missing feature column: {col}, setting to 0")
            df[col] = 0.0
            missing_features.append(col)
    
    if missing_features:
        logger.warning(f"Added {len(missing_features)} missing features with default values")
    
    # Extract features and scale — always recalculate risk scores from the model
    X = df[feature_columns]
    X_scaled = ml_assets['scaler'].transform(X)
    
    # Predict risk scores
    risk_scores = ml_assets['fraud_model'].predict(X_scaled, verbose=0).flatten()
    df['risk_score'] = risk_scores
    
    logger.info(f"Risk scores calculated. Min: {risk_scores.min():.4f}, Max: {risk_scores.max():.4f}, Mean: {risk_scores.mean():.4f}")
    
    return df

def finalize_batch_processing(df: pd.DataFrame, ml_assets: dict, enable_auto_hold: bool = True):
    """
    Finalize batch processing: update database and trigger auto-holds.
    
    Args:
        df: DataFrame with risk scores calculated
        ml_assets: ML assets dictionary
        enable_auto_hold: Whether to trigger automatic payment holds (default: True)
    
    Returns:
        Dictionary with auto-hold results
    """
    # Update database with providers and risk scores
    update_database_with_batch(df, ml_assets)
    
    # Trigger auto-hold for high-risk providers
    auto_hold_results = trigger_auto_hold_for_batch(df, enable_auto_hold)
    
    return auto_hold_results


def trigger_auto_hold_for_batch(df: pd.DataFrame, enable_auto_hold: bool = True):
    """
    Trigger automatic payment holds for high-risk providers from batch upload.
    Identical behavior to raw CMS processing.
    
    Args:
        df: DataFrame with provider_id, risk_score, and other fields
        enable_auto_hold: Flag to enable/disable auto-hold (default:True)
    
    Returns:
        Dictionary with hold counts
    """
    if not enable_auto_hold:
        logger.info("Auto-hold disabled for this batch upload")
        return {"triggered": 0, "successful": 0, "failed": 0}
    
    high_risk_df = df[df['risk_score'] >= 0.85]
    logger.info(f"Auto-hold: Found {len(high_risk_df)} high-risk providers (>= 0.85)")
    
    if len(high_risk_df) == 0:
        return {"triggered": 0, "successful": 0, "failed": 0}
    
    hold_success_count = 0
    hold_failure_count = 0
    
    for _, row in high_risk_df.iterrows():
        npi = row['provider_id']
        score = row['risk_score']
        specialty = row.get('specialty', 'Unknown')
        total_claim_cost = row.get('total_claim_cost', 0.0)
        
        payload = {
            "npi": int(npi),
            "transaction_id": str(uuid.uuid4()),
            "action": "HOLD",
            "fraud_score": float(score),
            "confidence": 1.0,
            "reasoning": f"Automated Batch Ingestion: Risk Score {score:.4f} >= 0.85 (Specialty: {specialty})",
            "source": "batch_ingest_pipeline",
            "analyst": "system_automation",
            "auto_triggered": True,
            "amount": float(total_claim_cost)
        }
        
        try:
            response = requests.post(FINANCE_API_URL, json=payload, timeout=5)
            if response.status_code == 200:
                logger.info(f"✓ Auto-hold triggered for NPI {npi} (score: {score:.4f})")
                hold_success_count += 1
            else:
                logger.warning(f"✗ Auto-hold failed for NPI {npi}: HTTP {response.status_code}")
                hold_failure_count += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Auto-hold request failed for NPI {npi}: {e}")
            hold_failure_count += 1
    
    logger.info(f"Auto-hold summary: {hold_success_count} successful, {hold_failure_count} failed")
    
    return {
        "triggered": len(high_risk_df),
        "successful": hold_success_count,
        "failed": hold_failure_count
    }


def update_database_with_batch(df: pd.DataFrame, ml_assets: dict):
    """
    Update database with providers from batch file.
    Makes providers searchable and analyzable via UI.
    
    Args:
        df: DataFrame with provider_id, risk_score, and other features
        ml_assets: ML assets dictionary (for feature store updates)
    """
    logger.info(f"Updating database with {len(df)} providers from batch...")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updated_count = 0
            inserted_count = 0
            inserted_npis = []
            
            for _, row in df.iterrows():
                npi = str(int(row['provider_id'])) if pd.notna(row['provider_id']) else None
                if not npi:
                    continue

                # Extract provider information
                risk_score = float(row['risk_score']) if pd.notna(row.get('risk_score')) else 0.0
                specialty = row.get('specialty', 'Unknown')

                # Get additional fields if available
                total_benes = int(row.get('total_benes', 0)) if pd.notna(row.get('total_benes')) else 0
                total_claim_cost = float(row.get('total_claim_cost', 0.0)) if pd.notna(row.get('total_claim_cost')) else 0.0
                total_service_cost = float(row.get('total_service_cost', 0.0)) if pd.notna(row.get('total_service_cost')) else 0.0
                cost_per_service = float(row.get('cost_per_service', 0.0)) if pd.notna(row.get('cost_per_service')) else 0.0
                services_per_bene = float(row.get('services_per_bene', 0.0)) if pd.notna(row.get('services_per_bene')) else 0.0
                
                # Engineered features (already recalculated with production stats)
                spb_z_tanh = float(row.get('spb_z_tanh', 0.0)) if pd.notna(row.get('spb_z_tanh')) else 0.0
                has_part_b = int(row.get('has_part_b', 0)) if pd.notna(row.get('has_part_b')) else 0
                has_part_d = int(row.get('has_part_d', 0)) if pd.notna(row.get('has_part_d')) else 0
                pagerank = float(row.get('pagerank_centrality', 0.0)) if pd.notna(row.get('pagerank_centrality')) else 0.0
                # Provider archetypes (default: Standard Practice Pattern)
                arch = []
                for i in range(5):
                    default = 1.0 if i == 0 else 0.0
                    val = row.get(f'provider_archetype_{i}', default)
                    arch.append(float(val) if pd.notna(val) else default)

                # Check if provider exists
                cursor.execute("SELECT 1 FROM providers WHERE provider_id = ?", (npi,))
                exists = cursor.fetchone()

                if exists:
                    cursor.execute("""
                        UPDATE providers 
                        SET risk_score = ?,
                            specialty = ?,
                            total_claim_cost = ?,
                            total_service_cost = ?,
                            cost_per_service = ?,
                            services_per_bene = ?,
                            total_benes = ?,
                            spb_z_tanh = ?,
                            has_part_b = ?,
                            has_part_d = ?,
                            pagerank_centrality = ?,
                            provider_archetype_0 = ?,
                            provider_archetype_1 = ?,
                            provider_archetype_2 = ?,
                            provider_archetype_3 = ?,
                            provider_archetype_4 = ?,
                            agent_analysed_at = NULL,
                            created_at = COALESCE(created_at, datetime('now'))
                        WHERE provider_id = ?
                    """, (risk_score, specialty, total_claim_cost, total_service_cost,
                           cost_per_service, services_per_bene, total_benes,
                           spb_z_tanh, has_part_b, has_part_d, pagerank,
                           arch[0], arch[1], arch[2], arch[3], arch[4], npi))
                    updated_count += 1
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO providers (
                                provider_id, 
                                risk_score, 
                                specialty,
                                total_benes,
                                total_claim_cost,
                                total_service_cost,
                                cost_per_service,
                                services_per_bene,
                                spb_z_tanh,
                                has_part_b,
                                has_part_d,
                                pagerank_centrality,
                                provider_archetype_0,
                                provider_archetype_1,
                                provider_archetype_2,
                                provider_archetype_3,
                                provider_archetype_4,
                                created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        """, (npi, risk_score, specialty, total_benes,
                               total_claim_cost, total_service_cost,
                               cost_per_service, services_per_bene,
                               spb_z_tanh, has_part_b, has_part_d, pagerank,
                               arch[0], arch[1], arch[2], arch[3], arch[4]))
                        inserted_count += 1
                        inserted_npis.append(npi)
                    except Exception as e:
                        logger.warning(f"Failed to insert NPI {npi}: {e}")
            
            conn.commit()

            logger.info(f"Database updated: {inserted_count} inserted, {updated_count} updated")
            if inserted_npis:
                logger.info(f"Newly inserted NPIs ({len(inserted_npis)}): {inserted_npis}")
            
        # Update in-memory feature store (for real-time risk checks)
        if 'feature_store' in ml_assets:
            feature_columns = ml_assets['final_feature_columns']
            new_features_df = df.set_index('provider_id')[feature_columns]
            
            current_store = ml_assets['feature_store']
            updated_store = pd.concat([current_store, new_features_df])
            # Remove duplicates, keeping the newest
            updated_store = updated_store[~updated_store.index.duplicated(keep='last')]
            
            ml_assets['feature_store'] = updated_store
            logger.info(f"In-memory feature store updated. Total providers: {len(updated_store)}")
            
    except Exception as e:
        logger.error(f"Error updating database with batch: {e}")
        raise


def archive_uploaded_file(file_path: Path, filename: str) -> str:
    """
    Move uploaded batch file to processed folder with timestamp.
    
    Args:
        file_path: Path to temporary uploaded file
        filename: Original filename
    
    Returns:
        Archived filename with timestamp
    """
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_name = f"{timestamp}_{filename}"
    archived_path = processed_dir / archived_name
    
    # Move file to processed directory
    shutil.move(str(file_path), str(archived_path))
    
    logger.info(f"File archived as: {archived_name}")
    
    return archived_name


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
            
        # Derive has_part_b / has_part_d from actual data
        df['has_part_b'] = (df.get('total_service_cost', pd.Series(0, index=df.index)) > 0).astype(int)
        df['has_part_d'] = (df.get('total_drug_cost', pd.Series(0, index=df.index)) > 0).astype(int)
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
                npi = row.get('provider_id')
                if pd.isna(npi):
                    continue
                score = float(row['risk_score']) if pd.notna(row.get('risk_score')) else 0.0
                specialty = row.get('specialty', 'Unknown')
                
                # Extract engineered features
                # CMS raw data often uses 'total_benes_phys' representing total beneficiaries
                total_benes_val = row.get('total_benes_phys') if pd.notna(row.get('total_benes_phys')) else row.get('total_benes', 0)
                total_benes = int(total_benes_val) if pd.notna(total_benes_val) else 0
                
                total_claim_cost = float(row.get('total_claim_cost', 0.0)) if pd.notna(row.get('total_claim_cost')) else 0.0
                total_service_cost = float(row.get('total_service_cost', 0.0)) if pd.notna(row.get('total_service_cost')) else 0.0
                cost_per_service = float(row.get('cost_per_service', 0.0)) if pd.notna(row.get('cost_per_service')) else 0.0
                services_per_bene = float(row.get('services_per_bene', 0.0)) if pd.notna(row.get('services_per_bene')) else 0.0
                
                spb_z_tanh = float(row.get('spb_z_tanh', 0.0)) if pd.notna(row.get('spb_z_tanh')) else 0.0
                has_part_b = int(row.get('has_part_b', 0)) if pd.notna(row.get('has_part_b')) else 0
                has_part_d = int(row.get('has_part_d', 0)) if pd.notna(row.get('has_part_d')) else 0
                pagerank = float(row.get('pagerank_centrality', 0.0)) if pd.notna(row.get('pagerank_centrality')) else 0.0
                
                arch = []
                for i in range(5):
                    default = 1.0 if i == 0 else 0.0
                    val = row.get(f'provider_archetype_{i}', default)
                    arch.append(float(val) if pd.notna(val) else default)
                
                cursor.execute("SELECT 1 FROM providers WHERE provider_id = ?", (npi,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute("""
                        UPDATE providers 
                        SET risk_score = ?,
                            specialty = ?,
                            total_claim_cost = ?,
                            total_service_cost = ?,
                            cost_per_service = ?,
                            services_per_bene = ?,
                            total_benes = ?,
                            spb_z_tanh = ?,
                            has_part_b = ?,
                            has_part_d = ?,
                            pagerank_centrality = ?,
                            provider_archetype_0 = ?,
                            provider_archetype_1 = ?,
                            provider_archetype_2 = ?,
                            provider_archetype_3 = ?,
                            provider_archetype_4 = ?,
                            agent_analysed_at = NULL,
                            created_at = COALESCE(created_at, datetime('now'))
                        WHERE provider_id = ?
                    """, (score, specialty, total_claim_cost, total_service_cost,
                           cost_per_service, services_per_bene, total_benes,
                           spb_z_tanh, has_part_b, has_part_d, pagerank,
                           arch[0], arch[1], arch[2], arch[3], arch[4], npi))
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO providers (
                                provider_id, 
                                risk_score, 
                                specialty,
                                total_benes,
                                total_claim_cost,
                                total_service_cost,
                                cost_per_service,
                                services_per_bene,
                                spb_z_tanh,
                                has_part_b,
                                has_part_d,
                                pagerank_centrality,
                                provider_archetype_0,
                                provider_archetype_1,
                                provider_archetype_2,
                                provider_archetype_3,
                                provider_archetype_4,
                                Prscrbr_First_Name,
                                Prscrbr_Last_Org_Name,
                                created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        """, (npi, score, specialty, total_benes,
                               total_claim_cost, total_service_cost,
                               cost_per_service, services_per_bene,
                               spb_z_tanh, has_part_b, has_part_d, pagerank,
                               arch[0], arch[1], arch[2], arch[3], arch[4],
                               row.get('Prscrbr_First_Name'), row.get('Prscrbr_Last_Org_Name')))
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
    enable_auto_hold: bool = True,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    ml_assets: dict = Depends(get_ml_assets)
):
    """
    Upload a CSV file with provider data.
    
    Supports two file formats:
    1. Pre-aggregated batch files (test data) - Processed immediately with instant results
    2. Raw CMS claims data - Background processing with database updates
    
    The system will automatically detect the format and process accordingly.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
        
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Detect file format
        file_format = detect_file_format(df)
        
        if file_format == 'batch':
            # BATCH FILE PROCESSING PATH
            logger.info(f"Processing batch file: {file.filename}")
            
            # Save uploaded file temporarily
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            temp_path = upload_dir / file.filename
            
            with open(temp_path, 'wb') as f:
                f.write(contents)
            
            # Process batch file (adds missing features and calculates risk scores)
            df_scored = process_batch_file(df, ml_assets, filename=file.filename)
            
            # Finalize: update database and trigger auto-holds
            auto_hold_results = finalize_batch_processing(df_scored, ml_assets, enable_auto_hold)
            
            # Archive file to processed folder
            archived_name = archive_uploaded_file(temp_path, file.filename)
            
            # Prepare response with immediate results
            high_risk_df = df_scored[df_scored['risk_score'] >= 0.85]
            high_risk_count = len(high_risk_df)
            
            # Get top 10 providers for preview
            preview_providers = df_scored.nlargest(10, 'risk_score')[
                ['provider_id', 'risk_score', 'specialty']
            ].to_dict('records')
            
            logger.info(f"Batch processing complete. {high_risk_count} high-risk providers found.")
            
            return {
                "success": True,
                "message": f"Batch file processed: {len(df_scored)} providers scored and added to database",
                "file": file.filename,
                "archived_as": archived_name,
                "format": "batch",
                "total_providers": len(df_scored),
                "high_risk_count": high_risk_count,
                "high_risk_threshold": 0.85,
                "auto_hold_enabled": enable_auto_hold,
                "auto_hold_results": auto_hold_results,
                "providers": preview_providers,
                "stats": {
                    "min_risk": float(df_scored['risk_score'].min()),
                    "max_risk": float(df_scored['risk_score'].max()),
                    "mean_risk": float(df_scored['risk_score'].mean()),
                    "median_risk": float(df_scored['risk_score'].median())
                },
                "note": "Providers are now searchable in the UI and can be analyzed by agents"
            }
        
        else:
            # RAW CMS DATA PROCESSING PATH (existing logic)
            logger.info(f"Processing raw CMS data: {file.filename}")
            
            # Column Mapping (CMS -> Internal)
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
                raise HTTPException(
                    status_code=400, 
                    detail="CSV must contain 'provider_id' (or 'Rndrng_NPI'/'PRSCRBR_NPI') column"
                )
                
            # Trigger background processing
            background_tasks.add_task(process_ingestion, df, ml_assets)
            
            return {
                "success": True,
                "message": f"Ingestion started for {len(df)} providers. Check logs for progress.",
                "file": file.filename,
                "format": "raw",
                "total_providers": len(df)
            }
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

