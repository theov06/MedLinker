"""Smoke tests for FastAPI endpoints."""

import os
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from medlinker_ai.api import app
from medlinker_ai.models import FacilityDocInput
from medlinker_ai.verify import verify_facility
from medlinker_ai.aggregate import aggregate_regions


@pytest.fixture(autouse=True)
def force_offline():
    """Force offline mode for all tests."""
    os.environ["LLM_PROVIDER"] = "none"
    yield
    if "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def setup_test_data():
    """Setup test data files."""
    # Create output directory
    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Create sample facilities
    facilities = []
    for i in range(3):
        doc = FacilityDocInput(
            facility_id=f"TEST{i:03d}",
            facility_name=f"Test Hospital {i}",
            region="Test Region",
            country="Test Country",
            source_id=f"test_source_{i}",
            source_type="dataset_row",
            source_text="Provides emergency care, surgery, and maternity services. "
                        "Equipment includes ultrasound and X-ray. "
                        "Staff: doctors, nurses, midwives."
        )
        analysis = verify_facility(doc)
        facilities.append(analysis)
    
    # Write facilities.jsonl
    facilities_file = output_dir / "facilities.jsonl"
    with open(facilities_file, 'w') as f:
        for facility in facilities:
            f.write(json.dumps(facility.model_dump()) + "\n")
    
    # Aggregate regions
    summaries = aggregate_regions(facilities)
    
    # Write regions.json
    regions_file = output_dir / "regions.json"
    with open(regions_file, 'w') as f:
        json.dump([s.model_dump() for s in summaries], f, indent=2)
    
    yield
    
    # Cleanup (optional - keep files for debugging)
    # facilities_file.unlink(missing_ok=True)
    # regions_file.unlink(missing_ok=True)


def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert data["name"] == "MedLinker AI"
    assert "endpoints" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"


def test_get_facilities(client, setup_test_data):
    """Test GET /facilities returns facility list."""
    response = client.get("/facilities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    
    # Check first facility structure
    facility = data[0]
    assert "facility_id" in facility
    assert "extracted_capabilities" in facility
    assert "status" in facility
    assert "citations" in facility
    assert "trace_id" in facility


def test_get_facilities_not_found(client):
    """Test GET /facilities returns 404 if data not available."""
    # Temporarily rename file
    facilities_file = Path("./outputs/facilities.jsonl")
    backup_file = Path("./outputs/facilities.jsonl.bak")
    
    if facilities_file.exists():
        facilities_file.rename(backup_file)
    
    try:
        response = client.get("/facilities")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        # Restore file
        if backup_file.exists():
            backup_file.rename(facilities_file)


def test_get_regions(client, setup_test_data):
    """Test GET /regions returns region list."""
    response = client.get("/regions")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check first region structure
    region = data[0]
    assert "country" in region
    assert "region" in region
    assert "desert_score" in region
    assert "missing_critical" in region
    assert "coverage" in region
    assert "trace_id" in region


def test_get_regions_not_found(client):
    """Test GET /regions returns 404 if data not available."""
    # Temporarily rename file
    regions_file = Path("./outputs/regions.json")
    backup_file = Path("./outputs/regions.json.bak")
    
    if regions_file.exists():
        regions_file.rename(backup_file)
    
    try:
        response = client.get("/regions")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        # Restore file
        if backup_file.exists():
            backup_file.rename(regions_file)


def test_post_ask(client, setup_test_data):
    """Test POST /ask returns answer with citations."""
    response = client.post(
        "/ask",
        json={"question": "Which regions are medical deserts?"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert "trace_id" in data
    
    # Check answer is non-empty
    assert len(data["answer"]) > 0
    
    # Check citations structure
    assert isinstance(data["citations"], list)
    if len(data["citations"]) > 0:
        citation = data["citations"][0]
        assert "snippet" in citation
        assert "field" in citation


def test_post_ask_empty_question(client, setup_test_data):
    """Test POST /ask rejects empty question."""
    response = client.post(
        "/ask",
        json={"question": ""}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_post_ask_whitespace_question(client, setup_test_data):
    """Test POST /ask rejects whitespace-only question."""
    response = client.post(
        "/ask",
        json={"question": "   "}
    )
    assert response.status_code == 400


def test_get_trace(client, setup_test_data):
    """Test GET /trace/{trace_id} returns trace details."""
    # First, get a trace_id from facilities
    response = client.get("/facilities")
    assert response.status_code == 200
    
    facilities = response.json()
    trace_id = facilities[0]["trace_id"]
    
    # Get trace
    response = client.get(f"/trace/{trace_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "trace_id" in data
    assert "spans" in data
    assert data["trace_id"] == trace_id
    
    # Check spans structure
    assert isinstance(data["spans"], list)
    assert len(data["spans"]) > 0
    
    span = data["spans"][0]
    assert "step_name" in span
    assert "inputs_summary" in span
    assert "outputs_summary" in span
    assert "evidence_refs" in span
    assert "timestamp" in span


def test_get_trace_not_found(client):
    """Test GET /trace/{trace_id} returns 404 for invalid trace."""
    response = client.get("/trace/invalid-trace-id-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_cors_enabled(client):
    """Test CORS headers are present."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


def test_facilities_response_schema(client, setup_test_data):
    """Test facilities response matches expected schema."""
    response = client.get("/facilities")
    assert response.status_code == 200
    
    facilities = response.json()
    for facility in facilities:
        # Required fields
        assert "facility_id" in facility
        assert "extracted_capabilities" in facility
        assert "status" in facility
        assert "reasons" in facility
        assert "confidence" in facility
        assert "citations" in facility
        assert "trace_id" in facility
        
        # Status values
        assert facility["status"] in ["VERIFIED", "INCOMPLETE", "SUSPICIOUS"]
        
        # Confidence values
        assert facility["confidence"] in ["LOW", "MEDIUM", "HIGH"]


def test_regions_response_schema(client, setup_test_data):
    """Test regions response matches expected schema."""
    response = client.get("/regions")
    assert response.status_code == 200
    
    regions = response.json()
    for region in regions:
        # Required fields
        assert "country" in region
        assert "region" in region
        assert "total_facilities" in region
        assert "facilities_analyzed" in region
        assert "desert_score" in region
        assert "missing_critical" in region
        assert "coverage" in region
        assert "trace_id" in region
        
        # Desert score range
        assert 0 <= region["desert_score"] <= 100


def test_ask_response_schema(client, setup_test_data):
    """Test ask response matches expected schema."""
    response = client.post(
        "/ask",
        json={"question": "Show suspicious facilities"}
    )
    assert response.status_code == 200
    
    data = response.json()
    
    # Required fields
    assert "answer" in data
    assert "citations" in data
    assert "trace_id" in data
    
    # Types
    assert isinstance(data["answer"], str)
    assert isinstance(data["citations"], list)
    assert isinstance(data["trace_id"], str)
    
    # Citation structure
    for citation in data["citations"]:
        assert "snippet" in citation
        assert "field" in citation
        assert "source_id" in citation
        
        # Snippet length constraint
        assert len(citation["snippet"]) <= 500
