"""API tests for the UPFFM backend."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "UPFFM API is running"}


def test_espn_league_unauthorized():
    """Test ESPN league endpoint without authentication."""
    response = client.get("/api/espn/league/12345")
    assert response.status_code == 401
    assert "ESPN authentication cookies required" in response.json()["detail"]


def test_yahoo_auth_url():
    """Test Yahoo OAuth URL endpoint."""
    response = client.get("/api/yahoo/auth/url")
    assert response.status_code == 200
    assert "auth_url" in response.json()
    assert "message" in response.json()


def test_projections_endpoint():
    """Test player projections endpoint."""
    response = client.get("/api/projections/players")
    assert response.status_code == 200
    assert len(response.json()) > 0
    player = response.json()[0]
    assert "player_id" in player
    assert "name" in player
    assert "position" in player
    assert "projected_points" in player 