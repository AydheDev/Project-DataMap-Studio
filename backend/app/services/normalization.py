import re
from dataclasses import dataclass
from datetime import date, datetime
from numbers import Real
import pandas as pd

ERRORS = {"#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NUM!", "#NAME?", "#NULL!",
          "#SPILL!", "#CALC!", "#GETTING_DATA", "#UNCACHED_FORMULA!"}

@dataclass(frozen=True)
class ExcelFault:
    code: str
    original: str | None = None

def missing(value):
    if value is None:
        return True
    if isinstance(value, ExcelFault):
        return False
    if isinstance(value, str):
        return not value.strip()
    return bool(pd.isna(value))

def text(value):
    if isinstance(value, ExcelFault):
        return value.original or value.code
    return "" if missing(value) else str(value).strip()

def normalized(value):
    if isinstance(value, ExcelFault):
        return ""
    return " ".join(text(value).split()).casefold()

def email(value):
    if isinstance(value, ExcelFault) or text(value).upper() in ERRORS:
        return ""
    return text(value).lower()

def valid_email(value):
    return bool(re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", value))

def login_problem(value, day_first=True):
    if missing(value):
        return "blank_login"
    code = value.code if isinstance(value, ExcelFault) else text(value).upper()
    if code == "#N/A":
        return "na_login"
    if isinstance(value, ExcelFault) or code in ERRORS or isinstance(value, bool):
        return "invalid_login"
    if isinstance(value, (datetime, date)):
        return None
    if isinstance(value, Real):
        return None if 1 <= value <= 2958465 else "invalid_login"
    # Require a complete date, never infer missing year/month/day or accept arbitrary text.
    raw = text(value)
    complete = (r"^(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4}|"
                r"\d{1,2} +[A-Za-z]+ +\d{4}|[A-Za-z]+ +\d{1,2},? +\d{4})(?:$|[ T])")
    if not re.match(complete, raw):
        return "invalid_login"
    try:
        # ISO dates must not be reinterpreted by the day-first setting.
        iso = bool(re.match(r"^\d{4}-\d{2}-\d{2}(?:$|[T ])", raw))
        parsed = pd.to_datetime(raw, errors="coerce", dayfirst=False if iso else day_first)
        return "invalid_login" if pd.isna(parsed) else None
    except (ValueError, TypeError, OverflowError):
        return "invalid_login"

def public_value(value):
    if isinstance(value, ExcelFault):
        return {"error": value.code, "original": value.original}
    if missing(value):
        return None
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value
