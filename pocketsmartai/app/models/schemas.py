from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# --- Auth Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None


# --- Recommendation Schemas ---
class RecommendedItem(BaseModel):
    item_name: str
    category: str
    estimated_price: float
    description: str
    suggested_platform: str  # Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, etc.
    platform_url: Optional[str] = None
    key_features: List[str] = []
    reasoning: Optional[str] = None


class CategoryAllocation(BaseModel):
    category_name: str
    allocated_amount: float
    percentage: float


class PlannerRecommendationResponse(BaseModel):
    category: str  # 'home', 'party', 'jewelry'
    title: str
    total_budget: float
    estimated_total_cost: float
    remaining_balance: float
    currency: str = "₹"
    budget_allocations: List[CategoryAllocation]
    recommendations: List[RecommendedItem]
    ai_insights: str
    outfit_analysis: Optional[Dict[str, Any]] = None  # For jewelry multimodal
    is_mock: bool = False


# --- Input Schemas ---
class HomePlannerInput(BaseModel):
    total_budget: float = Field(..., gt=0)
    room_type: str
    style_preference: str = "Modern & Minimalist"
    items_needed: List[str] = []
    additional_notes: Optional[str] = None


class PartyPlannerInput(BaseModel):
    total_budget: float = Field(..., gt=0)
    guest_count: int = Field(..., gt=0)
    event_type: str
    venue_type: str = "Home / Apartment"
    food_preference: str = "Buffet / Catering"
    include_entertainment: bool = True
    additional_notes: Optional[str] = None


class JewelryPlannerInput(BaseModel):
    total_budget: float = Field(..., gt=0)
    occasion: str
    style_preference: str = "Contemporary"
    jewelry_types: List[str] = []
    metal_preference: str = "Gold / Brass"
    additional_notes: Optional[str] = None


# --- Testimonial Schemas ---
class TestimonialCreate(BaseModel):
    user_name: str
    role_or_occasion: str
    comment: str
    rating: int = Field(5, ge=1, le=5)


class TestimonialResponse(TestimonialCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
