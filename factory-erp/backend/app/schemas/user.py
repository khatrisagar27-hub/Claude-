from app.schemas.common import ORMModel


class UserCreate(ORMModel):
    plant_id: str | None = None
    name: str
    email: str
    password: str
    role: str = "operator"


class UserOut(ORMModel):
    id: str
    plant_id: str | None
    name: str
    email: str
    role: str
    is_active: bool


class LoginRequest(ORMModel):
    email: str
    password: str


class TokenResponse(ORMModel):
    access_token: str
    token_type: str = "bearer"
