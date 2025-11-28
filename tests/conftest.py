import pytest
from fastapi.testclient import TestClient
from api_server import app

@pytest.fixture
def client():
    """
    Pytest fixture to create a TestClient for the FastAPI app.
    """
    return TestClient(app)
