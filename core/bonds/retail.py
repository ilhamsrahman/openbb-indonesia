"""Indonesian retail government bonds (ORI, SR, ST, SBR, SWR): coupon curve and coupon trend.

Built from the KSEI Master Securities files (via core.ksei.master). KSEI has no bond prices, so these
use COUPON rates. Retail SBN are sold at par, so the coupon is the yield at issuance.
Missing coupons are filled from Data_raw/Bonds/retail_coupons_manual.csv (edit it for new series).
"""

import csv
import re
from datetime import date
from functools import lru_cache
from typing import Optional

from core.ksei.master import OUT_DIR, _num, _parse_date, list_months, load_master

RETAIL_TYPES = {
    "ORI": {"name": "ORI – Obligasi Negara Ritel", "rate": "Fixed", "default_tenor": 3},
    "SR":  {"name": "SR – Sukuk Ritel", "rate": "Fixed", "default_tenor": 3},
    "ST":  {"name": "ST – Sukuk Tabungan", "rate": "Floating with floor", "default_tenor": 2},
    "SBR": {"name": "SBR – Savings Bond Ritel", "rate": "Floating with floor", "default_tenor": 2},
    "SWR": {"name": "SWR – Sukuk Wakaf Ritel", "rate": "Floating with floor", "default_tenor": 2},
}
TENOR_COLUMNS = ["2Y", "3Y", "4Y", "5Y", "6Y"]
_CODE_RE = re.compile(r"^(ORI|SR|ST|SBR|SWR)(\d{3})(?:T(\d))?$")
MANUAL_FILE = OUT_DIR / "retail_coupons_manual.csv"


def _parse_code(code: str):
    """'ORI025T6' -> ('ORI', 'ORI025', 6); 'SR017' -> ('SR', 'SR017', 3)."""
    m = _CODE_RE.match(code)
    if not m:
        return None
    prefix, num, tenor = m.groups()
    return prefix, f"{prefix}{num}", int(tenor) if tenor else RETAIL_TYPES[prefix]["default_tenor"]


def _manual_coupons() -> dict[str, float]:
    if not MANUAL_FILE.exists():
        return {}
    with open(MANUAL_FILE, newline="", encoding="utf-8") as f:
        return {r["code"].strip(): float(r["coupon_pct"]) for r in csv.DictReader(f) if r.get("coupon_pct")}


def _macaulay_duration(coupon_pct: float, years_left: float) -> Optional[float]:
    """Macaulay duration (years) of a monthly-coupon bond priced at par (yield = coupon)."""
    n = max(1, round(years_left * 12))
    i = coupon_pct / 100 / 12
    pv_total = pv_weighted = 0.0
    for k in range(1, n + 1):
        cf = i + (1 if k == n else 0)
        pv = cf / (1 + i) ** k
        pv_total += pv
        pv_weighted += (k / 12) * pv
    return round(pv_weighted / pv_total, 2) if pv_total else None


@lru_cache(maxsize=None)
def _month_records(yyyymm: str) -> tuple:
    """Retail bonds present in one month's master file (cached; files don't change)."""
    out = []
    for m in load_master(yyyymm):
        parsed = _parse_code(m.get("Code", ""))
        if parsed:
            out.append((parsed, dict(m)))
    return tuple(out)


def _series_info() -> dict[str, dict]:
    """Static info per retail code across all months: maturity, issue date, coupon."""
    manual = _manual_coupons()
    info: dict[str, dict] = {}
    for ym in sorted(list_months()):                       # oldest -> newest; later months win
        for (prefix, series, tenor), m in _month_records(ym):
            rec = info.setdefault(m["Code"], {"code": m["Code"], "type": prefix, "series": series,
                                              "tenor_years": tenor})
            maturity = _parse_date(m["Maturity Date"])
            if maturity:
                rec["maturity_date"] = maturity
            listing = _parse_date(m["Listing Date"])
            if listing:
                rec["listing_date"] = listing
            if _num(m["Interest"]) is not None:
                rec["coupon_pct"] = _num(m["Interest"])
                rec["coupon_source"] = "KSEI"
    for code, rec in info.items():
        if rec.get("coupon_pct") is None and code in manual:
            rec["coupon_pct"] = manual[code]
            rec["coupon_source"] = "manual"
        mat = rec.get("maturity_date")
        # issue date: listing date if KSEI has it, else maturity minus tenor
        rec["issue_date"] = rec.get("listing_date") or (
            date(mat.year - rec["tenor_years"], mat.month, min(mat.day, 28)) if mat else None)
    return info


def list_retail_types() -> list[dict]:
    return [{"label": v["name"], "value": k} for k, v in RETAIL_TYPES.items()]


def get_retail_curve(bond_type: str = "ORI", date_str: Optional[str] = None) -> list[dict]:
    """Retail bonds of one type outstanding at a month-end, sorted by years to maturity.

    A bond counts as outstanding if issue_date <= month-end < maturity. Non-tradable series (ST, SBR,
    SWR) don't appear in every KSEI file, so dates are used rather than presence in that month's file.
    """
    bond_type = bond_type.upper()
    if bond_type not in RETAIL_TYPES:
        raise ValueError(f"bond_type must be one of {list(RETAIL_TYPES)}")
    ym = date_str or list_months()[0]
    month_rows = {m["Code"]: m for _, m in _month_records(ym)}
    any_row = next(iter(load_master(ym)), None)
    as_of = _parse_date(any_row["Date"]) if any_row else None
    if not as_of:
        raise ValueError(f"No master file for {ym}")

    fixed = RETAIL_TYPES[bond_type]["rate"] == "Fixed"
    rows = []
    for rec in _series_info().values():
        mat, issued = rec.get("maturity_date"), rec.get("issue_date")
        if rec["type"] != bond_type or not mat or not issued or not (issued <= as_of < mat):
            continue
        years_left = round((mat - as_of).days / 365.25, 2)
        coupon = rec.get("coupon_pct")
        m = month_rows.get(rec["code"])
        rows.append({
            "label": f"{rec['code']} ({years_left:.1f}y)",
            "code": rec["code"],
            "series": rec["series"],
            "tenor_years": rec["tenor_years"],
            "issue_date": issued.isoformat(),
            "maturity_date": mat.isoformat(),
            "years_to_maturity": years_left,
            "duration_years": _macaulay_duration(coupon, years_left) if (coupon and fixed) else None,
            "coupon_pct": coupon,
            "rate_type": RETAIL_TYPES[bond_type]["rate"],
            "outstanding_amt": (_num(m["Current Amt"]) or _num(m["Num. of Sec"])) if m else None,
            "coupon_source": rec.get("coupon_source"),
        })
    return sorted(rows, key=lambda r: r["years_to_maturity"])


def get_retail_coupon_trend(bond_type: str = "ORI") -> list[dict]:
    """One row per issued series (oldest first), with its coupon for each tenor."""
    bond_type = bond_type.upper()
    if bond_type not in RETAIL_TYPES:
        raise ValueError(f"bond_type must be one of {list(RETAIL_TYPES)}")
    series: dict[str, dict] = {}
    for rec in _series_info().values():
        if rec["type"] != bond_type or rec.get("coupon_pct") is None:
            continue
        row = series.setdefault(rec["series"], {"series": rec["series"], "issue_date": rec.get("issue_date"),
                                                **{c: None for c in TENOR_COLUMNS}})
        col = f"{rec['tenor_years']}Y"
        if col in row:
            row[col] = rec["coupon_pct"]
        if rec.get("issue_date") and (row["issue_date"] is None or rec["issue_date"] < row["issue_date"]):
            row["issue_date"] = rec["issue_date"]
    rows = sorted(series.values(), key=lambda r: r["issue_date"] or date.max)
    for r in rows:
        d = r["issue_date"]
        r["label"] = f"{r['series']} ({d.strftime('%b %Y')})" if d else r["series"]
        r["issue_date"] = d.isoformat() if d else None
    return rows


# ---------- TradingView-style curve: fixed tenors, compare dates ----------
CURVE_TENORS = [("6M", 0.5), ("1Y", 1), ("2Y", 2), ("3Y", 3), ("4Y", 4), ("5Y", 5), ("6Y", 6)]


def _curve_points(bond_type: str, ym: str) -> list[tuple[float, float]]:
    """(years_to_maturity, coupon) for outstanding bonds; bonds within 0.25y are averaged."""
    pts = sorted((r["years_to_maturity"], r["coupon_pct"])
                 for r in get_retail_curve(bond_type, ym) if r["coupon_pct"] is not None)
    merged: list[list[float]] = []
    for y, c in pts:
        if merged and y - merged[-1][0] <= 0.25:
            grp = merged[-1]
            grp[2] += 1
            grp[0] += (y - grp[0]) / grp[2]
            grp[1] += (c - grp[1]) / grp[2]
        else:
            merged.append([y, c, 1])
    return [(y, c) for y, c, _ in merged]


def _interpolate(points: list[tuple[float, float]], x: float, max_extrap: float = 0.5) -> Optional[float]:
    """Linear interpolation; flat extrapolation up to max_extrap years beyond the ends, else None."""
    if not points:
        return None
    if x <= points[0][0]:
        return round(points[0][1], 3) if points[0][0] - x <= max_extrap else None
    if x >= points[-1][0]:
        return round(points[-1][1], 3) if x - points[-1][0] <= max_extrap else None
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return round(y0 + (y1 - y0) * (x - x0) / (x1 - x0), 3) if x1 != x0 else round(y0, 3)
    return None


def _shift_month(ym: str, months: int) -> str:
    y, m = int(ym[:4]), int(ym[4:])
    total = y * 12 + (m - 1) - months
    return f"{total // 12}{total % 12 + 1:02d}"


def get_retail_yield_curve(bond_type: str = "ORI", date_str: Optional[str] = None,
                           compare_1: Optional[str] = None, compare_2: Optional[str] = None) -> list[dict]:
    """Rows = tenors (6M..6Y); columns = coupon curve at the selected month and two comparison months.

    Defaults: compare_1 = 1 month earlier, compare_2 = 1 year earlier. Months without a master file
    (or with no outstanding bonds) give empty values.
    """
    bond_type = bond_type.upper()
    if bond_type not in RETAIL_TYPES:
        raise ValueError(f"bond_type must be one of {list(RETAIL_TYPES)}")
    available = set(list_months())
    ym = date_str or list_months()[0]
    months = {"selected": ym,
              "compare_1": compare_1 or _shift_month(ym, 1),
              "compare_2": compare_2 or _shift_month(ym, 12)}
    curves = {k: (_curve_points(bond_type, v) if v in available else []) for k, v in months.items()}
    max_tenor = max((y for pts in curves.values() for y, _ in pts), default=0)

    rows = []
    for label, years in CURVE_TENORS:
        if years > max_tenor + 0.5:
            break
        row = {"tenor": label, "years": years}
        for k in months:
            row[k] = _interpolate(curves[k], years)
        row["change_1_bp"] = round((row["selected"] - row["compare_1"]) * 100) \
            if row["selected"] is not None and row["compare_1"] is not None else None
        row["change_2_bp"] = round((row["selected"] - row["compare_2"]) * 100) \
            if row["selected"] is not None and row["compare_2"] is not None else None
        row["months"] = f"{months['selected']} vs {months['compare_1']} vs {months['compare_2']}"
        rows.append(row)
    return rows
