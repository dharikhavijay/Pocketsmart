import json
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import TEMPLATES_DIR, UPLOADS_DIR
from app.database import get_db
from app.models.user import User
from app.models.recommendation import RecommendationHistory
from app.models.schemas import JewelryPlannerInput
from app.services.auth_service import get_current_user_optional
from app.services.gemini_service import gemini_service

router = APIRouter(tags=["Jewelry Budget Planner"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render Jewelry Budget Planner page."""
    return templates.TemplateResponse(
        request=request,
        name="jewelry_planner.html",
        context={"current_user": current_user}
    )


@router.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    total_budget: Optional[float] = Form(None),
    occasion: Optional[str] = Form("Wedding"),
    style_preference: Optional[str] = Form("Contemporary"),
    metal_preference: Optional[str] = Form("Gold / Brass"),
    jewelry_types: Optional[List[str]] = Form(None),
    additional_notes: Optional[str] = Form(""),
    outfit_image: Optional[UploadFile] = File(None)
):
    """
    Process jewelry budget, style preferences, and optional outfit image upload.
    Executes multimodal Gemini AI analysis and returns recommendations.
    """
    is_api = request.headers.get("content-type", "").startswith("application/json")

    saved_relative_image_path = None
    saved_absolute_image_path = None

    if is_api:
        body = await request.json()
        input_data = JewelryPlannerInput(**body)
        total_budget = input_data.total_budget
        occasion = input_data.occasion
        style_preference = input_data.style_preference
        metal_preference = input_data.metal_preference
        jewelry_types = input_data.jewelry_types
        additional_notes = input_data.additional_notes or ""
    else:
        if not total_budget or total_budget <= 0:
            return templates.TemplateResponse(
                request=request,
                name="jewelry_planner.html",
                context={
                    "current_user": current_user,
                    "error": "Please specify a valid jewelry budget greater than ₹0."
                },
                status_code=400
            )

        occasion = occasion or "Wedding"
        style_preference = style_preference or "Contemporary"
        metal_preference = metal_preference or "Gold / Brass"
        jewelry_types = jewelry_types if jewelry_types else []
        additional_notes = additional_notes or ""

        # Process uploaded outfit image
        if outfit_image and outfit_image.filename:
            file_ext = Path(outfit_image.filename).suffix.lower()
            if file_ext in [".jpg", ".jpeg", ".png", ".webp"]:
                unique_name = f"outfit_{uuid.uuid4().hex[:10]}{file_ext}"
                dest_path = UPLOADS_DIR / unique_name
                try:
                    contents = await outfit_image.read()
                    with open(dest_path, "wb") as f:
                        f.write(contents)
                    saved_relative_image_path = f"/static/uploads/{unique_name}"
                    saved_absolute_image_path = str(dest_path)
                except Exception as e:
                    # Proceed without image if write failed
                    pass

    # Call Gemini service with multimodal support
    result = gemini_service.generate_jewelry_recommendations(
        total_budget=total_budget,
        occasion=occasion,
        style_preference=style_preference,
        metal_preference=metal_preference,
        jewelry_types=jewelry_types,
        image_path=saved_absolute_image_path,
        additional_notes=additional_notes
    )

    if saved_relative_image_path:
        result["uploaded_image_url"] = saved_relative_image_path

    # Persist in Database
    history_record = RecommendationHistory(
        user_id=current_user.id if current_user else None,
        category="jewelry",
        title=result.get("title", f"{occasion} Jewelry ({style_preference})"),
        total_budget=total_budget,
        image_path=saved_relative_image_path,
        input_parameters=json.dumps({
            "occasion": occasion,
            "style_preference": style_preference,
            "metal_preference": metal_preference,
            "jewelry_types": jewelry_types,
            "additional_notes": additional_notes,
            "has_image": bool(saved_relative_image_path)
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
        name="jewelry_recommendations.html",
        context={
            "current_user": current_user,
            "plan": result,
            "history_id": history_record.id,
            "uploaded_image": saved_relative_image_path,
            "chart_labels": json.dumps(chart_labels),
            "chart_data": json.dumps(chart_data)
        }
    )
