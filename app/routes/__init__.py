from app.routes.auth import router as auth_router
from app.routes.home_planner import router as home_router
from app.routes.party_planner import router as party_router
from app.routes.jewelry_planner import router as jewelry_router
from app.routes.history import router as history_router
from app.routes.api import router as api_router

__all__ = [
    "auth_router",
    "home_router",
    "party_router",
    "jewelry_router",
    "history_router",
    "api_router",
]
