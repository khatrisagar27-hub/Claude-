"""Loads an engagement's data into pandas once per run; every rule reads from it."""
import re
from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy import Boolean, Date, Numeric, String, Text, select
from sqlalchemy.orm import Session

from app.ingest.schema import DATASETS
from app.models import Client, Engagement
from app.statute import clean_id, gstin_state


def norm_doc(value) -> str:
    """Invoice numbers compared leniently, as a 2B reconciliation needs: case and
    separators ignored, and leading zeros dropped from every run of digits
    ("INV/0012" == "inv-12" == "INV 12")."""
    text = re.sub(r"\d+", lambda run: run.group(0).lstrip("0") or "0", str(value or "").upper())
    return re.sub(r"[^A-Z0-9]", "", text)


@dataclass
class Ctx:
    engagement_id: int
    period_start: pd.Timestamp
    period_end: pd.Timestamp
    as_at: pd.Timestamp          # date the data is taken to be complete up to
    home_state: str              # GST state code of the client, "" if GSTIN not recorded
    settings: dict
    materiality: float
    trivial: float

    def flag(self, name: str, default=False):
        return self.settings.get(name, default)


SETTING_DEFAULTS = {
    "einvoice_applicable": False,      # CGST Rule 48(4): aggregate turnover above the notified limit
    "tds_194q_applicable": False,      # s.194Q: buyer's turnover above Rs 10 crore in the preceding year
    "msme_written_agreement": True,    # MSMED s.15: 45 days with a written agreement, else 15
    "pf_applicable": True,
    "esi_applicable": True,
    "rbi_bank_rate_pct": 0,            # MSMED s.16 interest = 3 x bank rate; 0 = do not compute interest
    "data_as_at": None,                # ISO date; default is today, capped at period end
}


def make_ctx(db: Session, eng: Engagement, today: date | None = None) -> Ctx:
    settings = {**SETTING_DEFAULTS, **(eng.settings or {})}
    as_at = settings.get("data_as_at") or min(today or date.today(), eng.period_end)
    client = db.get(Client, eng.client_id)
    return Ctx(eng.id, pd.Timestamp(eng.period_start), pd.Timestamp(eng.period_end), pd.Timestamp(as_at),
               gstin_state(client.gstin) if client and client.gstin else "", settings,
               float(eng.materiality or 0), float(eng.trivial_threshold or 0))


class Data:
    """One DataFrame per dataset, typed for analysis: money as float, dates as
    datetime64, blank text as ''. Empty datasets still carry their columns."""

    def __init__(self, frames: dict):
        self.__dict__.update(frames)
        self.frames = frames

    def has(self, need: str) -> bool:
        name, _, column = need.partition(".")
        frame = self.frames[name]
        if frame.empty:
            return False
        if not column:
            return True
        series = frame[column]
        if series.dtype == object:
            return bool((series != "").any())
        if pd.api.types.is_numeric_dtype(series):
            return bool((series.fillna(0) != 0).any())
        return bool(series.notna().any())


def _typed(frame: pd.DataFrame, table) -> pd.DataFrame:
    for col in table.columns:
        if isinstance(col.type, Numeric):
            frame[col.name] = pd.to_numeric(frame[col.name], errors="coerce").astype(float)
            if not col.nullable or col.default is not None:
                frame[col.name] = frame[col.name].fillna(0.0)
        elif isinstance(col.type, Date):
            frame[col.name] = pd.to_datetime(frame[col.name], errors="coerce")
        elif isinstance(col.type, Boolean):
            frame[col.name] = frame[col.name].fillna(False).astype(bool)
        elif isinstance(col.type, (String, Text)):
            frame[col.name] = frame[col.name].fillna("").astype(str).str.strip()
    return frame


def load_data(db: Session, engagement_id: int) -> Data:
    frames = {}
    for key, ds in DATASETS.items():
        table = ds.model.__table__
        result = db.execute(select(table).where(table.c.engagement_id == engagement_id).order_by(table.c.id))
        frames[key] = _typed(pd.DataFrame(result.fetchall(), columns=list(result.keys())), table)
    return enrich(Data(frames))


def enrich(data: Data) -> Data:
    """Derived identity columns used by many rules."""
    p, s, parties = data.purchases, data.sales, data.parties
    p["doc"] = p["invoice_no"].map(norm_doc)
    p["vendor_gstin"] = p["vendor_gstin"].map(clean_id)
    p["vendor_key"] = p["vendor_gstin"].where(p["vendor_gstin"] != "", p["vendor_code"].str.upper())
    p["vendor_key"] = p["vendor_key"].where(p["vendor_key"] != "", p["vendor_name"].str.upper())
    p["gst"] = (p["cgst"] + p["sgst"] + p["igst"]).round(2)
    s["doc"] = s["invoice_no"].map(norm_doc)
    s["customer_gstin"] = s["customer_gstin"].map(clean_id)
    s["customer_key"] = s["customer_code"].str.upper().where(s["customer_code"] != "", s["customer_name"].str.upper())
    s["gst"] = (s["cgst"] + s["sgst"] + s["igst"]).round(2)
    for col in ("gstin", "pan"):
        parties[col] = parties[col].map(clean_id)
    data.gstr2b["supplier_gstin"] = data.gstr2b["supplier_gstin"].map(clean_id)
    data.gstr2b["doc"] = data.gstr2b["invoice_no"].map(norm_doc)
    data.employees["pan"] = data.employees["pan"].map(clean_id)
    lg = data.ledger
    group, name = lg["ledger_group"].str.lower(), lg["ledger"].str.lower()
    lg["is_cash"] = group.str.contains("cash") | ((group == "") & name.str.match(r"^(petty )?cash\b"))
    lg["is_bank"] = group.str.contains("bank") | ((group == "") & name.str.contains(r"\bbank\b"))
    lg["is_loan"] = group.str.contains("loan|deposit|borrowing") & ~group.str.contains("asset|advance")
    lg["is_income"] = group.str.contains("sales|income|revenue")
    lg["vkey"] = lg["voucher_type"] + "|" + lg["voucher_no"] + "|" + lg["voucher_date"].dt.strftime("%Y-%m-%d").fillna("")
    return data


def party_lookup(parties: pd.DataFrame, column: str) -> dict:
    """Map every way a party may be referred to (code, name, GSTIN) to one of its attributes."""
    out = {}
    for row in parties.itertuples(index=False):
        value = getattr(row, column)
        for ref in (row.code, row.name, row.gstin):
            if ref:
                out.setdefault(str(ref).upper(), value)
    return out


def fy_start_year(dates: pd.Series) -> pd.Series:
    """Financial year (April–March) a date falls in, as its starting calendar year."""
    return dates.dt.year - (dates.dt.month < 4).astype(int)
