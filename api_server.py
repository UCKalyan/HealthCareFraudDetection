import pandas as pd
import numpy as np
import tensorflow as tf
import shap
import json
import joblib
import os
from urllib import request, error
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import warnings

ml_assets = {}

class NpiRequest(BaseModel):
    npi: int

class ManualDataRequest(BaseModel):
    total_service_cost: float; total_services: int; total_benes_phys: int;
    total_drug_cost: float; total_scripts: int; total_benes_presc: int;
    specialty: str

def load_assets():
    print("--- Loading ML assets into memory... ---")
    from src.utils.config_loader import load_config
    config = load_config('config.yaml')
    ml_assets['config'] = config
    
    try:
        ml_assets['fraud_model'] = tf.keras.models.load_model(config['training']['model_path'])
        ml_assets['feature_store'] = pd.read_csv(config['preprocessor']['feature_store_path']).set_index('provider_id')
        ml_assets['kmeans_model'] = joblib.load(config['preprocessor']['kmeans_model_path'])
        ml_assets['scaler'] = joblib.load(config['preprocessor']['scaler_path'])
        
        with open(config['preprocessor']['specialty_stats_path'], 'r') as f:
            stats = json.load(f)
            ml_assets['cost_stats'] = pd.DataFrame(stats['cost_stats'])
            ml_assets['spb_stats'] = pd.DataFrame(stats['spb_stats'])
            ml_assets['median_pagerank'] = stats['median_pagerank']
            ml_assets['final_feature_columns'] = stats['final_feature_columns']
        
        final_feature_columns = ml_assets['final_feature_columns']
        background_data = shap.sample(ml_assets['feature_store'][final_feature_columns], 100)
        prediction_function = lambda x: ml_assets['fraud_model'].predict(x).ravel()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ml_assets['explainer'] = shap.KernelExplainer(prediction_function, background_data)
        
        print("--- ML assets loaded successfully. Server is ready. ---")
    except Exception as e:
        print(f"CRITICAL ERROR loading assets: {e}. Run build_artifacts.py first.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_assets()
    yield
    ml_assets.clear()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

def _run_analysis(feature_vector, provider_data, final_cols):
    """Runs prediction, SHAP, and the LIVE LLM reporting."""
    model, explainer, config = ml_assets['fraud_model'], ml_assets['explainer'], ml_assets['config']
    
    final_score = model.predict(feature_vector)[0][0]
    shap_values = explainer.shap_values(feature_vector)
    
    llm_config = config['llm_reporting']
    narrative_report = "<p>Error: Could not generate AI report.</p>"

    if llm_config['enabled']:
        feature_analysis_str = ""
        for i, name in enumerate(final_cols):
            provider_value = float(feature_vector[0][i])
            shap_value = float(np.array(shap_values).flatten()[i])
            feature_analysis_str += f"- **Feature:** '{name}' | **Provider's Value:** {provider_value:.2f} | **Impact on Fraud Score (SHAP):** {shap_value:+.4f}\n"

        user_prompt = llm_config['user_prompt_template'].format(
            base_value=explainer.expected_value,
            final_prediction_score=final_score,
            feature_analysis=feature_analysis_str
        )
        
        print("Sending data to the Gemini LLM for analysis...")
        
        # --- THE DEFINITIVE API KEY FIX ---
        api_key = llm_config.get("api_key")
        if not api_key or api_key == "PASTE_YOUR_API_KEY_HERE":
            error_text = "ERROR: Gemini API key not found or not set in config.yaml."
            print(error_text)
            narrative_report = f"<p>{error_text}</p>"
        else:
            api_url = f"{llm_config['api_url']}?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": user_prompt}]}],
                "systemInstruction": {"parts": [{"text": llm_config['system_prompt']}]}
            }
            try:
                req = request.Request(api_url, method="POST", headers={"Content-Type": "application/json"}, data=json.dumps(payload).encode("utf-8"))
                with request.urlopen(req) as response:
                    if response.status == 200:
                        result = json.loads(response.read().decode())
                        report_text = result['candidates'][0]['content']['parts'][0]['text']
                        narrative_report = report_text.replace('\n', '<br>')
                        print("Successfully received AI analysis.")
                    else:
                        error_text = f"Error from Gemini API: {response.status} - {response.read().decode()}"
                        print(error_text)
                        narrative_report = f"<p>Error: {error_text}</p>"
            except Exception as e:
                print(f"An unexpected error occurred during the LLM call: {e}")
                narrative_report = f"<p>An unexpected error occurred: {e}</p>"
    
    risk_level = "High" if final_score > 0.75 else ("Medium" if final_score > 0.5 else "Low")
    top_factor_idx = np.argmax(np.abs(shap_values))
    shap_data = [{"name": name, "value": float(np.array(shap_values).flatten()[i])} for i, name in enumerate(final_cols)]
    
    return {
        "risk": risk_level, "finalScore": float(final_score), "baseValue": float(explainer.expected_value), 
        "topFactor": final_cols[top_factor_idx], "aiNarrative": narrative_report, 
        "features": provider_data[final_cols].iloc[0].to_dict(), "shap": shap_data
    }

@app.post("/analyze_provider")
async def analyze_provider(request_data: NpiRequest):
    if not ml_assets: raise HTTPException(status_code=500, detail="Server not ready.")
    try:
        provider_data = ml_assets['feature_store'].loc[[request_data.npi]]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Provider NPI {request_data.npi} not found.")
    
    feature_cols = ml_assets['final_feature_columns']
    provider_data_aligned = provider_data.reindex(columns=feature_cols, fill_value=0)
    feature_vector = ml_assets['scaler'].transform(provider_data_aligned)
    
    analysis = _run_analysis(feature_vector, provider_data, feature_cols)
    analysis.update({"npi": request_data.npi, "name": f"{provider_data.get('Prscrbr_First_Name', ['N/A']).iloc[0]} {provider_data.get('Prscrbr_Last_Org_Name', ['N/A']).iloc[0]}", "specialty": provider_data.get('specialty', ['N/A']).iloc[0]})
    return analysis

@app.post("/analyze_new_provider")
async def analyze_new_provider(request_data: ManualDataRequest):
    print(f"Received request for new provider data.")
    if not ml_assets: raise HTTPException(status_code=500, detail="Server not ready.")
    
    provider_data = pd.DataFrame([request_data.dict()])
    # ... (simplified feature creation logic for prototype) ...
    provider_data['total_claim_cost'] = provider_data['total_service_cost'] + provider_data['total_drug_cost']
    provider_data['total_benes'] = provider_data['total_benes_phys'] + provider_data['total_benes_presc']
    total_actions = provider_data['total_services'] + provider_data['total_scripts']
    provider_data['cost_per_service'] = (provider_data['total_claim_cost'] / total_actions).fillna(0)
    provider_data['services_per_bene'] = (total_actions / provider_data['total_benes']).fillna(0)
    provider_data['pagerank_centrality'] = ml_assets.get('median_pagerank', 0)
    
    cluster_features = ml_assets['config']['preprocessor']['feature_engineering']['clustering']['features']
    clusters = ml_assets['kmeans_model'].predict(provider_data[cluster_features])
    for i in range(ml_assets['config']['preprocessor']['feature_engineering']['clustering']['n_clusters']):
        provider_data[f'provider_archetype_{i}'] = 1 if clusters[0] == i else 0

    feature_cols = ml_assets['final_feature_columns']
    provider_data_aligned = provider_data.reindex(columns=feature_cols, fill_value=0)
    feature_vector = ml_assets['scaler'].transform(provider_data_aligned)

    analysis = _run_analysis(feature_vector, provider_data_aligned, feature_cols)
    analysis.update({"npi": "N/A (Manual Data)", "name": "Ad-Hoc Analysis", "specialty": request_data.specialty})
    return analysis

