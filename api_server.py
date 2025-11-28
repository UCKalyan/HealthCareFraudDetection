import os
# Set TF Legacy Keras flag BEFORE any other imports to ensure it applies
os.environ["TF_USE_LEGACY_KERAS"] = "1"
import secrets
import sqlite3
import logging
import time
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Import Dependencies and Routers
from src.dependencies import lifespan
from src.routers import investigation, dashboard, search

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
    return response

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Sanitize error details to handle bytes
    errors = []
    for error in exc.errors():
        new_error = error.copy()
        if 'input' in new_error and isinstance(new_error['input'], bytes):
            new_error['input'] = new_error['input'].decode('utf-8', errors='replace')
        errors.append(new_error)
        
    logger.error(f"Validation Error: {errors}")
    body = await request.body()
    logger.error(f"Request Body: {body}")
    
    return JSONResponse(
        status_code=422,
        content={"detail": errors, "body": body.decode('utf-8') if body else ""},
    )

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include Routers
app.include_router(investigation.router)
app.include_router(dashboard.router)
app.include_router(search.router)

# --- Authentication & Session Management ---
SESSION_SECRET = secrets.token_hex(32)
sessions = {}  # session_id -> {username, role}
USERS = {
    "admin": {"password": "fraud2025", "role": "admin"},
    "investigator": {"password": "inv123", "role": "investigator"},
    "supervisor": {"password": "sup123", "role": "supervisor"}
}

def get_session_user(request: Request):
    """Get user info from session cookie"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Render login page"""
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    if username in USERS and USERS[username]["password"] == password:
        session_id = secrets.token_hex(16)
        sessions[session_id] = {"username": username, "role": USERS[username]["role"]}
        
        response = RedirectResponse(url="/dashboard", status_code=303)
        # Redirect supervisors to their dashboard
        if USERS[username]["role"] == "supervisor":
             response = RedirectResponse(url="/supervisor/dashboard", status_code=303)
             
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    return RedirectResponse(url="/login?error=Invalid+credentials", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    """Handle logout"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_id")
    return response

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to login or dashboard based on session"""
    user = get_session_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Render main dashboard (protected)"""
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": user['username'], "user": user})

# --- Feedback & Case Management System ---
DB_PATH = "data/feedback.db"
CASES_DB_PATH = "data/cases.db"

def init_db():
    """Initialize SQLite database for feedback and cases."""
    os.makedirs("data", exist_ok=True)
    
    # Feedback DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            npi TEXT NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

    # Cases DB
    conn = sqlite3.connect(CASES_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            npi TEXT NOT NULL,
            provider_name TEXT,
            status TEXT DEFAULT 'PENDING', -- PENDING, REVIEWED
            submitted_by TEXT,
            decision TEXT, -- STOP, HOLD, REVIEW, RELEASE
            notes TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class FeedbackRequest(BaseModel):
    npi: str
    action: str
    notes: str = None

@app.post("/feedback")
async def submit_feedback(request: Request, feedback: FeedbackRequest):
    """Submit human feedback for RL training."""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO feedback (npi, username, action, notes) VALUES (?, ?, ?, ?)",
            (feedback.npi, user, feedback.action, feedback.notes)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Case Management Endpoints ---

class CaseSubmission(BaseModel):
    npi: str
    provider_name: str
    notes: str = None

@app.post("/cases/submit")
async def submit_case(request: Request, case: CaseSubmission):
    """Submit a case to the supervisor."""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        conn = sqlite3.connect(CASES_DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO cases (npi, provider_name, submitted_by, notes) VALUES (?, ?, ?, ?)",
            (case.npi, case.provider_name, user['username'], case.notes)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Case submitted to supervisor"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/supervisor/dashboard", response_class=HTMLResponse)
async def supervisor_dashboard(request: Request):
    """Render supervisor dashboard."""
    user = get_session_user(request)
    if not user or user['role'] != 'supervisor':
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("supervisor_dashboard.html", {"request": request, "username": user['username']})

@app.get("/api/cases/pending")
async def get_pending_cases(request: Request):
    """Get all pending cases."""
    user = get_session_user(request)
    if not user or user['role'] != 'supervisor':
        raise HTTPException(status_code=403, detail="Forbidden")
    
    conn = sqlite3.connect(CASES_DB_PATH)
    conn.row_factory = sqlite3.Row
    cases = conn.execute("SELECT * FROM cases WHERE status = 'PENDING' ORDER BY timestamp DESC").fetchall()
    conn.close()
    return [dict(ix) for ix in cases]

class CaseDecision(BaseModel):
    case_id: int
    decision: str
    notes: str

from src.utils.notifications import send_decision_email

@app.post("/api/cases/decide")
async def submit_decision(request: Request, decision: CaseDecision):
    """Submit a decision for a case."""
    user = get_session_user(request)
    if not user or user['role'] != 'supervisor':
        raise HTTPException(status_code=403, detail="Forbidden")
        
    try:
        conn = sqlite3.connect(CASES_DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get case details
        case = c.execute("SELECT * FROM cases WHERE id = ?", (decision.case_id,)).fetchone()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
            
        # Update case
        c.execute(
            "UPDATE cases SET status = 'REVIEWED', decision = ?, notes = ? WHERE id = ?",
            (decision.decision, decision.notes, decision.case_id)
        )
        conn.commit()
        conn.close()
        
        # Send Email
        case_details = dict(case)
        case_details['notes'] = decision.notes
        send_decision_email("payments@example.com", decision.decision, case_details)
        
        return {"status": "success", "message": "Decision recorded and email sent"}
    except Exception as e:
        logger.error(f"Error submitting decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))
