"""Replay transactions into holdings and cash; bond terms, coupon dates, latest new issues."""

from collections import defaultdict
from datetime import date
from typing import Optional

from .tracker import CASH_SIGN, _add_months, _d, _f, load_tracker


# ---------------------------------------------------------------- holdings replay
def holdings_on(d: date) -> dict:
    t = load_tracker()
    stocks = defaultdict(lambda: {"qty": 0.0, "cost": 0.0, "realized": 0.0, "dividends": 0.0})
    bonds = defaultdict(lambda: {"face": 0.0, "cost": 0.0, "coupons": 0.0})   # key (code, account)
    cash = 0.0
    for r in t["transactions"]:
        if r["Date"] > d:
            break
        typ, asset, code = r["Type"], r["Asset"], r["Code"]
        qty, price, amt = _f(r.get("Quantity")), _f(r.get("Price")), _f(r.get("Amount (IDR)"))
        if asset == "Stock" and not amt and qty and price:
            amt = qty * price
        if asset == "Bond" and not amt and qty and price:
            amt = qty * price / 100
        if asset != "Cash" or typ in CASH_SIGN:
            if not (asset in ("Stock", "Bond") and typ == "OPENING"):
                cash += CASH_SIGN.get(typ, 0) * amt
        if asset == "Cash" and typ == "OPENING":
            pass  # counted above
        if asset == "Stock":
            s = stocks[code]
            if typ in ("OPENING", "BUY"):
                s["qty"] += qty; s["cost"] += amt
            elif typ == "SELL" and s["qty"]:
                avg = s["cost"] / s["qty"]
                s["realized"] += amt - avg * qty
                s["cost"] -= avg * qty; s["qty"] -= qty
            elif typ == "DIVIDEND":
                s["dividends"] += amt
        elif asset == "Bond":
            key = (code, str(r.get("Account") or "Unknown"))
            b = bonds[key]
            if typ in ("OPENING", "BUY"):
                b["face"] += qty; b["cost"] += amt
            elif typ in ("SELL", "MATURITY"):
                if b["face"]:
                    b["cost"] -= b["cost"] * min(qty, b["face"]) / b["face"]
                b["face"] -= qty
            elif typ == "COUPON":
                # coupon rows may omit the account: attribute to the code's first holding
                b["coupons"] += amt
    # cash override from latest balance on/before d
    derived = cash
    gap, gap_date = 0.0, None
    for cb in t["cash_balances"]:
        if cb["Date"] <= d:
            derived_then = holdings_cash_derived(cb["Date"]) if cb["Date"] != d else derived
            bal = sum(_f(x.get("Balance (IDR)")) for x in t["cash_balances"] if x["Date"] == cb["Date"])
            gap, gap_date = bal - derived_then, cb["Date"]
    return {"stocks": {k: v for k, v in stocks.items() if abs(v["qty"]) > 1e-9 or v["realized"] or v["dividends"]},
            "bonds": {k: v for k, v in bonds.items() if v["face"] > 1e-6 or v["coupons"]},
            "cash": derived + gap, "cash_derived": derived, "cash_gap": gap, "cash_gap_date": gap_date}

def holdings_cash_derived(d: date) -> float:
    t = load_tracker()
    cash = 0.0
    for r in t["transactions"]:
        if r["Date"] > d:
            break
        if r["Asset"] in ("Stock", "Bond") and r["Type"] == "OPENING":
            continue
        amt = _f(r.get("Amount (IDR)"))
        if not amt and _f(r.get("Quantity")) and _f(r.get("Price")):
            amt = _f(r["Quantity"]) * _f(r["Price"]) / (100 if r["Asset"] == "Bond" else 1)
        cash += CASH_SIGN.get(r["Type"], 0) * amt
    return cash

# ---------------------------------------------------------------- bond terms
def bond_coupon(code: str) -> tuple[Optional[float], str]:
    t = load_tracker()
    info = t["bonds"].get(code, {})
    if str(info.get("Rate Type") or "").lower().startswith("float"):
        bi = _f(t["settings"].get("BI Rate"))
        return max(bi + _f(info.get("Spread")), _f(info.get("Floor"))), "Floating"
    c = info.get("Coupon")
    if c in (None, ""):
        return None, "Unknown"
    c = _f(c)
    return (c / 100 if c > 1 else c), "Fixed"

def bond_maturity(code: str) -> Optional[date]:
    return _d(load_tracker()["bonds"].get(code, {}).get("Maturity"))

def coupon_dates(code: str, start: date, end: date) -> list[date]:
    mat = bond_maturity(code)
    if not mat:
        return []
    freq = int(_f(load_tracker()["bonds"].get(code, {}).get("Coupons per Year")) or 2)
    step = 12 // max(freq, 1)
    out, k = [], 0
    while True:
        d = _add_months(mat, -step * k)
        if d < start:
            break
        if d <= end:
            out.append(d)
        k += 1
    return sorted(out)

# ---------------- 3. Bond coupons vs latest new issues
_new_issue_cache: dict = {}

def _tenor_from_code(code: str) -> Optional[int]:
    import re
    m = re.search(r"T(\d)$", code)
    return int(m.group(1)) if m else None

def latest_new_issues() -> dict[tuple, dict]:
    """(type, tenor) -> latest series {series, code, coupon_pct, issue_date} from KSEI + tracker bonds."""
    if _new_issue_cache.get("data") is not None and _new_issue_cache.get("day") == date.today():
        return _new_issue_cache["data"]
    cands = []
    try:
        from core.bonds.retail import _series_info
        for rec in _series_info().values():
            if rec.get("coupon_pct") is not None and rec.get("issue_date"):
                cands.append((rec["type"], rec["tenor_years"], rec["issue_date"], rec["code"], rec["coupon_pct"]))
    except Exception:
        pass
    t = load_tracker()
    for code, info in t["bonds"].items():
        ty = str(info.get("Type") or "").upper()
        tenor = _tenor_from_code(code)
        mat = _d(info.get("Maturity"))
        cpn, _ = bond_coupon(code)
        if ty and tenor and mat and cpn is not None:
            cands.append((ty, tenor, date(mat.year - tenor, mat.month, min(mat.day, 28)), code, round(cpn * 100, 4)))
    best: dict[tuple, dict] = {}
    for ty, tenor, issued, code, cpn in cands:
        k = (ty, tenor)
        if k not in best or issued > best[k]["issue_date"]:
            best[k] = {"code": code, "coupon_pct": cpn, "issue_date": issued}
    _new_issue_cache.update(data=best, day=date.today())
    return best
