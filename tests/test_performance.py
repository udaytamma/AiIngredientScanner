"""Performance and timing tests for the Ingredient Safety Analyzer.

Tests operational performance boundaries:
- Response time limits for API endpoints
- Batch processing efficiency
- Concurrent request handling
- Memory usage patterns
"""

import time
import concurrent.futures
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from api import app
from graph import run_analysis
from state.schema import (
    AllergyRiskFlag,
    ExpertiseLevel,
    IngredientData,
    RiskLevel,
    SkinType,
)


def _create_mock_ingredient(name: str, safety_rating: int = 7) -> IngredientData:
    """Create mock ingredient for performance tests."""
    return IngredientData(
        name=name,
        purpose="Test purpose",
        safety_rating=safety_rating,
        concerns="No concerns",
        recommendation="Safe",
        allergy_risk_flag=AllergyRiskFlag.LOW,
        allergy_potential="Unknown",
        origin="Unknown",
        category="Unknown",
        regulatory_status="Approved",
        regulatory_bans="No",
        source="mock",
        confidence=0.9,
        aliases=[],
        risk_score=(10 - safety_rating) / 10,
        safety_notes="",
    )


class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoint_response_time(self, client):
        """Health endpoint should respond within 100ms."""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1, f"Health check took {elapsed:.3f}s, expected < 0.1s"

    def test_root_endpoint_response_time(self, client):
        """Root endpoint should respond within 100ms."""
        start = time.time()
        response = client.get("/")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1, f"Root endpoint took {elapsed:.3f}s, expected < 0.1s"

    def test_analyze_endpoint_with_mock_timing(self, client):
        """Analyze endpoint should complete within 5s with mocked LLM."""
        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Test",
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 8,
                    "summary": "Safe",
                    "assessments": [],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [],
                "error": None,
            }

            start = time.time()
            response = client.post(
                "/analyze",
                json={"ingredients": "Water, Glycerin"},
            )
            elapsed = time.time() - start

            assert response.status_code == 200
            assert elapsed < 5.0, f"Analyze took {elapsed:.3f}s, expected < 5s"


class TestBatchProcessing:
    """Tests for batch processing efficiency."""

    def test_batch_ingredient_research_timing(self):
        """Batch research should scale sub-linearly with ingredient count."""
        with patch("agents.research.lookup_ingredient") as mock_lookup, \
             patch("agents.research.grounded_ingredient_search") as mock_search:

            mock_lookup.return_value = None
            mock_search.side_effect = lambda n: _create_mock_ingredient(n)

            # Test with small batch
            small_ingredients = [f"ingredient_{i}" for i in range(3)]
            start_small = time.time()

            from agents.research import research_ingredients
            from state.schema import UserProfile, WorkflowState

            state_small = WorkflowState(
                session_id="perf-small",
                product_name="Test",
                raw_ingredients=small_ingredients,
                user_profile=UserProfile(
                    allergies=[],
                    skin_type=SkinType.NORMAL,
                    expertise=ExpertiseLevel.BEGINNER,
                ),
                ingredient_data=[],
                analysis_report=None,
                critic_feedback=None,
                retry_count=0,
                routing_history=[],
                stage_timings=None,
                error=None,
            )

            research_ingredients(state_small)
            elapsed_small = time.time() - start_small

            # Test with larger batch
            large_ingredients = [f"ingredient_{i}" for i in range(9)]
            start_large = time.time()

            state_large = WorkflowState(
                session_id="perf-large",
                product_name="Test",
                raw_ingredients=large_ingredients,
                user_profile=UserProfile(
                    allergies=[],
                    skin_type=SkinType.NORMAL,
                    expertise=ExpertiseLevel.BEGINNER,
                ),
                ingredient_data=[],
                analysis_report=None,
                critic_feedback=None,
                retry_count=0,
                routing_history=[],
                stage_timings=None,
                error=None,
            )

            research_ingredients(state_large)
            elapsed_large = time.time() - start_large

            # Large batch (3x ingredients) should take < 3x time due to batching
            # Allow some margin for overhead
            ratio = elapsed_large / elapsed_small if elapsed_small > 0 else 1
            assert ratio < 4.0, f"Batch scaling ratio {ratio:.2f} exceeds 4x"


class TestConcurrency:
    """Tests for concurrent request handling."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_concurrent_health_checks(self, client):
        """Multiple concurrent health checks should all succeed."""
        num_requests = 10

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(client.get, "/health")
                for _ in range(num_requests)
            ]

            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
        assert all(r.json()["status"] == "healthy" for r in results)

    def test_concurrent_analysis_requests(self, client):
        """Multiple concurrent analysis requests should complete."""
        with patch("api.run_analysis") as mock:
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Test",
                    "overall_risk": RiskLevel.LOW,
                    "average_safety_score": 8,
                    "summary": "Safe",
                    "assessments": [],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [],
                "error": None,
            }

            num_requests = 5

            def make_request(i):
                return client.post(
                    "/analyze",
                    json={
                        "product_name": f"Product {i}",
                        "ingredients": "Water, Glycerin",
                    },
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
                futures = [
                    executor.submit(make_request, i)
                    for i in range(num_requests)
                ]

                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # All requests should complete
            assert len(results) == num_requests
            assert all(r.status_code == 200 for r in results)


class TestMemoryEfficiency:
    """Tests for memory-efficient operations."""

    def test_large_ingredient_list_processing(self):
        """Processing large ingredient lists should not cause memory issues."""
        with patch("agents.research.lookup_ingredient") as mock_lookup, \
             patch("agents.research.grounded_ingredient_search") as mock_search, \
             patch("agents.analysis._generate_llm_analysis") as mock_llm, \
             patch("agents.critic._run_multi_gate_validation") as mock_critic:

            mock_lookup.return_value = None
            mock_search.side_effect = lambda n: _create_mock_ingredient(n)
            mock_llm.return_value = "Analysis complete"
            mock_critic.return_value = {
                "completeness_ok": True,
                "format_ok": True,
                "allergens_ok": True,
                "consistency_ok": True,
                "tone_ok": True,
                "failed_gates": [],
                "feedback": "Approved",
            }

            # Test with 50 ingredients (larger than typical)
            large_list = [f"ingredient_{i}" for i in range(50)]

            result = run_analysis(
                session_id="memory-test",
                product_name="Large Product",
                ingredients=large_list,
                allergies=[],
                skin_type="normal",
                expertise="beginner",
            )

            # Should complete without error
            assert result.get("error") is None
            assert len(result.get("ingredient_data", [])) == 50


class TestResponseSizeValidation:
    """Tests for response size limits."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_response_size_reasonable(self, client):
        """API response size should be reasonable for mobile consumption."""
        with patch("api.run_analysis") as mock:
            # Create response with multiple ingredients
            mock.return_value = {
                "analysis_report": {
                    "product_name": "Test Product with Long Name",
                    "overall_risk": RiskLevel.MEDIUM,
                    "average_safety_score": 6,
                    "summary": "This is a detailed summary " * 10,
                    "assessments": [
                        {
                            "name": f"ingredient_{i}",
                            "risk_level": RiskLevel.LOW,
                            "rationale": "Safe ingredient for use",
                            "is_allergen_match": False,
                            "alternatives": [],
                        }
                        for i in range(10)
                    ],
                    "allergen_warnings": [],
                    "expertise_tone": ExpertiseLevel.BEGINNER,
                },
                "ingredient_data": [
                    _create_mock_ingredient(f"ingredient_{i}")
                    for i in range(10)
                ],
                "error": None,
            }

            response = client.post(
                "/analyze",
                json={"ingredients": ", ".join(f"ingredient_{i}" for i in range(10))},
            )

            assert response.status_code == 200

            # Response should be under 100KB for mobile efficiency
            response_size = len(response.content)
            assert response_size < 100_000, f"Response size {response_size} bytes exceeds 100KB"
