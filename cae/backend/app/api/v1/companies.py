"""Company management endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tenant import Company, Tenant
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User

router = APIRouter()


class CompanyCreate(BaseModel):
    name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    entity_type: Optional[str] = None
    industry_sector: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class CompanyOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    gstin: Optional[str]
    pan: Optional[str]
    cin: Optional[str]
    entity_type: Optional[str]
    industry_sector: Optional[str]
    city: Optional[str]
    state: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    return db.query(Company).filter(
        Company.tenant_id == current_user.tenant_id,
        Company.is_active == True,
    ).all()


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner")),
):
    company = Company(id=uuid.uuid4(), tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.tenant_id == current_user.tenant_id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: uuid.UUID,
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner")),
):
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.tenant_id == current_user.tenant_id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(company, k, v)
    db.commit()
    db.refresh(company)
    return company
