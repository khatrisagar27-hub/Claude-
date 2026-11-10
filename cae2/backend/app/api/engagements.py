"""Clients and engagements."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit.dataset import SETTING_DEFAULTS
from app.db import get_db
from app.models import Client, Engagement, Finding, User
from app.security import current_user, reviewer
from app.statute import clean_id, gstin_valid, pan_valid

router = APIRouter(tags=["engagements"])
KINDS = ("internal_audit", "statutory_audit", "tax_audit", "gst_review")


class ClientIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    pan: str | None = None
    gstin: str | None = None


class EngagementIn(BaseModel):
    client_id: int
    name: str = Field(min_length=1, max_length=200)
    kind: str = "internal_audit"
    period_start: date
    period_end: date
    materiality: float = Field(0, ge=0)
    trivial_threshold: float = Field(0, ge=0)
    settings: dict = {}


class EngagementPatch(BaseModel):
    name: str | None = None
    materiality: float | None = Field(None, ge=0)
    trivial_threshold: float | None = Field(None, ge=0)
    settings: dict | None = None
    is_closed: bool | None = None


def get_engagement(engagement_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)) -> Engagement:
    eng = db.get(Engagement, engagement_id)
    if not eng:
        raise HTTPException(404, "Engagement not found")
    return eng


def open_engagement(eng: Engagement = Depends(get_engagement)) -> Engagement:
    if eng.is_closed:
        raise HTTPException(409, "This engagement is closed. Reopen it to make changes.")
    return eng


def _clean_settings(settings: dict) -> dict:
    unknown = set(settings) - set(SETTING_DEFAULTS)
    if unknown:
        raise HTTPException(422, f"Unknown setting(s): {', '.join(sorted(unknown))}")
    if settings.get("data_as_at"):
        try:
            date.fromisoformat(settings["data_as_at"])
        except (TypeError, ValueError):
            raise HTTPException(422, "data_as_at must be a date in YYYY-MM-DD form")
    return settings


def eng_out(e: Engagement, db: Session) -> dict:
    counts = dict(db.execute(select(Finding.status, func.count()).where(Finding.engagement_id == e.id).group_by(Finding.status)).all())
    return {"id": e.id, "client_id": e.client_id, "client_name": e.client.name, "client_gstin": e.client.gstin,
            "name": e.name, "kind": e.kind, "period_start": e.period_start, "period_end": e.period_end,
            "materiality": float(e.materiality or 0), "trivial_threshold": float(e.trivial_threshold or 0),
            "settings": {**SETTING_DEFAULTS, **(e.settings or {})}, "is_closed": e.is_closed,
            "open_findings": sum(counts.get(s, 0) for s in ("open", "queried"))}


@router.get("/clients")
def list_clients(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return [{"id": c.id, "name": c.name, "pan": c.pan, "gstin": c.gstin} for c in db.scalars(select(Client).order_by(Client.name))]


@router.post("/clients")
def add_client(body: ClientIn, db: Session = Depends(get_db), _: User = Depends(reviewer)):
    pan, gstin = clean_id(body.pan) or None, clean_id(body.gstin) or None
    if pan and not pan_valid(pan):
        raise HTTPException(422, "PAN is not in a valid format")
    if gstin and not gstin_valid(gstin):
        raise HTTPException(422, "GSTIN is not valid (format or check digit)")
    client = Client(name=body.name.strip(), pan=pan, gstin=gstin)
    db.add(client)
    db.commit()
    return {"id": client.id, "name": client.name, "pan": client.pan, "gstin": client.gstin}


@router.get("/engagements")
def list_engagements(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return [eng_out(e, db) for e in db.scalars(select(Engagement).order_by(Engagement.id.desc()))]


@router.post("/engagements")
def add_engagement(body: EngagementIn, db: Session = Depends(get_db), _: User = Depends(reviewer)):
    if not db.get(Client, body.client_id):
        raise HTTPException(404, "Client not found")
    if body.kind not in KINDS:
        raise HTTPException(422, f"Kind must be one of {', '.join(KINDS)}")
    if body.period_end <= body.period_start:
        raise HTTPException(422, "Period end must be after period start")
    eng = Engagement(**body.model_dump(exclude={"settings"}), settings=_clean_settings(body.settings))
    db.add(eng)
    db.commit()
    return eng_out(eng, db)


@router.get("/engagements/{engagement_id}")
def read_engagement(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    return eng_out(eng, db)


@router.patch("/engagements/{engagement_id}")
def edit_engagement(body: EngagementPatch, eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db),
                    _: User = Depends(reviewer)):
    changes = body.model_dump(exclude_none=True)
    if eng.is_closed and set(changes) - {"is_closed"}:
        raise HTTPException(409, "This engagement is closed. Reopen it to make changes.")
    if "settings" in changes:
        changes["settings"] = {**(eng.settings or {}), **_clean_settings(changes["settings"])}
    for name, value in changes.items():
        setattr(eng, name, value)
    db.commit()
    return eng_out(eng, db)
