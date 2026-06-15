from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that decodes the Bearer JWT and returns the
    authenticated User ORM object.

    Raises:
        HTTPException 401: If token is missing, malformed, or expired.
        HTTPException 401: If the user referenced in the token no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_type: str = payload.get("type", "access")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type; access token required",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user


def require_roles(*roles: str) -> Callable:
    """
    Factory that returns a FastAPI dependency which enforces role-based access.

    Usage::

        @router.get("/admin")
        async def admin_only(user: User = Depends(require_roles("super_admin", "partner"))):
            ...

    Args:
        *roles: One or more role strings that are permitted.

    Returns:
        An async FastAPI dependency that resolves to the current User if
        authorised, or raises HTTP 403 otherwise.
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(roles)}. "
                f"Your role: {current_user.role}",
            )
        return current_user

    return role_checker


# ---------------------------------------------------------------------------
# Convenience dependencies — import these directly in route handlers
# ---------------------------------------------------------------------------

#: Any internal audit team member (super_admin down to auditor)
require_auditor: Callable = require_roles(
    "super_admin", "partner", "manager", "auditor"
)

#: Partner-level and above (e.g. firm admin tasks)
require_partner: Callable = require_roles("super_admin", "partner")

#: Management-facing roles (can view dashboards / approve queries)
require_management: Callable = require_roles(
    "super_admin", "partner", "manager", "cfo", "management"
)

#: Super admin only
require_super_admin: Callable = require_roles("super_admin")
