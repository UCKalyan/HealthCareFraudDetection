
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import sqlite3
import os
from src.routers.dashboard import router
from src.database import get_db_connection

# Mock dependencies
mock_ml_assets = {
    'monitor': MagicMock(),
    'investigation_count': 5,
    'final_feature_columns': ['cost_per_service', 'services_per_bene', 'risk_score'],
    'scaler': MagicMock()
}

mock_ml_assets['monitor'].get_stats.return_value = {
    "providers_monitored": 100,
    "high_risk_alerts": 10,
    "avg_fraud_score": 0.5
}

# Create a test app with the router
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)

# Override dependency
def override_get_ml_assets():
    return mock_ml_assets

from src.dependencies import get_ml_assets
app.dependency_overrides[get_ml_assets] = override_get_ml_assets

client = TestClient(app)

# Setup Test Database
TEST_DB = "test_providers.db"

# Helper for manual setup
def manual_setup_db():
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS providers")
    cursor.execute("""
        CREATE TABLE providers (
            provider_id INTEGER PRIMARY KEY,
            Prscrbr_First_Name TEXT,
            Prscrbr_Last_Org_Name TEXT,
            specialty TEXT,
            cost_per_service REAL,
            services_per_bene REAL,
            risk_score REAL
        )
    """)
    cursor.execute("""
        INSERT INTO providers VALUES 
        (1234567890, 'John', 'Doe', 'Cardiology', 100.0, 5.0, 0.85),
        (9876543210, 'Jane', 'Smith', 'Dermatology', 50.0, 2.0, 0.15)
    """)
    conn.commit()
    conn.close()

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    manual_setup_db()
    
    # Patch the DB path in src.database
    with patch("src.database.DB_PATH", TEST_DB):
        yield
        
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_dashboard_stats():
    # This endpoint uses the monitor agent, which is mocked
    response = client.get("/dashboard_stats")
    assert response.status_code == 200
    data = response.json()
    assert data['providers_monitored'] == 100

def test_providers_list():
    # This endpoint uses the database
    with patch("src.database.DB_PATH", TEST_DB):
        response = client.get("/providers")
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) == 2
        assert data['data'][0]['npi'] == 1234567890
        assert data['data'][0]['risk_score'] == 0.85
        assert data['data'][0]['risk_status'] == "High"

def test_providers_search():
    with patch("src.database.DB_PATH", TEST_DB):
        response = client.get("/providers?search=Jane")
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) == 1
        assert data['data'][0]['name'] == "Jane Smith"

if __name__ == "__main__":
    # Manually run if pytest not available
    try:
        # Manual setup
        manual_setup_db()
        
        # We need to patch manually for the main execution
        with patch("src.database.DB_PATH", TEST_DB):
            test_dashboard_stats()
            print("test_dashboard_stats passed")
            
            test_providers_list()
            print("test_providers_list passed")
            
            test_providers_search()
            print("test_providers_search passed")
        
        # Manual cleanup
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
