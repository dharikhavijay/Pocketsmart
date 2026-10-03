from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import TEMPLATES_DIR, settings
from app.database import get_db
from app.models.user import User
from app.models.schemas import UserCreate, UserLogin
from app.services.auth_service import AuthService, get_current_user_optional

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: Optional[str] = "/dashboard",
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render login page. Redirect to dashboard if already authenticated."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "current_user": None,
            "next": next,
            "error": None
        }
    )


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    username_or_email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    next: Optional[str] = Form("/dashboard")
):
    """Handle user login for both Form submissions and JSON payloads."""
    # Check if request is JSON
    if request.headers.get("content-type") == "application/json":
        data = await request.json()
        identifier = data.get("username_or_email")
        pwd = data.get("password")
        is_api = True
    else:
        identifier = username_or_email
        pwd = password
        is_api = False

    if not identifier or not pwd:
        error = "Please provide both username/email and password."
        if is_api:
            return JSONResponse(status_code=400, content={"detail": error})
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "current_user": None,
                "next": next or "/dashboard",
                "error": error
            },
            status_code=400
        )

    user = AuthService.authenticate_user(db, identifier, pwd)
    if not user:
        error = "Invalid credentials. Please check your username/email and password."
        if is_api:
            return JSONResponse(status_code=401, content={"detail": error})
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "current_user": None,
                "next": next or "/dashboard",
                "error": error
            },
            status_code=401
        )

    # Generate token
    token = AuthService.create_access_token(data={"sub": user.username})

    if is_api:
        return {"access_token": token, "token_type": "bearer", "username": user.username}

    redirect_url = next if next and next.startswith("/") else "/dashboard"
    redirect = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return redirect


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render registration page."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "current_user": None,
            "error": None
        }
    )


@router.post("/register")
async def register(
    request: Request,
    db: Session = Depends(get_db),
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    password: Optional[str] = Form(None)
):
    """Handle new user registration."""
    is_api = request.headers.get("content-type") == "application/json"
    if is_api:
        data = await request.json()
        username = data.get("username")
        email = data.get("email")
        full_name = data.get("full_name")
        password = data.get("password")

    if not username or not email or not password:
        error = "Username, email, and password are required."
        if is_api:
            return JSONResponse(status_code=400, content={"detail": error})
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "error": error
            },
            status_code=400
        )

    # Check for existing user
    if db.query(User).filter(User.username == username).first():
        error = f"Username '{username}' is already taken."
        if is_api:
            return JSONResponse(status_code=400, content={"detail": error})
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "error": error
            },
            status_code=400
        )

    if db.query(User).filter(User.email == email).first():
        error = f"Email '{email}' is already registered."
        if is_api:
            return JSONResponse(status_code=400, content={"detail": error})
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "current_user": None,
                "error": error
            },
            status_code=400
        )

    # Create user
    hashed = AuthService.hash_password(password)
    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Login and redirect
    token = AuthService.create_access_token(data={"sub": new_user.username})

    if is_api:
        return {
            "message": "User registered successfully",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            }
        }

    redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return redirect


@router.post("/token")
async def get_token(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Issue JWT token for API clients."""
    user = AuthService.authenticate_user(db, user_data.username_or_email, user_data.password)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Incorrect username or password"}
        )
    token = AuthService.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/logout")
async def logout():
    """Clear session cookie and redirect to login."""
    response = RedirectResponse(url="/login?msg=logged_out", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response
