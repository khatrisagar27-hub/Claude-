"""Small utilities shared by rules."""
import math
from datetime import date, datetime

import pandas as pd

EVIDENCE_ROWS = 200


def rows(frame: pd.DataFrame, columns: list[str], limit: int = EVIDENCE_ROWS) -> list[dict]:
    """Evidence rows, JSON-safe and in the column order given."""
    out = []
    for record in frame[columns].head(limit).to_dict("records"):
        out.append({k: _plain(v) for k, v in record.items()})
    return out


def _plain(v):
    if v is None or v is pd.NaT:
        return None
    if isinstance(v, (pd.Timestamp, datetime, date)):
        return v.strftime("%d-%m-%Y")
    if isinstance(v, float):
        return None if math.isnan(v) else round(v, 2)
    if hasattr(v, "item"):
        return v.item()
    return v


def d(value) -> str:
    return "" if pd.isna(value) else pd.Timestamp(value).strftime("%d-%m-%Y")


def month(value) -> str:
    return pd.Timestamp(value).strftime("%b-%Y")
