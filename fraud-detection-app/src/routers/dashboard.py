import logging
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from src.dependencies import get_ml_assets

# Configure Logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/dashboard_stats")
async def get_dashboard_stats(ml_assets: dict = Depends(get_ml_assets)):
    # if 'monitor' not in ml_assets:
    #     return JSONResponse(status_code=503, content={"error": "Monitor agent not initialized. Server starting up or failed to load assets."})
    
    # Monitor agent is initialized in api_server.py startup or dependencies?
    # In the original code, it was imported in api_server.py.
    # We need to ensure 'monitor' is in ml_assets.
    # The dependencies.py lifespan didn't explicitly initialize MonitorAgent.
    # We should probably initialize it there or here if it's lightweight.
    # For now, let's assume it's in ml_assets or we initialize it if missing.
    
    if 'monitor' not in ml_assets:
        # Lazy initialization if not present
        from src.agents.monitor import MonitorAgent
        ml_assets['monitor'] = MonitorAgent(ml_assets['feature_store'])
        
    monitor_stats = ml_assets['monitor'].get_stats()
    monitor_stats['active_investigations'] = ml_assets.get('investigation_count', 0)
    
    return monitor_stats

@router.get("/providers")
async def get_providers(
    page: int = 1, 
    limit: int = 10, 
    search: str = "", 
    npi_filter: str = "",
    name_filter: str = "",
    specialty_filter: str = "",
    sort_by: str = "npi", 
    order: str = "asc",
    ml_assets: dict = Depends(get_ml_assets)
):
    from src.database import get_db_connection
    
    offset = (page - 1) * limit
    
    # Base Query
    query = "SELECT * FROM providers WHERE 1=1"
    params = []
    
    # 1. Global Search
    if search:
        search_term = f"%{search}%"
        query += """ AND (
            CAST(provider_id AS TEXT) LIKE ? OR 
            LOWER(Prscrbr_First_Name) LIKE ? OR 
            LOWER(Prscrbr_Last_Org_Name) LIKE ?
        )"""
        params.extend([search_term, search_term.lower(), search_term.lower()])

    # 2. Column Filters
    if npi_filter:
        query += " AND CAST(provider_id AS TEXT) LIKE ?"
        params.append(f"%{npi_filter}%")
    
    if name_filter:
        name_term = f"%{name_filter.lower()}%"
        query += " AND (LOWER(Prscrbr_First_Name) LIKE ? OR LOWER(Prscrbr_Last_Org_Name) LIKE ?)"
        params.extend([name_term, name_term])
        
    if specialty_filter:
        query += " AND LOWER(specialty) LIKE ?"
        params.append(f"%{specialty_filter.lower()}%")
    
    # 3. Sort
    sort_map = {
        "npi": "provider_id",
        "name": "Prscrbr_Last_Org_Name",
        "specialty": "specialty",
        "cost": "cost_per_service",
        "risk": "risk_score"
    }
    sort_col = sort_map.get(sort_by, "provider_id")
    sort_dir = "ASC" if order == "asc" else "DESC"
    
    query += f" ORDER BY {sort_col} {sort_dir}"
    
    # 4. Pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    # Execute
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get Total Count (for pagination)
        # We need to construct a count query with the same filters but without limit/offset/order
        count_query = "SELECT COUNT(*) FROM providers WHERE 1=1"
        count_params = []
        
        # Re-apply filters for count (Code duplication here is minimal and safer than complex string manipulation)
        if search:
            search_term = f"%{search}%"
            count_query += """ AND (
                CAST(provider_id AS TEXT) LIKE ? OR 
                LOWER(Prscrbr_First_Name) LIKE ? OR 
                LOWER(Prscrbr_Last_Org_Name) LIKE ?
            )"""
            count_params.extend([search_term, search_term.lower(), search_term.lower()])

        if npi_filter:
            count_query += " AND CAST(provider_id AS TEXT) LIKE ?"
            count_params.append(f"%{npi_filter}%")
        
        if name_filter:
            name_term = f"%{name_filter.lower()}%"
            count_query += " AND (LOWER(Prscrbr_First_Name) LIKE ? OR LOWER(Prscrbr_Last_Org_Name) LIKE ?)"
            count_params.extend([name_term, name_term])
            
        if specialty_filter:
            count_query += " AND LOWER(specialty) LIKE ?"
            count_params.append(f"%{specialty_filter.lower()}%")
            
        cursor.execute(count_query, count_params)
        total_records = cursor.fetchone()[0]
        
        # Get Data
        cursor.execute(query, params)
        rows = cursor.fetchall()
    
    # Format for UI
    providers = []
    for row in rows:
        # Use pre-calculated score
        risk_score = float(row['risk_score'])
        
        # --- Dual-Score Visualization (Nested Learning) ---
        early_warning_score = None
        alert = None
        
        # If Fast Model is loaded, compute real-time score
        if ml_assets.get('fraud_model_fast') and ml_assets.get('scaler'):
             try:
                 # We need features to predict. 
                 # Currently, get_providers only fetches from DB (basic info).
                 # To do this efficiently, we'd need the feature vector.
                 # For now, let's skip on-the-fly prediction for the LIST view to avoid latency.
                 # Instead, we'll just show a placeholder or only do it if we had the features.
                 # Actually, let's check if we can get features easily.
                 # The 'providers' table might not have all features.
                 # Let's rely on the 'provider details' page for the full check.
                 pass
             except Exception:
                 pass
        
        if risk_score > 0.75:
            risk_status = "High"
        elif risk_score > 0.30:
            risk_status = "Medium"
        else:
            risk_status = "Low"
            
        providers.append({
            "npi": int(row['provider_id']),
            "name": f"{row['Prscrbr_First_Name']} {row['Prscrbr_Last_Org_Name']}",
            "specialty": row['specialty'],
            "cost_per_service": float(row['cost_per_service'] or 0.0),
            "services_per_bene": float(row['services_per_bene'] or 0.0),
            "risk_status": risk_status,
            "risk_score": risk_score,
            # "early_warning_score": early_warning_score, # Disabled for list view performance
            # "alert": alert
        })

    return {
        "data": providers,
        "total": total_records,
        "page": page,
        "limit": limit,
        "total_pages": (total_records + limit - 1) // limit
    }

@router.get("/graph_data/{npi}")
async def get_graph_data(npi: int, ml_assets: dict = Depends(get_ml_assets)):
    """
    Generates a mock network graph for a specific provider.
    """
    from src.database import get_db_connection
    
    try:
        with get_db_connection() as conn:
            # Verify provider exists
            provider_data = pd.read_sql_query("SELECT * FROM providers WHERE provider_id = ?", conn, params=(npi,))
            
            if provider_data.empty:
                 raise HTTPException(status_code=404, detail="Provider not found")
                 
            provider_name = f"{provider_data['Prscrbr_First_Name'].iloc[0]} {provider_data['Prscrbr_Last_Org_Name'].iloc[0]}"
            risk_score = float(provider_data['risk_score'].iloc[0])
            
            # Get Candidates for Similarity
            # Sample 500 random providers from DB
            candidate_pool = pd.read_sql_query("SELECT * FROM providers ORDER BY RANDOM() LIMIT 500", conn)
            
    except Exception as e:
         if isinstance(e, HTTPException): raise e
         raise HTTPException(status_code=500, detail=str(e))

    nodes = []
    edges = []
    
    # 1. Central Node (The Provider)
    nodes.append({
        "data": {
            "id": str(npi),
            "label": provider_name,
            "type": "provider",
            "risk": risk_score,
            "size": 40 + (risk_score * 20),
            "color": "#ef4444" if risk_score > 0.7 else "#3b82f6"
        }
    })
    
    # 2. Real-Time Similarity Search (Peer Graph)
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Get feature vector for the target provider
        features = ml_assets['final_feature_columns']
        target_vector = ml_assets['scaler'].transform(provider_data[features])
        
        # Ensure target is in the pool (it might not be if random sample didn't pick it)
        if npi not in candidate_pool['provider_id'].values:
            candidate_pool = pd.concat([candidate_pool, provider_data])
            
        pool_vectors = ml_assets['scaler'].transform(candidate_pool[features])
        
        # Calculate Similarity
        similarities = cosine_similarity(target_vector, pool_vectors).flatten()
        
        # Get Top 6 (Index 0 is the target itself, so we want 1-6)
        top_indices = similarities.argsort()[-6:-1][::-1]
        
        for idx in top_indices:
            peer_row = candidate_pool.iloc[idx]
            peer_npi = peer_row['provider_id']
            peer_score = similarities[idx]
            
            if peer_npi == npi: continue # Skip self
            
            peer_row = candidate_pool.iloc[idx]
            peer_name = f"{peer_row.get('Prscrbr_First_Name', '')} {peer_row.get('Prscrbr_Last_Org_Name', '')}"
            peer_risk = float(peer_row.get('risk_score', 0.0))
            
            # Add Peer Node
            nodes.append({
                "data": {
                    "id": str(peer_npi),
                    "label": peer_name,
                    "type": "peer",
                    "risk": peer_risk,
                    "color": "#ef4444" if peer_risk > 0.75 else ("#eab308" if peer_risk > 0.30 else "#3b82f6")
                }
            })
            
            # Add Edge (Similarity)
            edges.append({
                "data": {
                    "source": str(npi),
                    "target": str(peer_npi),
                    "label": f"{int(peer_score*100)}% Match"
                }
            })
            
    except Exception as e:
        logger.error(f"Error generating similarity graph: {e}")
        # Fallback: Add a generic error node
        nodes.append({
            "data": {
                "id": "error",
                "label": "Error calculating similarity",
                "type": "error",
                "color": "#94a3b8"
            }
        })

    return {"elements": {"nodes": nodes, "edges": edges}}

@router.get("/api/provider_risk/{npi}")
async def get_provider_risk(npi: int, ml_assets: dict = Depends(get_ml_assets)):
    """
    Computes the real-time Dual-Score (Stable vs Fast) for a provider.
    """
    from fastapi.responses import JSONResponse
    try:
        scaler = ml_assets.get('scaler')
        model = ml_assets.get('fraud_model')
        model_fast = ml_assets.get('fraud_model_fast')
        final_feature_columns = ml_assets.get('final_feature_columns')
        feature_store = ml_assets.get('feature_store')
        
        if feature_store is None:
            logger.error("Feature store is None")
            return JSONResponse(status_code=404, content={"error": "Feature store not loaded"})
            
        if npi not in feature_store.index:
            return JSONResponse(status_code=404, content={"error": "Provider features not found"})
            
        # Prepare Data
        provider_data = feature_store.loc[[npi]]
        provider_data_aligned = provider_data.reindex(columns=final_feature_columns, fill_value=0)
        feature_vector = scaler.transform(provider_data_aligned)
        
        # 1. Stable Score
        stable_score = float(model.predict(feature_vector, verbose=0)[0][0])
        
        # 2. Fast Score
        fast_score = -1.0
        if model_fast:
            fast_score = float(model_fast.predict(feature_vector, verbose=0)[0][0])
            
        result = {
            "npi": npi,
            "risk_score": stable_score,
            "early_warning_score": fast_score if fast_score != -1.0 else None,
            "alert": None
        }
        
        if fast_score > 0.8 and stable_score < 0.5:
            result["alert"] = "⚠️ EMERGING THREAT: Recent behavior deviates significantly from history."
            
        return result
        
    except Exception as e:
        logger.error(f"Error computing risk: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
