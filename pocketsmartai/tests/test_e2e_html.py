import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home_planner_html_form_flow():
    # Submit form data as if submitted from web browser
    form_data = {
        "total_budget": "65000",
        "room_type": "Living Room",
        "style_preference": "Scandinavian Light Wood",
        "items_needed": ["Sofa", "Coffee Table", "Ceiling Lights"],
        "additional_notes": "Prefer light grey and oak tones"
    }
    response = client.post("/generate-home", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html_content = response.text
    assert "Living Room" in html_content
    assert "homeBudgetChart" in html_content
    assert "IKEA" in html_content or "Amazon" in html_content


def test_party_planner_html_form_flow():
    form_data = {
        "total_budget": "45000",
        "guest_count": "30",
        "event_type": "Birthday Party",
        "venue_type": "Home / Apartment",
        "food_preference": "Bulk Party Platters via Swiggy / Zomato",
        "include_entertainment": "true",
        "additional_notes": "Finger foods and mocktails"
    }
    response = client.post("/generate-party", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html_content = response.text
    assert "Birthday Party" in html_content
    assert "partyBudgetChart" in html_content


def test_jewelry_planner_html_multipart_with_image():
    # Create a small valid test PNG image in-memory
    from PIL import Image
    img_byte_arr = io.BytesIO()
    test_img = Image.new('RGB', (100, 100), color='crimson')
    test_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    files = {
        "outfit_image": ("outfit_test.png", img_byte_arr, "image/png")
    }
    form_data = {
        "total_budget": "25000",
        "occasion": "Wedding / Reception",
        "style_preference": "Traditional Temple / Kundan",
        "metal_preference": "Yellow Gold Plated",
        "jewelry_types": ["Necklace / Choker", "Earrings / Jhumkas"],
        "additional_notes": "Crimson silk lehenga"
    }
    response = client.post("/generate-jewelry", data=form_data, files=files)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html_content = response.text
    assert "jewelryBudgetChart" in html_content
    assert "outfit_" in html_content or "Multimodal" in html_content


def test_testimonial_submission_flow():
    data = {
        "user_name": "Test Reviewer",
        "role_or_occasion": "Wedding Planner",
        "comment": "Exceptional experience using PocketSmart AI for our event budget!",
        "rating": "5"
    }
    response = client.post("/testimonials", data=data, follow_redirects=False)
    assert response.status_code == 302
    assert "/testimonials?msg=success" in response.headers["location"]
