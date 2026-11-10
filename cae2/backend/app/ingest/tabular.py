"""Excel / CSV → validated rows for one dataset.

Nothing is guessed silently: a row that fails validation is rejected with a
reason, columns we could not map are reported, and any value we derive is
recorded as a note on the import batch.
"""
import csv
import io
import re
from datetime import date, datetime

import pandas as pd

from app.ingest.schema import DATASETS, Dataset

TRUE = {"y", "yes", "true", "1", "t"}
FALSE = {"n", "no", "false", "0", "f", ""}
DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y", "%d/%m/%y", "%d-%m-%y",
                "%Y%m%d", "%d.%m.%Y", "%d %b %Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S")
MONTH_FORMATS = ("%b-%Y", "%b %Y", "%B %Y", "%B-%Y", "%Y-%m", "%m-%Y", "%m/%Y", "%b-%y")


def norm(text) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def blank(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NaT or str(v).strip() in ("", "nan", "NaT", "None")


def to_date(v) -> date:
    if isinstance(v, (datetime, pd.Timestamp)):
        return v.date()
    if isinstance(v, date):
        return v
    text = str(v).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError("is not a recognised date (use DD-MM-YYYY)")


def to_month(v) -> date:
    text = str(v).strip()
    if not isinstance(v, (datetime, pd.Timestamp, date)):
        for fmt in MONTH_FORMATS:
            try:
                return datetime.strptime(text, fmt).date().replace(day=1)
            except ValueError:
                pass
    return to_date(v).replace(day=1)


def to_number(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    text = str(v).strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "")
    negative = text.startswith("(") and text.endswith(")")
    text = re.sub(r"\s*(dr|cr)\.?$", "", text.strip("()"), flags=re.I).strip()
    try:
        number = float(text)
    except ValueError:
        raise ValueError("is not a number")
    return -number if negative else number


def read_table(filename: str, content: bytes) -> pd.DataFrame:
    """Raw cells with no header assumed, so we can find the header row ourselves."""
    if filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(io.BytesIO(content), header=None, dtype=object)
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Could not read the file as CSV")
    # csv.reader, not pandas: exports carry title rows with fewer cells than the data.
    lines = list(csv.reader(io.StringIO(text)))
    width = max((len(line) for line in lines), default=0)
    return pd.DataFrame([line + [""] * (width - len(line)) for line in lines], dtype=object)


def header_map(ds: Dataset) -> dict:
    lookup = {norm(col.name): col.name for col in ds.cols}  # a column's own name always wins over an alias
    for col in ds.cols:
        for spelling in col.aliases:
            lookup.setdefault(norm(spelling), col.name)
    return lookup


def find_header(raw: pd.DataFrame, ds: Dataset) -> int:
    """Exports often carry title rows; the header is the first row that names the required columns."""
    lookup, required = header_map(ds), {c.name for c in ds.cols if c.required}
    best, best_hits = None, 0
    for i in range(min(len(raw), 25)):
        found = {lookup[norm(c)] for c in raw.iloc[i].tolist() if not blank(c) and norm(c) in lookup}
        if required <= found:
            return i
        if len(found) > best_hits:
            best, best_hits = i, len(found)
    if best is None:
        raise ValueError(f"No column headings recognised. Expected at least: {', '.join(sorted(required))}")
    found = {lookup[norm(c)] for c in raw.iloc[best].tolist() if not blank(c) and norm(c) in lookup}
    raise ValueError(f"Required column(s) missing: {', '.join(sorted(required - found))}")


def coerce(col, value, max_len):
    if col.kind == "date":
        return to_date(value)
    if col.kind == "month":
        return to_month(value)
    if col.kind == "money":
        return round(to_number(value), 2)
    if col.kind == "qty":
        return round(to_number(value), 3)
    if col.kind == "int":
        return int(to_number(value))
    if col.kind == "bool":
        text = str(value).strip().lower()
        if text in TRUE:
            return True
        if text in FALSE:
            return False
        raise ValueError("must be Yes or No")
    text = str(value).strip()
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))  # Excel turns "1001" into 1001.0
    if col.kind == "choice":
        key = text.lower()
        if key in col.choices:
            return col.choices[key]
        if key.replace(" ", "_") in col.choices:
            return col.choices[key.replace(" ", "_")]
        raise ValueError(f"must be one of: {', '.join(sorted(set(col.choices.values())))}")
    if max_len and len(text) > max_len:
        raise ValueError(f"is longer than {max_len} characters")
    return text


def validate_rows(ds: Dataset, records: list[dict], first_row: int = 2):
    """records: list of {canonical column name: raw value}. Returns (rows, errors)."""
    table = ds.model.__table__
    rows, errors = [], []
    for offset, record in enumerate(records):
        row_no, out, problems = first_row + offset, {}, []
        if all(blank(v) for v in record.values()):
            continue
        for col in ds.cols:
            value = record.get(col.name)
            if blank(value):
                if col.required:
                    problems.append(f"{col.name} is blank")
                continue
            try:
                out[col.name] = coerce(col, value, getattr(table.c[col.name].type, "length", None))
            except ValueError as exc:
                problems.append(f"{col.name} '{str(value)[:40]}' {exc}")
        if problems:
            errors.append({"row": row_no, "problems": problems})
        else:
            out["source_row"] = row_no
            rows.append(out)
    return rows, errors


def parse_file(dataset: str, filename: str, content: bytes) -> dict:
    ds = DATASETS[dataset]
    raw = read_table(filename, content)
    head = find_header(raw, ds)
    lookup, mapping, unmapped = header_map(ds), {}, []
    for position, heading in enumerate(raw.iloc[head].tolist()):
        if blank(heading):
            continue
        name = lookup.get(norm(heading))
        if name and name not in mapping.values():
            mapping[position] = name
        else:
            unmapped.append(str(heading))
    body = raw.iloc[head + 1:]
    records = [{name: row[pos] for pos, name in mapping.items()} for row in body.itertuples(index=False)]
    rows, errors = validate_rows(ds, records, first_row=head + 2)
    return {"rows": rows, "errors": errors, "unmapped": unmapped, "mapped": sorted(mapping.values()),
            "rows_read": sum(1 for r in records if not all(blank(v) for v in r.values()))}
