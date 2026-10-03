import pytest
from app.services.platform_linker import PlatformLinker
from app.services.gemini_service import gemini_service


def test_platform_linker_urls():
    amazon_url = PlatformLinker.get_search_url("Amazon", "Sofa Living Room")
    assert "amazon.in/s?k=Sofa+Living+Room" in amazon_url

    ikea_url = PlatformLinker.get_search_url("IKEA", "Coffee Table")
    assert "ikea.com/in/en/search/?q=Coffee+Table" in ikea_url

    swiggy_url = PlatformLinker.get_search_url("Swiggy", "Pizza Party")
    assert "swiggy.com/search?query=Pizza+Party" in swiggy_url

    zomato_url = PlatformLinker.get_search_url("Zomato", "Biryani Platter")
    assert "zomato.com/search?q=Biryani+Platter" in zomato_url


def test_platform_meta_enrichment():
    item = {
        "item_name": "L-shaped Sectional Sofa",
        "category": "Furniture",
        "estimated_price": 24000.0,
        "suggested_platform": "IKEA"
    }
    enriched = PlatformLinker.enrich_recommendation(item)
    assert "platform_url" in enriched
    assert "platform_meta" in enriched
    assert enriched["platform_meta"]["name"] == "IKEA"
    assert enriched["platform_meta"]["color"] == "#0058A3"


def test_gemini_service_home_budget_integrity():
    budget = 40000.0
    res = gemini_service.generate_home_recommendations(
        total_budget=budget,
        room_type="Master Bedroom",
        items_needed=["Bed frame", "Bedside lamp", "Curtains"]
    )
    assert res["total_budget"] == budget
    assert res["estimated_total_cost"] <= budget
    assert res["remaining_balance"] >= 0
    assert len(res["recommendations"]) >= 3


def test_gemini_service_party_budget_integrity():
    budget = 20000.0
    res = gemini_service.generate_party_recommendations(
        total_budget=budget,
        guest_count=20,
        event_type="Housewarming"
    )
    assert res["total_budget"] == budget
    assert res["estimated_total_cost"] <= budget
    assert len(res["recommendations"]) >= 3


def test_gemini_service_jewelry_budget_integrity():
    budget = 18000.0
    res = gemini_service.generate_jewelry_recommendations(
        total_budget=budget,
        occasion="Festival",
        style_preference="Contemporary",
        metal_preference="Gold / Brass"
    )
    assert res["total_budget"] == budget
    assert res["estimated_total_cost"] <= budget
    assert len(res["recommendations"]) >= 3
    assert "outfit_analysis" in res
