import json
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.recommendation import RecommendationHistory
from app.services.auth_service import get_current_user_optional, get_current_active_user
from app.services.gemini_service import gemini_service
from app.config import settings

router = APIRouter(tags=["API & Session"])


@router.get("/session-info")
@router.get("/api/session-info")
async def get_session_info(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Activity 2.4 / Milestone 3:
    Retrieves metadata about current user session, user ID, and login status.
    """
    if not current_user:
        return {
            "authenticated": False,
            "user_id": None,
            "username": None,
            "status": "guest",
            "gemini_status": "active" if gemini_service.is_configured else "fallback_demo_mode"
        }

    return {
        "authenticated": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "status": "active",
        "gemini_status": "active" if gemini_service.is_configured else "fallback_demo_mode"
    }


@router.get("/session-data")
@router.get("/api/session-data")
async def get_session_data(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Activity 2.4 / Milestone 3:
    Returns detailed session-specific data used for personalization and recommendation tracking.
    """
    if not current_user:
        return {
            "session_id": request.session.get("session_id", "guest") if hasattr(request, "session") else "guest",
            "recent_plans_count": 0,
            "saved_plans": []
        }

    user_plans = db.query(RecommendationHistory).filter(
        RecommendationHistory.user_id == current_user.id
    ).order_by(RecommendationHistory.created_at.desc()).limit(10).all()

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "recent_plans_count": len(user_plans),
        "saved_plans": [
            {
                "id": p.id,
                "category": p.category,
                "title": p.title,
                "total_budget": p.total_budget,
                "created_at": p.created_at.isoformat()
            }
            for p in user_plans
        ]
    }


@router.get("/recommendations-details")
@router.get("/api/recommendations-details")
async def get_recommendation_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Activity 3.2 / Milestone 3:
    Returns detailed AI-generated product recommendations based on user budget and category.
    """
    rec = db.query(RecommendationHistory).filter(RecommendationHistory.id == id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation record with ID {id} not found."
        )

    try:
        parsed_ai_response = json.loads(rec.ai_response_json)
    except Exception:
        parsed_ai_response = {}

    try:
        parsed_inputs = json.loads(rec.input_parameters)
    except Exception:
        parsed_inputs = {}

    return {
        "id": rec.id,
        "user_id": rec.user_id,
        "category": rec.category,
        "title": rec.title,
        "total_budget": rec.total_budget,
        "image_path": rec.image_path,
        "input_parameters": parsed_inputs,
        "recommendations_data": parsed_ai_response,
        "created_at": rec.created_at.isoformat()
    }


@router.get("/startup")
async def startup_check():
    """
    Activity 3.4 / Milestone 3:
    Initializes essential application services and loads configuration settings.
    """
    return {
        "app_name": settings.APP_NAME,
        "status": "healthy",
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_api_configured": bool(gemini_service.is_configured),
        "database": "sqlite_ready"
    }
