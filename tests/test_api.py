"""Tests for the REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from api import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns OK status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data

    def test_health_endpoint(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAnalyzeEndpoint:
    """Tests for the /analyze endpoint."""

    def test_analyze_missing_ingredients(self, client):
        """Test that empty ingredients returns error."""
        response = client.post(
            "/analyze",
            json={
                "product_name": "Test Product",
                "ingredients": "",
                "allergies": [],
                "skin_type": "normal",
                "expertise": "beginner",
            },
        )
        assert response.status_code == 400
        assert "No ingredients provided" in response.json()["detail"]

    def test_analyze_request_format(self, client):
        """Test that request with valid format is accepted (may fail on LLM call)."""
        response = client.post(
            "/analyze",
            json={
                "product_name": "Test Cream",
                "ingredients": "Water, Glycerin",
                "allergies": ["Fragrance"],
                "skin_type": "sensitive",
                "expertise": "beginner",
            },
        )
        # Either success or 500 (if LLM unavailable), but not 400
        assert response.status_code in [200, 500]


class TestOCREndpoint:
    """Tests for the /ocr endpoint."""

    def test_ocr_invalid_base64(self, client):
        """Test that invalid base64 returns error gracefully."""
        response = client.post(
            "/ocr",
            json={"image": "not-valid-base64!!!"},
        )
        # Should return error response, not crash
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "error" in data

    def test_ocr_empty_image(self, client):
        """Test that empty image returns error."""
        response = client.post(
            "/ocr",
            json={"image": ""},
        )
        assert response.status_code == 200
        data = response.json()
        # Empty base64 will fail to decode
        assert data["success"] == False


class TestAPIModels:
    """Tests for API request/response models."""

    def test_analysis_request_defaults(self, client):
        """Test that default values are applied correctly."""
        # Missing optional fields should use defaults
        response = client.post(
            "/analyze",
            json={
                "ingredients": "Water, Glycerin, Sodium Lauryl Sulfate",
            },
        )
        # Request should be accepted (defaults applied)
        assert response.status_code in [200, 500]

    def test_skin_type_case_insensitive(self, client):
        """Test that skin type is case-insensitive."""
        response = client.post(
            "/analyze",
            json={
                "ingredients": "Water, Glycerin",
                "skin_type": "SENSITIVE",  # uppercase
            },
        )
        assert response.status_code in [200, 500]
