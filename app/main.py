import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import settings, STATIC_DIR, TEMPLATES_DIR, UPLOADS_DIR
from app.database import init_db
from app.routes import (
    auth_router,
    home_router,
    party_router,
    jewelry_router,
    history_router,
    api_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pocketsmartai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    logger.info(f"Initializing {settings.APP_NAME}...")
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    logger.info("Database tables initialized.")
    yield
    logger.info("PocketSmart AI application shutdown.")


app = FastAPI(
    title=settings.APP_NAME,
    description="GenAI-powered smart budget allocation & product recommendation assistant across Home, Party, and Jewelry domains.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include Routers
app.include_router(auth_router)
app.include_router(home_router)
app.include_router(party_router)
app.include_router(jewelry_router)
app.include_router(history_router)
app.include_router(api_router)


# Global Exception Handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.headers.get("accept") == "application/json" or request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "Resource not found"})
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "current_user": None,
            "page_title": "404 - Page Not Found",
            "content": """
            <div class="text-center py-5">
                <h1 class="display-1 text-primary fw-bold">404</h1>
                <h3 class="mb-3">Oops! Page Not Found</h3>
                <p class="text-muted mb-4">The budget planner or resource you were looking for doesn't exist.</p>
                <a href="/" class="btn btn-primary px-4 py-2"><i class="fa-solid fa-house me-2"></i>Return Home</a>
            </div>
            """
        },
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    if request.headers.get("accept") == "application/json" or request.url.path.startswith("/api/"):
        return JSONResponse(status_code=500, content={"detail": "Internal server error occurred"})
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "current_user": None,
            "page_title": "500 - Server Error",
            "content": """
            <div class="text-center py-5">
                <h1 class="display-1 text-danger fw-bold">500</h1>
                <h3 class="mb-3">Something Went Wrong</h3>
                <p class="text-muted mb-4">Our AI assistant encountered an unexpected error. Please try again shortly.</p>
                <a href="/" class="btn btn-outline-primary px-4 py-2"><i class="fa-solid fa-arrow-left me-2"></i>Back to Safety</a>
            </div>
            """
        },
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
