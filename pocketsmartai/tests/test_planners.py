import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_public_pages_render():
    routes = [
        "/",
        "/login",
        "/register",
        "/testimonials",
        "/home-planner",
        "/party-planner",
        "/jewelry-planner",
        "/startup"
    ]
    for r in routes:
        response = client.get(r)
        assert response.status_code in [200, 307, 302], f"Failed on route {r}: {response.status_code}"


def test_home_planner_generation_json():
    payload = {
        "total_budget": 50000.0,
        "room_type": "Living Room",
        "style_preference": "Modern & Minimalist",
        "items_needed": ["Sofa", "Coffee Table", "Ceiling Lights"]
    }
    response = client.post("/generate-home", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "home"
    assert data["total_budget"] == 50000.0
    assert len(data["budget_allocations"]) > 0
    assert len(data["recommendations"]) > 0
    # Check platform URL enrichment
    for item in data["recommendations"]:
        assert "suggested_platform" in item
        assert "platform_url" in item
        assert item["platform_url"].startswith("http")


def test_party_planner_generation_json():
    payload = {
        "total_budget": 30000.0,
        "guest_count": 25,
        "event_type": "Birthday Party",
        "venue_type": "Home / Apartment",
        "food_preference": "Buffet / Multi-Course",
        "include_entertainment": True
    }
    response = client.post("/generate-party", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "party"
    assert data["total_budget"] == 30000.0
    assert len(data["recommendations"]) > 0


def test_jewelry_planner_generation_json():
    payload = {
        "total_budget": 20000.0,
        "occasion": "Wedding / Reception",
        "style_preference": "Traditional Temple",
        "metal_preference": "Yellow Gold Plated",
        "jewelry_types": ["Necklace", "Earrings"]
    }
    response = client.post("/generate-jewelry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "jewelry"
    assert data["total_budget"] == 20000.0
    assert len(data["recommendations"]) > 0


def test_session_info_and_startup():
    info_resp = client.get("/session-info")
    assert info_resp.status_code == 200
    info_data = info_resp.json()
    assert "authenticated" in info_data
    assert "gemini_status" in info_data

    startup_resp = client.get("/startup")
    assert startup_resp.status_code == 200
    startup_data = startup_resp.json()
    assert startup_data["status"] == "healthy"
