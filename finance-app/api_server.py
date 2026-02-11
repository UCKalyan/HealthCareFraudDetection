"""
Finance Application - API Server

FastAPI backend for Finance application UI with session-based authentication
and RESTful endpoints for payment processing, provider queries, and analytics.

Author: Healthcare Fraud Detection Team
Date: 2024-11-30
"""

import os
import secrets
import sqlite3
import logging
import time
import json
import threading
import yaml
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background threads
    thread = threading.Thread(target=refresh_dashboard_stats_background, daemon=True)
    thread.start()
    logger.info("🚀 Background stats refresh thread started")
    
    # Start daily summary scheduler
    try:
        from src.utils.daily_summary import get_scheduler
        scheduler = get_scheduler(str(DB_PATH))
        scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start daily summary scheduler: {e}")
    
    yield
    # Shutdown: Clean up resources
    try:
        from src.utils.daily_summary import get_scheduler
        scheduler = get_scheduler()
        if scheduler:
            scheduler.stop()
    except:
        pass
    logger.info("🛑 Server shutting down")

# Initialize FastAPI with lifespan
app = FastAPI(title="Finance Application", lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load environment variables
load_dotenv()

# Database path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

def load_config():
    """Load configuration from YAML file"""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    return {}

# Load initial config
app_config = load_config()
db_config_path = app_config.get("database", {}).get("finance_db_path", "../shared-data/databases/finance.db")
DB_PATH = (BASE_DIR / db_config_path).resolve()

if not DB_PATH.exists():
    logger.error(f"Database not found at {DB_PATH}")

# Auth Database path
AUTH_DB_PATH = (PROJECT_ROOT / "shared-data/databases/auth.db").resolve()

if not AUTH_DB_PATH.exists():
    logger.error(f"Auth Database not found at {AUTH_DB_PATH}")

# Session management
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))
SESSION_COOKIE_NAME = "hcfd_session"


# ==============================================================================
# Authentication & Session Management
# ==============================================================================

def get_session_user(request: Request):
    """Get user info from shared session DB"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None
        
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check session validity
        cursor.execute("""
            SELECT s.username, u.role 
            FROM sessions s
            JOIN users u ON s.username = u.username
            WHERE s.session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"username": row["username"], "role": row["role"]}
    except Exception as e:
        logger.error(f"Auth DB error: {e}")
        
    return None


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Render login page"""
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Handle login form submission against shared Auth DB"""
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verify user
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        
        if user:
            session_id = secrets.token_hex(32)
            
            # Create session
            cursor.execute("INSERT INTO sessions (session_id, username) VALUES (?, ?)", (session_id, username))
            conn.commit()
            conn.close()
            
            response = RedirectResponse(url="/dashboard", status_code=303)
            # Set shared cookie for SSO (Path=/)
            response.set_cookie(key=SESSION_COOKIE_NAME, value=session_id, httponly=True, path="/")
            return response
            
        conn.close()
    except Exception as e:
        logger.error(f"Login error: {e}")

    return RedirectResponse(url="/login?error=Invalid+credentials", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    """Handle logout"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        try:
            conn = sqlite3.connect(AUTH_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Logout error: {e}")
            
    response = RedirectResponse(url="/login")
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


# ==============================================================================
# Page Routes
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to login or dashboard"""
    user = get_session_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Render main dashboard"""
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@app.get("/payments", response_class=HTMLResponse)
async def payments_page(request: Request):
    """Render payment processing center"""
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("payments.html", {"request": request, "user": user})


@app.get("/providers", response_class=HTMLResponse)
async def providers_page(request: Request):
    """Render provider explorer"""
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("providers.html", {"request": request, "user": user})


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Render analytics page"""
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("analytics.html", {"request": request, "user": user})


@app.get("/audit", response_class=HTMLResponse)
async def audit_page(request: Request):
    """Render agent audit trail"""
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("audit.html", {"request": request, "user": user})


@app.get("/recovery", response_class=HTMLResponse)
async def recovery_page(request: Request):
    """Render payment recovery management"""
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("recovery.html", {"request": request, "user": user})


# ==============================================================================
# API Endpoints - Dashboard Stats
# ==============================================================================

import json
import threading

# ... (existing imports)

# Config path definition moved to top of file

def refresh_dashboard_stats_background():
    """Background thread to refresh dashboard stats based on configured interval"""
    logger.info("🚀 Background stats refresh thread started")
    
    while True:
        try:
            # Load config to get interval
            config = load_config()
            interval = config.get("dashboard", {}).get("refresh_interval_seconds", 1800)
            
            refresh_dashboard_stats()
            
            # Sleep for the configured interval
            time.sleep(interval)
            
        except Exception as e:
            logger.error(f"Error in background stats refresh: {e}")
            time.sleep(60) # Fallback sleep on error

def refresh_dashboard_stats():
    """Calculate stats and update the summary table"""
    start_time = time.time()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total providers
        cursor.execute("SELECT COUNT(*) FROM provider_financial_profiles")
        total_providers = cursor.fetchone()[0]
        
        # Total payments
        cursor.execute("SELECT SUM(total_payment_all) FROM provider_financial_profiles")
        total_payments = cursor.fetchone()[0] or 0
        
        # High-risk providers
        cursor.execute("SELECT COUNT(*) FROM provider_financial_profiles WHERE is_high_cost_provider = 1 OR is_opioid_prescriber = 1")
        high_risk_providers = cursor.fetchone()[0]
        
        # Recent transactions
        today_start = datetime.now().strftime('%Y-%m-%dT00:00:00')
        cursor.execute("SELECT COUNT(*) FROM payment_transactions WHERE created_at >= ?", (today_start,))
        transactions_today = cursor.fetchone()[0]
        
        # Agent decisions today
        cursor.execute("SELECT payment_status, COUNT(*) FROM payment_transactions WHERE created_at >= ? GROUP BY payment_status", (today_start,))
        decisions = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average confidence
        cursor.execute("SELECT AVG(agent_confidence) FROM payment_transactions WHERE created_at >= ? AND agent_confidence IS NOT NULL", (today_start,))
        avg_confidence = cursor.fetchone()[0] or 0
        
        # Calculate autonomous rate
        autonomous_rate = (decisions.get('APPROVE', 0) / max(transactions_today, 1)) * 100
        
        # Update summary table
        cursor.execute("""
            UPDATE dashboard_statistics SET
                total_providers = ?,
                total_payments = ?,
                high_risk_providers = ?,
                transactions_today = ?,
                avg_confidence = ?,
                autonomous_rate = ?,
                decisions_json = ?,
                last_updated = datetime('now')
            WHERE id = 1
        """, (
            total_providers,
            total_payments,
            high_risk_providers,
            transactions_today,
            avg_confidence,
            autonomous_rate,
            json.dumps(decisions)
        ))
        
        conn.commit()
        conn.close()
        
        elapsed = time.time() - start_time
        # logger.info(f"🔄 Dashboard stats refreshed in {elapsed:.2f}s") # Commented out to reduce noise
        
    except Exception as e:
        logger.error(f"Error refreshing dashboard stats: {e}")

# Removed deprecated startup event
# @app.on_event("startup") logic moved to lifespan

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """Get dashboard KPI statistics from cache"""
    start_time = time.time()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM dashboard_statistics WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {}
            
        elapsed = time.time() - start_time
        # logger.info(f"⚡ Dashboard stats served from cache in {elapsed:.4f}s")
        
        return {
            "total_providers": row['total_providers'],
            "total_payments": row['total_payments'],
            "high_risk_providers": row['high_risk_providers'],
            "transactions_today": row['transactions_today'],
            "decisions_today": json.loads(row['decisions_json']),
            "average_confidence": row['avg_confidence'],
            "autonomous_rate": row['autonomous_rate']
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# API Endpoints - Payment Processing
# ==============================================================================

@app.get("/api/payments/recent")
def get_recent_payments(page: int = 1, limit: int = 50):
    """Get recent payment transactions with pagination"""
    start_time = time.time()
    offset = (page - 1) * limit
    logger.info(f"💳 Fetching recent payments (Page {page}, Limit {limit})...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get Total Count
        cursor.execute("SELECT COUNT(*) FROM payment_transactions")
        total_records = cursor.fetchone()[0]
        
        # Get Data
        cursor.execute('''
            SELECT t.*, p.provider_name, p.provider_state
            FROM payment_transactions t
            LEFT JOIN provider_financial_profiles p ON t.npi = p.npi
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Fetched {len(payments)} payments in {elapsed:.2f}s")
        
        return {
            "payments": payments,
            "total": total_records,
            "page": page,
            "limit": limit,
            "total_pages": (total_records + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/payments/search")
@app.get("/api/payments/search")
def search_payments(
    npi: Optional[int] = None,
    status: Optional[str] = None, 
    transaction_id: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    """Search payment transactions by NPI, status, or transaction ID with pagination"""
    offset = (page - 1) * limit
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Base Query Construction
        base_query = '''
            FROM payment_transactions t
            LEFT JOIN provider_financial_profiles p ON t.npi = p.npi
            WHERE 1=1
        '''
        params = []
        
        if npi:
            base_query += " AND t.npi = ?"
            params.append(npi)
        
        if status:
            base_query += " AND t.payment_status = ?"
            params.append(status)
        
        if transaction_id:
            base_query += " AND t.transaction_id LIKE ?"
            params.append(f"%{transaction_id}%")
            
        # Get Total Count
        count_query = f"SELECT COUNT(*) {base_query}"
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()[0]
        
        # Get Data
        data_query = f"SELECT t.*, p.provider_name, p.provider_state {base_query} ORDER BY t.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(data_query, params)
        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "payments": payments, 
            "total": total_records,
            "page": page,
            "limit": limit,
            "total_pages": (total_records + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Error searching payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ==============================================================================
# API Endpoints - Provider Explorer
# ==============================================================================

@app.get("/api/providers/search")
@app.get("/api/providers/search")
def search_providers(query: str = "", limit: int = 100):
    """Search providers by NPI, name, or state"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT npi, provider_name, provider_state, provider_type,
                   total_payment_all, is_high_cost_provider, is_opioid_prescriber,
                   monthly_payment_estimate
            FROM provider_financial_profiles
            WHERE CAST(npi AS TEXT) LIKE ? 
               OR provider_name LIKE ?
               OR provider_state LIKE ?
            ORDER BY total_payment_all DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        providers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"providers": providers, "count": len(providers)}
        
    except Exception as e:
        logger.error(f"Error searching providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/providers/{npi}", response_class=HTMLResponse)
@app.get("/providers/{npi}", response_class=HTMLResponse)
def provider_details_page(request: Request, npi: int):
    """Render provider details page"""
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login")
        
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get provider profile
        cursor.execute('SELECT * FROM provider_financial_profiles WHERE npi = ?', (npi,))
        provider = cursor.fetchone()
        
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
            
        # Get transaction history
        cursor.execute('''
            SELECT * FROM payment_transactions 
            WHERE npi = ? 
            ORDER BY created_at DESC 
            LIMIT 100
        ''', (npi,))
        transactions = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return templates.TemplateResponse(
            "provider_details.html", 
            {
                "request": request, 
                "user": user,
                "provider": dict(provider),
                "transactions": transactions
            }
        )
    except Exception as e:
        logger.error(f"Error rendering provider details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers/{npi}")
@app.get("/api/providers/{npi}")
def get_provider_details(npi: int):
    """Get complete provider financial profile"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Get provider profile
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM provider_financial_profiles WHERE npi = ?', (npi,))
        provider = cursor.fetchone()
        
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # Get transaction history
        cursor.execute('''
            SELECT * FROM payment_transactions 
            WHERE npi = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        ''', (npi,))
        transactions = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "provider": dict(provider),
            "transactions": transactions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching provider details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# API Endpoints - Analytics
# ==============================================================================

@app.get("/api/analytics/high-risk")
def get_high_risk_providers(limit: int = 100):
    """Get high-risk providers"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT npi, provider_name, provider_state, total_payment_all,
                   is_high_cost_provider, is_opioid_prescriber,
                   opioid_prescriber_rate, partd_opioid_cost
            FROM provider_financial_profiles
            WHERE is_high_cost_provider = 1 OR is_opioid_prescriber = 1
            ORDER BY total_payment_all DESC
            LIMIT ?
        ''', (limit,))
        
        providers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"providers": providers}
        
    except Exception as e:
        logger.error(f"Error fetching high-risk providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# API Endpoints - Agent Audit
# ==============================================================================

@app.get("/api/audit/decisions")
@app.get("/api/audit/decisions")
def get_agent_decisions(limit: int = 100):
    """Get agent decision logs"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM agent_decision_logs
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        decisions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"decisions": decisions}
        
    except Exception as e:
        logger.error(f"Error fetching agent decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# MCP Integration - Payment Hold Endpoint
# ==============================================================================

@app.post("/api/process_payment_hold")
@app.post("/api/process_payment_hold")
def process_payment_hold(data: dict):
    """
    Receives payment hold request from Fraud Detection via MCP.
    NOW WITH PAYMENT LIFECYCLE AWARENESS:
    - If payment is PROCESSED: Returns error indicating recovery is needed
    - If payment is PENDING/NEW: Processes hold as before
    """
    npi = data.get("npi")
    transaction_id = data.get("transaction_id")  # May be provided
    action = data.get("action")
    fraud_score = data.get("fraud_score", 0.0)
    confidence = data.get("confidence", 0.0)
    reasoning = data.get("reasoning", "")
    source = data.get("source", "unknown")
    analyst = data.get("analyst", "system")
    
    logger.info(f"📥 MCP Request from {source}: Hold payment for NPI {npi} by {analyst}")
    
    try:
        from src.services import PaymentClassifier
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # If transaction_id provided, check if it's already processed
        if transaction_id:
            cursor.execute("""
                SELECT payment_date, payment_status, payment_amount
                FROM payment_transactions
                WHERE transaction_id = ?
            """, (transaction_id,))
            result = cursor.fetchone()
            
            if result:
                payment_date_str, payment_status, payment_amount = result
                category = PaymentClassifier.classify_payment(payment_date_str, payment_status)
                
                if not PaymentClassifier.can_hold_payment(category):
                    conn.close()
                    logger.warning(f"❌ Cannot hold {payment_status} payment {transaction_id}")
                    return {
                        "success": False,
                        "error": "PAYMENT_ALREADY_PROCESSED",
                        "message": f"Payment already {payment_status}. Use recovery workflow instead.",
                        "requires_recovery": True,
                        "payment_category": category,
                        "transaction_id": transaction_id
                    }
        
        # Create a payment hold transaction
        if not transaction_id:
            transaction_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO payment_transactions 
            (transaction_id, npi, payment_amount, fraud_risk_score, 
             agent_decision, agent_confidence, agent_reasoning, 
             payment_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            transaction_id,
            npi,
            data.get('amount', 0.0),  # Use provided amount or default to 0
            fraud_score,
            "HOLD",
            confidence,
            f"[MCP from {source} by {analyst}] {reasoning}",
            "HELD"
        ))
        
        # Log the agent decision
        cursor.execute('''
            INSERT INTO agent_decision_logs
            (transaction_id, npi, agent_name, decision, confidence, reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            transaction_id,
            npi,
            f"MCP-{source}",
            "HOLD",
            confidence,
            f"[MCP] {reasoning}"
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Payment hold processed via MCP: Transaction {transaction_id}")
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "npi": npi,
            "decision": "HOLD",
            "message": f"Payment hold processed for NPI {npi}"
        }
        
    except Exception as e:
        logger.error(f"Error processing payment hold: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Recovery Workflow Endpoints
# ==============================================================================

@app.post("/api/initiate_recovery")
async def initiate_recovery(data: dict):
    """
    Initiates recovery process for processed payment flagged as fraudulent.
    Called from Fraud Detection when fraud is detected on historical processed payment.
    """
    transaction_id = data.get("transaction_id")
    npi = data.get("npi")
    fraud_score = data.get("fraud_score", 0.0)
    fraud_evidence = data.get("fraud_evidence", {})
    initiator = data.get("initiator", "fraud_detection_agent")
    initiated_by = data.get("initiated_by", "system")
    
    logger.info(f"📋 Recovery request for transaction {transaction_id}, NPI {npi}")
    
    try:
        from src.services import RecoveryService
        
        recovery_service = RecoveryService(str(DB_PATH))
        result = recovery_service.initiate_recovery(
            transaction_id=transaction_id,
            npi=npi,
            fraud_score=fraud_score,
            fraud_evidence=fraud_evidence,
            initiator=initiator,
            initiated_by=initiated_by
        )
        
        logger.info(f"✅ Recovery initiated: {result['recovery_id']}")
        
        # Handle case where recovery already exists
        if result.get("status") == "ALREADY_EXISTS":
             return {
                "success": True,
                "recovery_id": result["recovery_id"],
                "message": f"Recovery request already exists for transaction {transaction_id}",
                "approval_level": result.get("approval_level", "UNKNOWN"), # Safe get
                "npi": npi,
                "transaction_id": transaction_id
            }

        return {
            "success": True,
            "recovery_id": result["recovery_id"],
            "message": f"Recovery initiated for ${result.get('amount', 0.0):.2f}",
            "approval_level": result["approval_level"],
            "npi": npi,
            "transaction_id": transaction_id
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error initiating recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recovery/requests")
async def get_recovery_requests(request:Request, status: str = None):
    """Get all recovery requests with optional status filter"""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from src.services.recovery_service import RecoveryService
        recovery_service = RecoveryService(str(DB_PATH))
        requests_list = recovery_service.get_recovery_requests(status=status)
        return {"recovery_requests": requests_list}
    except Exception as e:
        logger.error(f"Error fetching recovery requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recovery/details/{recovery_id}")
async def get_recovery_details(request: Request, recovery_id: str):
    """Get detailed recovery workflow information including timeline and email status"""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from src.services.recovery_workflow import get_recovery_workflow_details
        details = get_recovery_workflow_details(str(DB_PATH), recovery_id)
        
        if 'error' in details:
            raise HTTPException(status_code=404, detail=details['error'])
        
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recovery details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recovery/{recovery_id}/approve")
async def approve_recovery(recovery_id: str, data: dict):
    """Approve recovery request"""
    
    approver = data.get("approver", "system")
    notes = data.get("notes", "")
    recovery_method = data.get("recovery_method", "RECOUPMENT")
    
    try:
        from src.services import RecoveryService
        
        recovery_service = RecoveryService(str(DB_PATH))
        result = recovery_service.approve_recovery(
            recovery_id=recovery_id,
            approver=approver,
            notes=notes,
            recovery_method=recovery_method
        )
        
        return {
            "success": True,
            "message": "Recovery approved",
            "recovery_id": result["recovery_id"],
            "recovery_method": result["recovery_method"]
        }
        
    except Exception as e:
        logger.error(f"Error approving recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recovery/{recovery_id}/reject")
async def reject_recovery(recovery_id: str, data: dict):
    """Reject recovery request"""
    
    rejector = data.get("rejector", "system")
    notes = data.get("notes", "")
    
    try:
        from src.services import RecoveryService
        
        recovery_service = RecoveryService(str(DB_PATH))
        result = recovery_service.reject_recovery(
            recovery_id=recovery_id,
            rejector=rejector,
            notes=notes
        )
        
        return {
            "success": True,
            "message": "Recovery rejected",
            "recovery_id": result["recovery_id"]
        }
        
    except Exception as e:
        logger.error(f"Error rejecting recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/provider/actions/{npi}")
async def get_provider_actions(npi: int):
    """Get all payment holds and recovery requests for a provider"""
    try:
        from src.services.provider_actions import get_provider_finance_actions
        actions = get_provider_finance_actions(str(DB_PATH), npi)
        return actions
    except Exception as e:
        logger.error(f"Error fetching provider actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
