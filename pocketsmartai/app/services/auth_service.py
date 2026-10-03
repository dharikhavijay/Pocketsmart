import os
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User


class AuthService:
    """Handles password hashing, token generation, and user authentication."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash plain text password with bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain text password against bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Generate JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate JWT access token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None

    @classmethod
    def get_token_from_request(cls, request: Request) -> Optional[str]:
        """Extract JWT token from authorization header or cookie."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            if cookie_token.startswith("Bearer "):
                return cookie_token.split(" ")[1]
            return cookie_token
        return None

    @classmethod
    def get_user_by_username_or_email(cls, db: Session, identifier: str) -> Optional[User]:
        """Retrieve user by either email or username."""
        return db.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

    @classmethod
    def authenticate_user(cls, db: Session, identifier: str, password: str) -> Optional[User]:
        """Verify user credentials and return user object if valid."""
        user = cls.get_user_by_username_or_email(db, identifier)
        if not user:
            return None
        if not cls.verify_password(password, user.hashed_password):
            return None
        return user


# --- FastAPI Route Dependencies ---

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Dependency that returns the logged-in user if token exists, or None."""
    token = AuthService.get_token_from_request(request)
    if not token:
        return None
    payload = AuthService.decode_token(token)
    if not payload:
        return None
    username: str = payload.get("sub")
    if not username:
        return None
    user = db.query(User).filter(User.username == username).first()
    return user


def get_current_active_user(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Dependency requiring active authenticated user for API/HTML routes."""
    if not user:
        # If API request (JSON)
        if request.headers.get("accept") == "application/json" or request.url.path.startswith("/api/"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Web browser redirect to login
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/login?next={request.url.path}"}
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return user
