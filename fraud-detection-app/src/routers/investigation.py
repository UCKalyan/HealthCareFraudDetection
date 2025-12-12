import logging
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from src.schemas import NpiRequest, ManualDataRequest
from src.dependencies import get_ml_assets
from src.agents.investigator import InvestigatorAgent
from src.agents.analyst import AnalystAgent
from src.agents.reporter import ReporterAgent
from src.agents.supervisor import SupervisorAgent
import asyncio
import json
import uuid
import requests
from datetime import datetime

# Configure Logging
logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cache for analysis results
analysis_cache = {}

async def _run_agentic_analysis(provider_id: str, provider_data: pd.Series, ml_assets: dict):
    """
    Orchestrates the multi-agent analysis flow.
    """
    try:
        # 1. Investigator Agent
        investigator = InvestigatorAgent(ml_assets['config'])
        investigation_report = investigator.run(provider_data)
        logger.info(f"Investigator Report: {investigation_report}")
        logger.info(f"************************* Investigator Report Completed *************************")
        # 2. Analyst Agent
        analyst = AnalystAgent(
            ml_assets['config'], 
            ml_assets['fraud_model'], 
            ml_assets['explainer'],
            ml_assets['scaler'],
            ml_assets['final_feature_columns']
        )
        analysis_results = analyst.run(provider_data)
        logger.info(f"Analyst Results: {analysis_results}")
        logger.info(f"************************* Analyst Results: Completed *************************")

        # 3. Supervisor Agent
        supervisor = SupervisorAgent(ml_assets['config'])
        provider_name = f"{provider_data.get('Prscrbr_First_Name', '')} {provider_data.get('Prscrbr_Last_Org_Name', '')}".strip()
        supervisor_recommendation = supervisor.run(analysis_results, provider_name, provider_id)
        logger.info(f"Supervisor Recommendation: {supervisor_recommendation}")
        logger.info(f"************************* Supervisor Recommendation Completed *************************")

        # 4. Reporter Agent
        reporter = ReporterAgent(ml_assets['config'])
        final_report = reporter.run(investigation_report, analysis_results, supervisor_recommendation, provider_id)
        logger.info("Reporter generated final report.")

        # Construct trace
        trace = [
            f"👀 **Observe**: Investigator analyzed {investigation_report['name']} ({investigation_report['specialty']})",
        ]
        if investigation_report['red_flags']:
            for flag in investigation_report['red_flags']:
                trace.append(f"⚠️ **Flag**: {flag}")
        else:
            trace.append("✅ **Check**: No immediate red flags found by Investigator.")
            
        trace.append(f"🤔 **Think**: Analyst calculating risk score and SHAP values...")
        trace.append(f"⚡ **Act**: Analyst determined risk level: {analysis_results['risk_level']} (Score: {analysis_results['final_score']:.4f})")
        trace.append(f"📝 **Report**: Reporter generating final narrative...")
        trace.append(f"👮 **Supervise**: Supervisor recommends: {supervisor_recommendation['recommendation']}")

        # Construct final response matching the UI's expected format
        result = {
            "npi": provider_id,
            "name": f"{provider_data.get('Prscrbr_First_Name', '')} {provider_data.get('Prscrbr_Last_Org_Name', '')}",
            "risk": analysis_results['risk_level'], 
            "finalScore": analysis_results['final_score'], 
            "baseValue": analysis_results['base_value'], 
            "topFactor": analysis_results['top_factor'], 
            "aiNarrative": final_report['final_narrative'], 
            "features": analysis_results['features'], 
            "shap": analysis_results['shap_data'],
            "investigatorFinding": investigation_report['summary'],
            "analystFinding": analysis_results['analysis_text'],
            "supervisorRecommendation": supervisor_recommendation['recommendation'],
            "trace": trace,
            "specialty": investigation_report['specialty']
        }
        
        # Cache the result
        analysis_cache[str(provider_id)] = result
        return result

    except Exception as e:
        logger.error(f"Error in agentic analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_provider")
async def analyze_provider(request: Request, ml_assets: dict = Depends(get_ml_assets)):
    """
    Analyzes an existing provider from the dataset by NPI.
    Accepts both JSON and Form data to be robust against client variations.
    """
    npi = None
    try:
        # Try parsing as JSON
        data = await request.json()
        npi = data.get("npi")
    except Exception:
        # Fallback to Form data
        try:
            form = await request.form()
            npi = form.get("npi")
        except Exception:
            pass
            
    if not npi:
        raise HTTPException(status_code=422, detail="Missing NPI in request body")
        
    try:
        npi = int(npi)
    except ValueError:
        raise HTTPException(status_code=422, detail="NPI must be a valid integer")

    logger.info(f"Received analysis request for NPI: {npi}")
    
    from src.database import get_db_connection
    
    try:
        # Check cache first to improve performance
        if str(npi) in analysis_cache:
            logger.info(f"Returning cached analysis for NPI: {npi}")
            return analysis_cache[str(npi)]
        
        with get_db_connection() as conn:
            # Fetch provider data
            provider_df = pd.read_sql_query("SELECT * FROM providers WHERE provider_id = ?", conn, params=(npi,))
            
        if provider_df.empty:
            raise HTTPException(status_code=404, detail="Provider NPI not found in dataset.")
        
        # Convert single row DataFrame to Series for compatibility with agents
        provider_data = provider_df.iloc[0]
        
        # Run the agentic workflow
        report = await _run_agentic_analysis(str(npi), provider_data, ml_assets)
        
        return report
        
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logger.error(f"Error in analyze_provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_new_provider")
async def analyze_new_provider(request: ManualDataRequest, ml_assets: dict = Depends(get_ml_assets)):
    """
    Analyzes a hypothetical provider based on manual input data.
    """
    logger.info(f"Received manual analysis request: {request}")
    
    try:
        # Construct a DataFrame row from the request
        input_data = {
            'total_service_cost': request.total_service_cost,
            'total_services': request.total_services,
            'total_benes_phys': request.total_benes_phys,
            'total_drug_cost': request.total_drug_cost,
            'total_scripts': request.total_scripts,
            'total_benes_presc': request.total_benes_presc,
            'specialty': request.specialty,
            # Add dummy values for other required columns if necessary, or ensure preprocessing handles missing
            'Prscrbr_First_Name': 'Manual',
            'Prscrbr_Last_Org_Name': 'Entry',
            'provider_id': 0000000000
        }
        
        # We need to ensure this data has all the columns expected by the feature engineering steps
        # For now, we'll assume the AnalystAgent can handle the raw input or we map it here.
        # Looking at AnalystAgent, it expects 'provider_data' to have the features.
        # We might need to run the same feature engineering (ratios, etc.) here.
        
        # Simplified Feature Engineering for Manual Data
        # (This duplicates logic from ingest.py/main.py - ideally should be a shared utility)
        input_data['cost_per_service'] = input_data['total_service_cost'] / input_data['total_services'] if input_data['total_services'] > 0 else 0
        input_data['services_per_bene'] = input_data['total_services'] / input_data['total_benes_phys'] if input_data['total_benes_phys'] > 0 else 0
        
        # Z-score normalization for 'spb_z_tanh' requires global stats
        # Note: ml_assets['spb_stats'] is a DataFrame loaded from JSON, so this remains valid.
        spb_mean = ml_assets['spb_stats'].loc[request.specialty, 'mean'] if request.specialty in ml_assets['spb_stats'].index else ml_assets['spb_stats']['mean'].mean()
        spb_std = ml_assets['spb_stats'].loc[request.specialty, 'std'] if request.specialty in ml_assets['spb_stats'].index else ml_assets['spb_stats']['std'].mean()
        
        z_score = (input_data['services_per_bene'] - spb_mean) / spb_std if spb_std > 0 else 0
        input_data['spb_z_tanh'] = np.tanh(0.5 * z_score) # Approximate tanh scaling
        
        # PageRank - assign median
        input_data['pagerank_centrality'] = ml_assets['median_pagerank']
        
        # Archetypes - assign 0 for now (or run K-Means prediction if we had the scaler for just these features)
        # For simplicity in this refactor, we set them to 0
        for i in range(5):
            input_data[f'provider_archetype_{i}'] = 0.0
            
        provider_data = pd.Series(input_data)
        
        # Run the agentic workflow
        report = await _run_agentic_analysis("MANUAL_ENTRY", provider_data, ml_assets)
        
        return report

    except Exception as e:
        logger.error(f"Error processing manual data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Streaming Implementation ---
import json
import asyncio
from fastapi.responses import StreamingResponse

async def stream_agentic_analysis(provider_id: str, provider_data: pd.Series, ml_assets: dict):
    """
    Generator that yields progress events and the final result.
    """
    try:
        # 1. Investigator Agent
        yield json.dumps({"type": "progress", "agent": "investigator", "status": "working"}) + "\n"
        investigator = InvestigatorAgent(ml_assets['config'])
        investigation_report = investigator.run(provider_data)
        logger.info(f"Investigator Report: {investigation_report}")
        logger.info(f"************************* Investigator Report Completed *************************")
        yield json.dumps({"type": "progress", "agent": "investigator", "status": "done"}) + "\n"

        # 2. Analyst Agent
        yield json.dumps({"type": "progress", "agent": "analyst", "status": "working"}) + "\n"
        analyst = AnalystAgent(
            ml_assets['config'], 
            ml_assets['fraud_model'], 
            ml_assets['explainer'],
            ml_assets['scaler'],
            ml_assets['final_feature_columns']
        )
        analysis_results = analyst.run(provider_data)
        logger.info(f"Analyst Results: {analysis_results}")
        logger.info(f"************************* Analyst Results: Completed *************************")
        yield json.dumps({"type": "progress", "agent": "analyst", "status": "done"}) + "\n"

        # 3. Supervisor Agent
        yield json.dumps({"type": "progress", "agent": "supervisor", "status": "working"}) + "\n"
        supervisor = SupervisorAgent(ml_assets['config'])
        provider_name = f"{provider_data.get('Prscrbr_First_Name', '')} {provider_data.get('Prscrbr_Last_Org_Name', '')}".strip()
        supervisor_recommendation = supervisor.run(analysis_results, provider_name, provider_id)
        logger.info(f"Supervisor Recommendation: {supervisor_recommendation}")
        logger.info(f"************************* Supervisor Recommendation Completed *************************")
        yield json.dumps({"type": "progress", "agent": "supervisor", "status": "done"}) + "\n"

        # 4. Reporter Agent
        yield json.dumps({"type": "progress", "agent": "reporter", "status": "working"}) + "\n"
        reporter = ReporterAgent(ml_assets['config'])
        final_report = reporter.run(investigation_report, analysis_results, supervisor_recommendation, provider_id)
        logger.info("Reporter generated final report.")
        yield json.dumps({"type": "progress", "agent": "reporter", "status": "done"}) + "\n"

        # Construct trace
        trace = [
            f"👀 **Observe**: Investigator analyzed {investigation_report['name']} ({investigation_report['specialty']})",
        ]
        if investigation_report['red_flags']:
            for flag in investigation_report['red_flags']:
                trace.append(f"⚠️ **Flag**: {flag}")
        else:
            trace.append("✅ **Check**: No immediate red flags found by Investigator.")
            
        trace.append(f"🤔 **Think**: Analyst calculating risk score and SHAP values...")
        final_score = analysis_results.get('final_score')
        score_str = f"{final_score:.4f}" if final_score is not None else "N/A"
        trace.append(f"⚡ **Act**: Analyst determined risk level: {analysis_results['risk_level']} (Score: {score_str})")
        trace.append(f"📝 **Report**: Reporter generating final narrative...")
        trace.append(f"👮 **Supervise**: Supervisor recommends: {supervisor_recommendation['recommendation']}")

        # Construct final response
        result = {
            "npi": provider_id,
            "name": f"{provider_data.get('Prscrbr_First_Name', '')} {provider_data.get('Prscrbr_Last_Org_Name', '')}",
            "risk": analysis_results['risk_level'], 
            "finalScore": analysis_results['final_score'], 
            "baseValue": analysis_results['base_value'], 
            "topFactor": analysis_results['top_factor'], 
            "aiNarrative": final_report['final_narrative'], 
            "features": analysis_results['features'], 
            "shap": analysis_results['shap_data'],
            "investigatorFinding": investigation_report['summary'],
            "analystFinding": analysis_results['analysis_text'],
            "supervisorRecommendation": supervisor_recommendation['recommendation'],
            "trace": trace,
            "specialty": investigation_report['specialty']
        }
        
        # Cache the result
        analysis_cache[str(provider_id)] = result
        
        # Yield final result
        yield json.dumps({"type": "result", "data": result}) + "\n"

    except Exception as e:
        logger.error(f"Error in streaming analysis: {e}")
        yield json.dumps({"type": "error", "detail": str(e)}) + "\n"

@router.post("/analyze_provider_stream")
async def analyze_provider_stream(request: Request, ml_assets: dict = Depends(get_ml_assets)):
    """
    Streams analysis progress and results.
    """
    npi = None
    try:
        data = await request.json()
        npi = data.get("npi")
    except Exception:
        pass
            
    if not npi:
        raise HTTPException(status_code=422, detail="Missing NPI")
        
    try:
        npi = int(npi)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid NPI")

    from src.database import get_db_connection
    
    # Check cache first (optional: if cached, we could just return result immediately, 
    # but for consistency with UI stream reader, we might want to simulate or just yield result)
    if str(npi) in analysis_cache:
        async def yield_cached():
            yield json.dumps({"type": "result", "data": analysis_cache[str(npi)]}) + "\n"
        return StreamingResponse(yield_cached(), media_type="application/x-ndjson")

    with get_db_connection() as conn:
        provider_df = pd.read_sql_query("SELECT * FROM providers WHERE provider_id = ?", conn, params=(npi,))
        
    if provider_df.empty:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider_data = provider_df.iloc[0]
    
    return StreamingResponse(stream_agentic_analysis(str(npi), provider_data, ml_assets), media_type="application/x-ndjson")

from fastapi.responses import FileResponse
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

@router.get("/generate_report_pdf/{npi}")
async def generate_report_pdf(npi: int, ml_assets: dict = Depends(get_ml_assets)):
    """
    Generates a PDF report for the given NPI.
    """
    from src.database import get_db_connection
    
    try:
        # 1. Fetch Data
        # Check cache first
        if str(npi) in analysis_cache:
            logger.info(f"Using cached analysis for NPI: {npi}")
            report_data = analysis_cache[str(npi)]
        else:
            logger.info(f"Cache miss for NPI: {npi}, re-running analysis...")
            with get_db_connection() as conn:
                provider_df = pd.read_sql_query("SELECT * FROM providers WHERE provider_id = ?", conn, params=(npi,))
                
            if provider_df.empty:
                raise HTTPException(status_code=404, detail="Provider not found")
                
            provider_data = provider_df.iloc[0]
            report_data = await _run_agentic_analysis(str(npi), provider_data, ml_assets)
        
        # 2. Generate PDF
        pdf_path = f"reports/report_{npi}.pdf"
        os.makedirs("reports", exist_ok=True)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        import re
        
        def clean_text_for_pdf(text):
            if not text: return ""
            # Remove HTML tags but keep content
            text = re.sub(r'<[^>]+>', '', text)
            # Replace markdown bold with reportlab bold
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            # Replace newlines with <br/>
            text = text.replace('\n', '<br/>')
            return text

        # Title
        story.append(Paragraph(f"Fraud Investigation Report: {report_data['name']}", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Metadata
        story.append(Paragraph(f"<b>NPI:</b> {npi}", styles['Normal']))
        story.append(Paragraph(f"<b>Specialty:</b> {report_data['specialty']}", styles['Normal']))
        story.append(Paragraph(f"<b>Risk Level:</b> {report_data['risk']}", styles['Normal']))
        story.append(Paragraph(f"<b>Fraud Score:</b> {report_data['finalScore']:.4f}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Executive Summary
        story.append(Paragraph("<b>Executive Summary</b>", styles['Heading2']))
        story.append(Paragraph(clean_text_for_pdf(report_data['aiNarrative']), styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Findings
        story.append(Paragraph("<b>Key Findings</b>", styles['Heading2']))
        story.append(Paragraph(f"<b>Investigator:</b> {clean_text_for_pdf(report_data['investigatorFinding'])}", styles['Normal']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Analyst:</b> {clean_text_for_pdf(report_data['analystFinding'])}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Top Risk Factors (SHAP)
        story.append(Paragraph("<b>Top Risk Factors</b>", styles['Heading2']))
        shap_data = [['Feature', 'Impact']]
        for item in report_data['shap'][:5]:
            shap_data.append([item['name'], f"{item['value']:.4f}"])
            
        t = Table(shap_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        
        doc.build(story)
        
        return FileResponse(pdf_path, filename=f"FraudReport_{npi}.pdf", media_type='application/pdf')

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# MCP Integration - Payment Hold Endpoint
# ==============================================================================

@router.post("/api/submit_payment_hold")
async def submit_payment_hold(request: Request):
    """
    Submits fraud response - either payment hold OR recovery initiation.
    System automatically determines which based on payment status from Finance API.
    
    Flow:
    1. Try to hold payment (works for NEW/PENDING payments)
    2. If payment is PROCESSED, automatically initiate recovery instead
    3. Return appropriate response to UI
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid JSON")
    
    npi = data.get("npi")
    fraud_score = data.get("fraud_score", 0.0)
    reasoning = data.get("reasoning", "High fraud risk detected")
    transaction_id = data.get("transaction_id")  # Optional, for specific transactions
    auto_triggered = data.get("auto_triggered", False)
    
    if not npi:
        raise HTTPException(status_code=422, detail="Missing NPI")
    
    logger.info(f"🚨 Fraud response request for NPI {npi}, transaction {transaction_id}")
    
    try:
        import requests
        
        # Step 1: Try to hold payment (works for NEW/PENDING payments)
        hold_response = requests.post(
            "http://localhost:8001/api/process_payment_hold",
            json={
                "npi": npi,
                "transaction_id": transaction_id,
                "action": "HOLD",
                "fraud_score": fraud_score,
                "confidence": 0.95,
                "reasoning": reasoning,
                "source": "fraud_detection",
                "analyst": "fraud_analyst",
                "auto_triggered": auto_triggered
            },
            timeout=5
        )
        
        result = hold_response.json()
        
        # Step 2: Check if payment requires recovery instead
        if not result.get("success") and result.get("requires_recovery"):
            logger.info(f"💰 Payment already processed, initiating recovery for NPI {npi}")
            
            # Get fraud evidence from analysis cache
            fraud_evidence = {
                "fraud_score": fraud_score,
                "reasoning": reasoning,
                "shap_values": analysis_cache.get(str(npi), {}).get("shap", [])[:10],  # Top 10
                "investigation": analysis_cache.get(str(npi), {}).get("investigatorFinding", ""),
                "analysis": analysis_cache.get(str(npi), {}).get("analystFinding", ""),
                "supervisor_recommendation": analysis_cache.get(str(npi), {}).get("supervisorRecommendation", "")
            }
            
            # Initiate recovery workflow
            recovery_response = requests.post(
                "http://localhost:8001/api/initiate_recovery",
                json={
                    "transaction_id": result.get("transaction_id") or transaction_id,
                    "npi": npi,
                    "fraud_score": fraud_score,
                    "fraud_evidence": fraud_evidence,
                    "initiator": "fraud_detection_agent" if auto_triggered else "analyst_manual",
                    "initiated_by": "system"
                },
                timeout=5
            )
            
            if recovery_response.status_code == 200:
                recovery_result = recovery_response.json()
                logger.info(f"✅ Recovery initiated: {recovery_result.get('recovery_id')}")
                
                return {
                    "success": True,
                    "action": "RECOVERY_INITIATED",
                    "message": f"Payment already processed. Recovery process initiated.",
                    "recovery_id": recovery_result.get("recovery_id"),
                    "approval_level": recovery_result.get("approval_level"),
                    "amount": recovery_result.get("message", ""),
                    "payment_category": result.get("payment_category")
                }
            else:
                logger.error(f"Recovery initiation failed: {recovery_response.text}")
                return {
                    "success": False,
                    "message": f"Failed to initiate recovery: {recovery_response.text}"
                }
        
        # Step 3: Payment hold was successful (or other success case)
        if result.get("success"):
            logger.info(f"✅ Payment hold successful for NPI {npi}")
            return {
                "success": True,
                "action": "PAYMENT_HELD",
                "message": f"Payment hold submitted for NPI {npi}",
                "transaction_id": result.get("transaction_id"),
                "finance_response": result
            }
        else:
            # Some other error
            return {
                "success": False,
                "message": result.get("message", "Unknown error from Finance system")
            }
            
    except requests.exceptions.Timeout:
        logger.error("Finance system timeout")
        return {
            "success": False,
            "message": "Finance system timeout - please try again"
        }
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Finance system")
        return {
            "success": False,
            "message": "Cannot connect to Finance system - ensure it's running on port 8001"
        }
    except Exception as e:
        logger.error(f"Error in fraud response: {e}")
        return {
            "success": False,
            "message": str(e)
        }
