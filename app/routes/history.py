import json
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import TEMPLATES_DIR
from app.database import get_db
from app.models.user import User
from app.models.recommendation import RecommendationHistory, Testimonial
from app.services.auth_service import get_current_user_optional, get_current_active_user

router = APIRouter(tags=["History & Views"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Main Landing Page."""
    testimonials = db.query(Testimonial).order_by(Testimonial.created_at.desc()).limit(3).all()
    # If no testimonials in DB, provide default showcase items
    if not testimonials:
        default_testimonials = [
            Testimonial(
                user_name="Aarav Sharma",
                role_or_occasion="3BHK Home Interior in Bangalore",
                comment="PocketSmart AI saved me at least ₹45,000 on my living room furnishing. The IKEA and Amazon product links matched my minimalist theme perfectly!",
                rating=5
            ),
            Testimonial(
                user_name="Pooja & Rohit",
                role_or_occasion="Engagement Celebration for 60 Guests",
                comment="Allocating budget across Zomato bulk catering, OYO banquet hall, and Amazon decor was seamless. Zero financial surprises on our big day.",
                rating=5
            ),
            Testimonial(
                user_name="Meera Kapoor",
                role_or_occasion="Diwali Festive Jewelry Matching",
                comment="I uploaded my emerald green lehenga image, and Gemini suggested the exact antique gold choker and jhumkas to complement my neckline. Mindblowing!",
                rating=5
            )
        ]
        testimonials = default_testimonials

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "current_user": current_user,
            "testimonials": testimonials
        }
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """User Dashboard displaying activity stats, budget analytics, and recent plans."""
    user_queries = db.query(RecommendationHistory).filter(
        RecommendationHistory.user_id == current_user.id
    ).order_by(RecommendationHistory.created_at.desc()).all()

    total_plans = len(user_queries)
    total_budget_planned = sum(q.total_budget for q in user_queries)
    home_count = sum(1 for q in user_queries if q.category == "home")
    party_count = sum(1 for q in user_queries if q.category == "party")
    jewelry_count = sum(1 for q in user_queries if q.category == "jewelry")

    recent_plans = user_queries[:5]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "current_user": current_user,
            "total_plans": total_plans,
            "total_budget_planned": total_budget_planned,
            "home_count": home_count,
            "party_count": party_count,
            "jewelry_count": jewelry_count,
            "recent_plans": recent_plans
        }
    )


@router.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all saved recommendation queries with category filtering."""
    query = db.query(RecommendationHistory).filter(
        RecommendationHistory.user_id == current_user.id
    )
    if category and category in ["home", "party", "jewelry"]:
        query = query.filter(RecommendationHistory.category == category)

    plans = query.order_by(RecommendationHistory.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "current_user": current_user,
            "plans": plans,
            "selected_category": category or "all"
        }
    )


@router.get("/history/{rec_id}", response_class=HTMLResponse)
async def recommendation_detail_page(
    rec_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Inspect full AI breakdown and recommendation items for a past plan."""
    rec = db.query(RecommendationHistory).filter(RecommendationHistory.id == rec_id).first()
    if not rec:
        return RedirectResponse(url="/history", status_code=status.HTTP_302_FOUND)

    try:
        plan_data = json.loads(rec.ai_response_json)
    except Exception:
        plan_data = {}

    allocations = plan_data.get("budget_allocations", [])
    chart_labels = [a["category_name"] for a in allocations]
    chart_data = [a["allocated_amount"] for a in allocations]

    return templates.TemplateResponse(
        request=request,
        name="recommendation_details.html",
        context={
            "current_user": current_user,
            "rec": rec,
            "plan": plan_data,
            "chart_labels": json.dumps(chart_labels),
            "chart_data": json.dumps(chart_data)
        }
    )


@router.get("/testimonials", response_class=HTMLResponse)
async def testimonials_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Testimonials and Community reviews showcase."""
    testimonials = db.query(Testimonial).order_by(Testimonial.created_at.desc()).all()
    if not testimonials:
        # Seed initial testimonials if empty
        seed = [
            Testimonial(
                user_name="Aarav Sharma",
                role_or_occasion="3BHK Home Interior in Bangalore",
                comment="PocketSmart AI saved me at least ₹45,000 on my living room furnishing. The IKEA and Amazon product links matched my minimalist theme perfectly!",
                rating=5
            ),
            Testimonial(
                user_name="Pooja & Rohit",
                role_or_occasion="Engagement Celebration for 60 Guests",
                comment="Allocating budget across Zomato bulk catering, OYO banquet hall, and Amazon decor was seamless. Zero financial surprises on our big day.",
                rating=5
            ),
            Testimonial(
                user_name="Meera Kapoor",
                role_or_occasion="Diwali Festive Jewelry Matching",
                comment="I uploaded my emerald green lehenga image, and Gemini suggested the exact antique gold choker and jhumkas to complement my neckline. Mindblowing!",
                rating=5
            )
        ]
        for t in seed:
            db.add(t)
        db.commit()
        testimonials = db.query(Testimonial).order_by(Testimonial.created_at.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="testimonials.html",
        context={
            "current_user": current_user,
            "testimonials": testimonials
        }
    )


@router.post("/testimonials")
async def add_testimonial(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    user_name: str = Form(...),
    role_or_occasion: str = Form(...),
    comment: str = Form(...),
    rating: int = Form(5)
):
    """Submit a new user testimonial."""
    new_test = Testimonial(
        user_name=user_name,
        role_or_occasion=role_or_occasion,
        comment=comment,
        rating=max(1, min(5, rating))
    )
    db.add(new_test)
    db.commit()
    return RedirectResponse(url="/testimonials?msg=success", status_code=status.HTTP_302_FOUND)
