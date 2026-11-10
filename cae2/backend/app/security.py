"""Passwords (bcrypt), JWT access tokens, and the role checks used by the API."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

ROLES = ("partner", "manager", "staff")
ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def check_password_strength(password: str):
    # bcrypt silently ignores bytes past 72, so reject rather than truncate.
    if len(password) < 10 or len(password.encode()) > 72:
        raise HTTPException(422, "Password must be 10 to 72 characters")


def create_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.token_minutes)
    return jwt.encode({"sub": str(user.id), "exp": expires}, settings.resolved_secret(), algorithm=ALGORITHM)


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)) -> User:
    if creds is None:
        raise HTTPException(401, "Not signed in")
    try:
        payload = jwt.decode(creds.credentials, settings.resolved_secret(), algorithms=[ALGORITHM])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Session expired or invalid")
    if user is None or not user.is_active:
        raise HTTPException(401, "Account disabled")
    return user


def require(*roles: str):
    """Dependency: the signed-in user must hold one of the given roles."""
    def check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, f"Requires role: {' or '.join(roles)}")
        return user
    return check


reviewer = require("partner", "manager")
partner = require("partner")
