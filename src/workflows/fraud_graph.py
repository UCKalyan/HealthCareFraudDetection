import pandas as pd
import numpy as np
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
import json

# Define the State
class FraudAnalysisState(TypedDict):
    npi: int
    provider_data: Any 
    ml_assets: Dict[str, Any] 
    
    # Outputs
    risk_score: float
    risk_level: str
    shap_values: List[Dict]
    graph_data: Dict
    anomalies: List[str]
    final_report: str
    investigator_finding: str
    analyst_finding: str
    trace: List[str] # Execution trace
    
# --- Nodes ---

def calculate_risk_node(state: FraudAnalysisState):
    """
    Node 1: Calculates Fraud Risk Score using the TensorFlow model.
    Role: Analyst (Risk Analysis)
    """
    trace = state.get('trace', [])
    
    # THINK
    trace.append("💭 **Think**: Assessing fraud risk using the TensorFlow model and SHAP explainers.")
    print("\n* Node A (Analyst) 💭: Assessing fraud risk...")
    
    assets = state['ml_assets']
    provider_data = state['provider_data']
    
    # Ensure DataFrame
    if isinstance(provider_data, dict):
        provider_data = pd.DataFrame([provider_data])
        
    features = assets['final_feature_columns']
    
    # ACT
    trace.append("⚡ **Act**: Running `fraud_model.predict()` and calculating SHAP values.")
    
    # Prepare data
    aligned_data = provider_data.reindex(columns=features, fill_value=0)
    feature_vector = assets['scaler'].transform(aligned_data)
    
    # Predict
    score = float(assets['fraud_model'].predict(feature_vector)[0][0])
    
    # SHAP
    shap_vals = assets['explainer'].shap_values(feature_vector)
    
    # Robust handling for different SHAP return types (list of arrays vs array)
    if isinstance(shap_vals, list):
        # For classification, it returns a list of arrays (one for each class)
        # We usually want the positive class (index 1) or the only class (index 0)
        target_shap = shap_vals[1] if len(shap_vals) > 1 else shap_vals[0]
    else:
        target_shap = shap_vals
        
    shap_flat = np.array(target_shap).flatten()
        
    # Format SHAP for UI
    shap_ui = []
    
    # Archetype Mapping (Same as API Server)
    archetype_map = {
        'provider_archetype_0': 'Routine Care',
        'provider_archetype_1': 'High-Value Specialist',
        'provider_archetype_2': 'Tier 2 High Cost',
        'provider_archetype_3': 'Elevated Risk Profile',
        'provider_archetype_4': 'Extreme Outlier'
    }
    
    for i, col in enumerate(features):
        # Map name if it exists in the map, otherwise use original
        display_name = archetype_map.get(col, col)
        shap_ui.append({"name": display_name, "value": float(shap_flat[i])})
        
    risk_level = "High" if score > 0.75 else ("Medium" if score > 0.5 else "Low")
    
    # OBSERVE
    top_factor = shap_ui[0]['name'] if shap_ui else "None"
    trace.append(f"👀 **Observe**: Risk Score: {score:.4f} ({risk_level}). Top Driver: {top_factor}.")
    
    # Analyst Finding (Detailed with rich HTML)
    sorted_shap = sorted(shap_ui, key=lambda x: abs(x['value']), reverse=True)
    top_3 = sorted_shap[:3]
    
    # Build risk drivers HTML
    drivers_html = "<ul class='space-y-2 mt-2'>\n"
    for i, item in enumerate(top_3, 1):
        impact_color = "text-red-600" if item['value'] > 0 else "text-green-600"
        impact_sign = "+" if item['value'] > 0 else ""
        drivers_html += f"<li class='text-sm'><b>{i}. {item['name']}</b>: <span class='{impact_color} font-semibold'>{impact_sign}{item['value']:.3f}</span> impact on risk score</li>\n"
    drivers_html += "</ul>"
    
    # Risk level specific message
    if risk_level == "High":
        risk_message = "<span class='text-red-600 font-bold'>⚠️ HIGH RISK</span> - Immediate investigation recommended"
    elif risk_level == "Medium":
        risk_message = "<span class='text-yellow-600 font-bold'>⚡ MEDIUM RISK</span> - Review recommended"
    else:
        risk_message = "<span class='text-green-600 font-bold'>✓ LOW RISK</span> - Standard monitoring"
    
    analyst_finding_text = f"""
    <div class="space-y-2">
        <div class="bg-blue-50/40 p-3 rounded-lg">
            <h3 class="text-sm font-bold text-slate-700 mb-2">📊 Risk Score Analysis</h3>
            <p class="text-sm"><b>Overall Assessment:</b> {risk_message}</p>
            <p class="text-sm"><b>Risk Score:</b> <span class="font-mono font-bold text-lg">{score:.4f}</span></p>
        </div>
        
        <div class="bg-purple-50/40 p-3 rounded-lg">
            <h3 class="text-sm font-bold text-slate-700 mb-2">🎯 Key Risk Drivers</h3>
            <p class="text-xs text-slate-600 mb-1">The following features contributed most significantly to this risk assessment:</p>
            {drivers_html}
        </div>
    </div>
    """

    
    # REFLECT
    trace.append(f"🤔 **Reflect**: Provider is {risk_level} risk. Proceeding to Network Analysis.")
    
    return {
        "risk_score": score,
        "risk_level": risk_level,
        "shap_values": shap_ui,
        "analyst_finding": analyst_finding_text,
        "trace": trace
    }

def analyze_network_node(state: FraudAnalysisState):
    """
    Node 2: Performs Network Analysis (Cosine Similarity).
    Role: Network Analyst (Graph Mining)
    """
    trace = state['trace']
    
    # THINK
    trace.append("💭 **Think**: Identifying collusion patterns by finding similar providers.")
    print("* Node B (Network Analyst) 💭: Mining graph for collusion...")
    
    assets = state['ml_assets']
    npi = state['npi']
    provider_data = state['provider_data']
    
    # ACT
    trace.append("⚡ **Act**: Computing Cosine Similarity on feature vectors against the provider database.")
    
    # Logic copied from api_server.py
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        
        features = assets['final_feature_columns']
        target_vector = assets['scaler'].transform(provider_data[features])
        
        # Sample for speed
        candidate_pool = assets['feature_store'].sample(min(500, len(assets['feature_store'])))
        if npi not in candidate_pool.index:
            candidate_pool = pd.concat([candidate_pool, provider_data])
            
        pool_vectors = assets['scaler'].transform(candidate_pool[features])
        similarities = cosine_similarity(target_vector, pool_vectors).flatten()
        
        top_indices = similarities.argsort()[-6:-1][::-1]
        
        nodes = []
        edges = []
        
        # Central Node
        p_name = f"{provider_data.iloc[0].get('Prscrbr_First_Name', '')} {provider_data.iloc[0].get('Prscrbr_Last_Org_Name', '')}"
        nodes.append({
            "data": {
                "id": str(npi),
                "label": p_name,
                "type": "provider",
                "risk": state['risk_score'],
                "color": "#ef4444" if state['risk_score'] > 0.75 else ("#eab308" if state['risk_score'] > 0.5 else "#3b82f6")
            }
        })
        
        for idx in top_indices:
            peer_npi = candidate_pool.index[idx]
            if peer_npi == npi: continue
            
            peer_row = candidate_pool.iloc[idx]
            peer_name = f"{peer_row.get('Prscrbr_First_Name', '')} {peer_row.get('Prscrbr_Last_Org_Name', '')}"
            peer_risk = float(peer_row.get('risk_score', 0.0))
            
            nodes.append({
                "data": {
                    "id": str(peer_npi),
                    "label": peer_name,
                    "type": "peer",
                    "risk": peer_risk,
                    "color": "#ef4444" if peer_risk > 0.75 else ("#eab308" if peer_risk > 0.5 else "#3b82f6")
                }
            })
            edges.append({
                "data": {
                    "source": str(npi),
                    "target": str(peer_npi),
                    "label": f"{int(similarities[idx]*100)}%"
                }
            })
            
        # OBSERVE
        peer_count = len(nodes) - 1
        trace.append(f"👀 **Observe**: Found {peer_count} similar peers with matching billing patterns.")
        
        # Update Investigator Finding
        current_finding = state.get('investigator_finding', '')
        network_finding = f"<b>Network Analysis:</b> Identified <b>{peer_count}</b> similar peers with matching billing patterns.<br>"
        updated_finding = network_finding + current_finding
        
        # REFLECT
        trace.append("🤔 **Reflect**: Network graph constructed. Checking for specific anomalies.")
            
        return {
            "graph_data": {"elements": {"nodes": nodes, "edges": edges}}, 
            "investigator_finding": updated_finding,
            "trace": trace
        }
        
    except Exception as e:
        print(f"Graph Error: {e}")
        trace.append(f"❌ **Error**: Graph analysis failed: {e}")
        return {"graph_data": {}, "trace": trace}

def detect_anomalies_node(state: FraudAnalysisState):
    """
    Node 3: Rule-based Anomaly Detection.
    Role: Investigator (Anomaly Detection)
    """
    trace = state['trace']
    
    # THINK
    trace.append("💭 **Think**: Checking for specific rule violations (High Cost, High Volume, Risk Mismatch).")
    print("* Node C (Investigator) 💭: Detecting anomalies...")
    
    # ACT
    trace.append("⚡ **Act**: Applying heuristic rules to provider data.")
    
    data = state['provider_data'].iloc[0]
    anomalies = []
    
    # Create SHAP lookup for context
    shap_dict = {item['name']: item['value'] for item in state.get('shap_values', [])}
    
    # Rule 1: High Cost
    cost = data.get('cost_per_service', 0)
    if cost > 200:
        impact = shap_dict.get('cost_per_service', 0)
        if impact > 0:
            anomalies.append(f"Extremely high cost per service (${cost:.2f}) - <b>Risk Driver</b>")
        else:
            anomalies.append(f"High cost per service (${cost:.2f}), but considered benign by model")
        
    # Rule 2: High Volume
    vol = data.get('services_per_bene', 0)
    if vol > 10:
        impact = shap_dict.get('services_per_bene', 0)
        if impact > 0:
            anomalies.append(f"Unusually high services per patient ({vol:.1f}) - <b>Risk Driver</b>")
        else:
            # If it lowers risk, it might be typical for this high-volume specialty
            anomalies.append(f"High services per patient ({vol:.1f}), but consistent with low-risk profile")
        
    # Rule 3: Risk Mismatch
    if state['risk_score'] > 0.8 and data.get('total_services', 0) < 50:
        anomalies.append("High risk score despite low service volume (Suspicious Ratio)")
        
    # OBSERVE
    if anomalies:
        trace.append(f"👀 **Observe**: Detected {len(anomalies)} contextual anomalies.")
    else:
        trace.append("👀 **Observe**: No specific rule-based anomalies detected.")
    
    # Investigator Finding (Detailed with rich HTML)
    if anomalies:
        anomalies_html = "<ul class='space-y-2 mt-2'>\n"
        for anomaly in anomalies:
            # Check if it's a risk driver or benign
            if "Risk Driver" in anomaly or "HIGH" in anomaly:
                icon = "🚨"
                color_class = "text-red-700 font-semibold"
            elif "MEDIUM" in anomaly or "Suspicious" in anomaly:
                icon = "⚠️"
                color_class = "text-yellow-700 font-semibold"
            else:
                icon = "ℹ️"
                color_class = "text-blue-700"
            
            anomalies_html += f"<li class='text-sm {color_class}'>{icon} {anomaly}</li>\n"
        anomalies_html += "</ul>"
        summary_msg = f"<span class='text-red-600 font-bold'>⚠️ {len(anomalies)} anomal{'y' if len(anomalies) == 1 else 'ies'} detected</span>"
        findings_section = f"""
        <div class="bg-orange-50/40 p-3 rounded-lg">
            <h3 class="text-sm font-bold text-slate-700 mb-2">📋 Detailed Findings</h3>
            {anomalies_html}
        </div>
        """
    else:
        anomalies_html = "<p class='text-sm text-green-700'>✅ No rule-based anomalies detected. Billing patterns appear normal.</p>"
        summary_msg = "<span class='text-green-600 font-bold'>✓ No anomalies detected</span>"
        findings_section = f"""
        <div class="bg-green-50/40 p-3 rounded-lg">
            <h3 class="text-sm font-bold text-slate-700 mb-2">📋 Detailed Findings</h3>
            {anomalies_html}
        </div>
        """
        
    investigator_finding_text = f"""
    <div class="space-y-2">
        <div class="bg-purple-50/40 p-3 rounded-lg">
            <h3 class="text-sm font-bold text-slate-700 mb-2">🔍 Anomaly Detection Results</h3>
            <p class="text-sm"><b>Summary:</b> {summary_msg}</p>
        </div>
        
        {findings_section}
    </div>
    """

    
    # REFLECT
    trace.append("🤔 **Reflect**: Findings ready. Evaluating next steps...")
    
    # Decision Logic for Trace
    risk = state['risk_score']
    if risk > 0.5 or anomalies:
        trace.append("⚡ **Act**: Risk is significant or anomalies found. Proceeding to Network Analysis.")
    else:
        trace.append("⚡ **Act**: Risk is low and no anomalies. Skipping Network Analysis to optimize resources.")
        
    return {
        "anomalies": anomalies,
        "investigator_finding": investigator_finding_text,
        "trace": trace
    }

def generate_report_node(state: FraudAnalysisState):
    """
    Node 4: Generates the final narrative using Gemini.
    Role: Reporter (Final Synthesis)
    """
    trace = state['trace']
    
    # THINK
    trace.append("💭 **Think**: Synthesizing all findings into a final executive summary.")
    print("* Node D (Reporter) 💭: Synthesizing report...")
    
    assets = state['ml_assets']
    
    # ACT
    trace.append("⚡ **Act**: Prompting Gemini with risk, network, and anomaly data.")
    
    # Calculate peer count safely
    nodes = state.get('graph_data', {}).get('elements', {}).get('nodes', [])
    peer_count = max(0, len(nodes) - 1)
    
    # Construct Prompt
    prompt = f"""
    You are an expert Fraud Investigator. Write a final executive summary for this healthcare provider.
    
    **Provider NPI:** {state['npi']}
    **Risk Score:** {state['risk_score']:.4f} ({state['risk_level']})
    
    **Key Anomalies Detected:**
    {json.dumps(state.get('anomalies', []), indent=2)}
    
    **Top Risk Factors (SHAP):**
    {json.dumps(state['shap_values'][:5], indent=2)}
    
    **Network Analysis:**
    Found {peer_count} similar peers with matching billing patterns.
    
    **Instructions:**
    - Output ONLY valid HTML.
    - DO NOT use markdown code blocks (like ```html).
    - DO NOT include the <html> or <body> tags, just the content.
    - Use <h3> for section headers.
    - Use <ul> and <li> for lists.
    - Use <b> for emphasis.
    - Structure:
        1. <h3>Executive Verdict</h3>: Clear statement of risk.
        2. <h3>Key Findings</h3>: Bullet points of why the score is high/low.
        3. <h3>Network Intelligence</h3>: Mention peer similarity.
        4. <h3>Recommended Actions</h3>: Concrete next steps.
    - Make it professional, concise, and visually appealing.
    """
    
    # Call Gemini (using the existing helper if available, or direct call)
    # We'll use the 'analyst' agent's helper since it's already configured
    try:
        report = assets['analyst']._call_llm(prompt)
        
        # Check for API errors returned as text
        if "Error:" in report or "429" in report or "404" in report or "Rate limit" in report:
            trace.append(f"❌ **Error**: Report generation failed due to API error.")
            # Format error message as user-friendly HTML
            error_html = f"""
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
                <h3 class="text-yellow-800 font-bold">⚠️ Report Generation Unavailable</h3>
                <p class="text-yellow-700 mt-2">{report}</p>
                <p class="text-yellow-600 text-sm mt-2"><b>What this means:</b> The AI report service is temporarily unavailable due to high demand. However, the fraud analysis was completed successfully.</p>
                <p class="text-yellow-600 text-sm mt-1"><b>What to do:</b> You can still view the Risk Analysis, Network Analysis, and AI Supervisor recommendation above. Try refreshing the analysis in a few minutes for the full executive summary.</p>
            </div>
            """
            report = error_html
        else:
            # Cleanup if LLM still adds markdown
            report = report.replace("```html", "").replace("```", "").strip()
            # OBSERVE
            trace.append("👀 **Observe**: Generated executive summary successfully.")
            
    except Exception as e:
        error_html = f"""
        <div class="bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <h3 class="text-red-800 font-bold">❌ Report Generation Error</h3>
            <p class="text-red-700 mt-2">An unexpected error occurred while generating the report.</p>
            <p class="text-red-600 text-sm mt-2"><b>Error:</b> {str(e)}</p>
        </div>
        """
        report = error_html
        trace.append(f"❌ **Error**: Unexpected error during report generation: {e}")

        
    # REFLECT
    trace.append("🤔 **Reflect**: Analysis complete. Returning final results.")
        
    return {"final_report": report, "trace": trace}

def route_to_network(state: FraudAnalysisState):
    """Conditional Edge Logic"""
    risk = state['risk_score']
    anomalies = state.get('anomalies', [])
    
    if risk > 0.5 or len(anomalies) > 0:
        return "network_analysis"
    return "report_gen"

# --- Build Graph ---

def build_fraud_graph():
    workflow = StateGraph(FraudAnalysisState)
    
    workflow.add_node("risk_calc", calculate_risk_node)
    workflow.add_node("anomaly_detection", detect_anomalies_node)
    workflow.add_node("network_analysis", analyze_network_node)
    workflow.add_node("report_gen", generate_report_node)
    
    workflow.set_entry_point("risk_calc")
    
    # New Flow: Risk -> Anomaly -> (Conditional) -> Network -> Report
    workflow.add_edge("risk_calc", "anomaly_detection")
    
    workflow.add_conditional_edges(
        "anomaly_detection",
        route_to_network,
        {
            "network_analysis": "network_analysis",
            "report_gen": "report_gen"
        }
    )
    
    workflow.add_edge("network_analysis", "report_gen")
    workflow.add_edge("report_gen", END)
    
    return workflow.compile()
