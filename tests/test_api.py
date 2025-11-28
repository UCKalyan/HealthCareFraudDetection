import pytest
from unittest.mock import patch, MagicMock
from api_server import app, ml_assets

# Mock the load_assets function to avoid loading heavy models
@pytest.fixture(autouse=True)
def mock_load_assets():
    with patch('api_server.load_assets') as mock:
        # Populate ml_assets with dummy objects
        ml_assets['config'] = {'llm': {'api_key': 'test_key'}}
        ml_assets['feature_store'] = MagicMock()
        ml_assets['fraud_model'] = MagicMock()
        ml_assets['scaler'] = MagicMock()
        ml_assets['explainer'] = MagicMock()
        ml_assets['kmeans_model'] = MagicMock()
        ml_assets['investigator'] = MagicMock()
        ml_assets['analyst'] = MagicMock()
        ml_assets['reporter'] = MagicMock()
        ml_assets['monitor'] = MagicMock()
        
        # Mock specific agent methods
        ml_assets['analyst'].run.return_value = {
            "risk_level": "Low",
            "final_score": 0.1,
            "base_value": 0.1,
            "top_factor": "None",
            "shap_data": [],
            "analysis_text": "Test Analysis",
            "features": {}
        }
        
        yield mock

def test_read_root(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/login"

def test_analyze_provider(client):
    # Mock the graph workflow execution
    with patch('api_server.fraud_graph.invoke') as mock_invoke:
        mock_invoke.return_value = {
            "risk_score": 0.85,
            "risk_level": "High",
            "shap_values": [],
            "graph_data": {},
            "anomalies": ["Anomaly 1"],
            "final_report": "<h3>Executive Verdict</h3><p>High Risk</p>",
            "investigator_finding": "Found anomalies",
            "analyst_finding": "High risk score",
            "trace": ["Start", "End"]
        }
        
        response = client.post("/analyze_provider", json={"npi": 1234567890})
        assert response.status_code == 200
        data = response.json()
        # API returns camelCase keys
        assert data["finalScore"] == 0.85
        assert "High Risk" in data["aiNarrative"]
