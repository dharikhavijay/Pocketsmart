import json
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import TEMPLATES_DIR
from app.database import get_db
from app.models.user import User
from app.models.recommendation import RecommendationHistory
from app.models.schemas import HomePlannerInput
from app.services.auth_service import get_current_user_optional
from app.services.gemini_service import gemini_service

router = APIRouter(tags=["Home Interior Planner"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render Home Interior Budget Planner input form."""
    return templates.TemplateResponse(
        request=request,
        name="home_planner.html",
        context={"current_user": current_user}
    )


@router.post("/generate-home")
async def generate_home(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    total_budget: Optional[float] = Form(None),
    room_type: Optional[str] = Form(None),
    style_preference: Optional[str] = Form("Modern & Minimalist"),
    items_needed: Optional[List[str]] = Form(None),
    additional_notes: Optional[str] = Form("")
):
    """
    Process home interior budget and room requirements, invoke Gemini AI,
    save recommendation history, and render recommendations page.
    """
    is_api = request.headers.get("content-type") == "application/json"

    if is_api:
        body = await request.json()
        input_data = HomePlannerInput(**body)
        total_budget = input_data.total_budget
        room_type = input_data.room_type
        style_preference = input_data.style_preference
        items_list = input_data.items_needed
        additional_notes = input_data.additional_notes or ""
    else:
        if not total_budget or total_budget <= 0:
            return templates.TemplateResponse(
                request=request,
                name="home_planner.html",
                context={
                    "current_user": current_user,
                    "error": "Please specify a valid budget greater than ₹0."
                },
                status_code=400
            )
        room_type = room_type or "Living Room"
        items_list = items_needed if items_needed else []
        additional_notes = additional_notes or ""

    # Generate recommendations using Gemini
    result = gemini_service.generate_home_recommendations(
        total_budget=total_budget,
        room_type=room_type,
        items_needed=items_list,
        style_preference=style_preference,
        additional_notes=additional_notes
    )

    # Persist in Database
    history_record = RecommendationHistory(
        user_id=current_user.id if current_user else None,
        category="home",
        title=result.get("title", f"{room_type} Interior Plan"),
        total_budget=total_budget,
        input_parameters=json.dumps({
            "room_type": room_type,
            "style_preference": style_preference,
            "items_needed": items_list,
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

    # Prepare chart data for Jinja2
    allocations = result.get("budget_allocations", [])
    chart_labels = [a["category_name"] for a in allocations]
    chart_data = [a["allocated_amount"] for a in allocations]

    return templates.TemplateResponse(
        request=request,
        name="home_recommendations.html",
        context={
            "current_user": current_user,
            "plan": result,
            "history_id": history_record.id,
            "chart_labels": json.dumps(chart_labels),
            "chart_data": json.dumps(chart_data)
        }
    )
