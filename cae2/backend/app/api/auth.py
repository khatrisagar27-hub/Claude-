"""Sign-in, first-run setup and user administration."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import ROLES, check_password_strength, create_token, current_user, hash_password, partner, verify_password

router = APIRouter(tags=["auth"])


class Credentials(BaseModel):
    email: str
    password: str


class NewUser(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: str = Field(min_length=1, max_length=200)
    password: str
    role: str = "staff"


class UserPatch(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None


def user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role, "is_active": u.is_active}


def _create(db: Session, body: NewUser, role: str) -> User:
    if role not in ROLES:
        raise HTTPException(422, f"Role must be one of {', '.join(ROLES)}")
    check_password_strength(body.password)
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "A user with this email already exists")
    user = User(email=email, name=body.name.strip(), role=role, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return user


@router.get("/setup")
def setup_needed(db: Session = Depends(get_db)):
    return {"needed": db.scalar(select(func.count(User.id))) == 0}


@router.post("/setup")
def setup(body: NewUser, db: Session = Depends(get_db)):
    """Creates the first partner. Works only while there are no users at all."""
    if db.scalar(select(func.count(User.id))) > 0:
        raise HTTPException(409, "Setup is already complete")
    user = _create(db, body, "partner")
    return {"token": create_token(user), "user": user_out(user)}


@router.post("/login")
def login(body: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"token": create_token(user), "user": user_out(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_out(user)


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(partner)):
    return [user_out(u) for u in db.scalars(select(User).order_by(User.name))]


@router.post("/users")
def add_user(body: NewUser, db: Session = Depends(get_db), _: User = Depends(partner)):
    return user_out(_create(db, body, body.role))


@router.patch("/users/{user_id}")
def edit_user(user_id: int, body: UserPatch, db: Session = Depends(get_db), me: User = Depends(partner)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == me.id and (body.is_active is False or (body.role and body.role != "partner")):
        raise HTTPException(409, "You cannot remove your own partner access")
    if body.role is not None:
        if body.role not in ROLES:
            raise HTTPException(422, f"Role must be one of {', '.join(ROLES)}")
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.password:
        check_password_strength(body.password)
        user.password_hash = hash_password(body.password)
    db.commit()
    return user_out(user)
