import json
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import TEMPLATES_DIR
from app.database import get_db
from app.models.user import User
from app.models.recommendation import RecommendationHistory
from app.models.schemas import PartyPlannerInput
from app.services.auth_service import get_current_user_optional
from app.services.gemini_service import gemini_service

router = APIRouter(tags=["Party Budget Planner"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render Party Budget Planner input form."""
    return templates.TemplateResponse(
        request=request,
        name="party_planner.html",
        context={"current_user": current_user}
    )


@router.post("/generate-party")
async def generate_party(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    total_budget: Optional[float] = Form(None),
    guest_count: Optional[int] = Form(None),
    event_type: Optional[str] = Form("Birthday Party"),
    venue_type: Optional[str] = Form("Home / Apartment"),
    food_preference: Optional[str] = Form("Buffet / Catering"),
    include_entertainment: Optional[bool] = Form(True),
    additional_notes: Optional[str] = Form("")
):
    """
    Process party budget and attendee details, invoke Gemini AI,
    save recommendation history, and render recommendations page.
    """
    is_api = request.headers.get("content-type") == "application/json"

    if is_api:
        body = await request.json()
        input_data = PartyPlannerInput(**body)
        total_budget = input_data.total_budget
        guest_count = input_data.guest_count
        event_type = input_data.event_type
        venue_type = input_data.venue_type
        food_preference = input_data.food_preference
        include_entertainment = input_data.include_entertainment
        additional_notes = input_data.additional_notes or ""
    else:
        if not total_budget or total_budget <= 0:
            return templates.TemplateResponse(
                request=request,
                name="party_planner.html",
                context={
                    "current_user": current_user,
                    "error": "Please provide a valid budget greater than ₹0."
                },
                status_code=400
            )
        if not guest_count or guest_count <= 0:
            return templates.TemplateResponse(
                request=request,
                name="party_planner.html",
                context={
                    "current_user": current_user,
                    "error": "Please specify at least 1 guest."
                },
                status_code=400
            )
        event_type = event_type or "Birthday Party"
        venue_type = venue_type or "Home / Apartment"
        food_preference = food_preference or "Buffet / Catering"
        additional_notes = additional_notes or ""

    # Call Gemini recommendation service
    result = gemini_service.generate_party_recommendations(
        total_budget=total_budget,
        guest_count=guest_count,
        event_type=event_type,
        venue_type=venue_type,
        food_preference=food_preference,
        include_entertainment=include_entertainment,
        additional_notes=additional_notes
    )

    # Persist in Database
    history_record = RecommendationHistory(
        user_id=current_user.id if current_user else None,
        category="party",
        title=result.get("title", f"{event_type} for {guest_count} Guests"),
        total_budget=total_budget,
        input_parameters=json.dumps({
            "guest_count": guest_count,
            "event_type": event_type,
            "venue_type": venue_type,
            "food_preference": food_preference,
            "include_entertainment": include_entertainment,
            "additional_notes": additional_notes
        }),
        ai_response_json=json.dumps(result)
    )
    db.add(history_record)
    db.commit()
    db.refresh(history_record)

    if is_api:
        result["history_id"] = history_record.id
        return result

    # Prepare chart data
    allocations = result.get("budget_allocations", [])
    chart_labels = [a["category_name"] for a in allocations]
    chart_data = [a["allocated_amount"] for a in allocations]

    return templates.TemplateResponse(
        request=request,
        name="party_recommendations.html",
        context={
            "current_user": current_user,
            "plan": result,
            "history_id": history_record.id,
            "chart_labels": json.dumps(chart_labels),
            "chart_data": json.dumps(chart_data)
        }
    )
