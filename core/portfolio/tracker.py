"""Read Portfolio_Tracker.xlsx and shared helpers (dates, numbers, cash signs)."""

import calendar
from datetime import date
from datetime import datetime
from typing import Optional

from core.paths import TRACKER


CASH_SIGN = {"OPENING": 1, "BUY": -1, "SELL": 1, "COUPON": 1, "DIVIDEND": 1, "MATURITY": 1,
             "DEPOSIT": 1, "WITHDRAW": -1, "FEE": -1, "TAX": -1}

EXTERNAL_FLOW = {"DEPOSIT": 1, "WITHDRAW": -1}

# ---------------------------------------------------------------- helpers
def _d(x) -> Optional[date]:
    if x is None or x == "":
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y", "%d %b %Y"):
        try:
            return datetime.strptime(str(x).strip(), fmt).date()
        except ValueError:
            pass
    return None

def _f(x) -> float:
    if x in (None, ""):
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).replace(",", "").replace("%", ""))
    except ValueError:
        return 0.0

def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))

# ---------------------------------------------------------------- tracker file (cached by mtime)
_tracker_cache: dict = {}

def load_tracker() -> dict:
    if not TRACKER.exists():
        raise FileNotFoundError(f"Tracker not found: {TRACKER}")
    mtime = TRACKER.stat().st_mtime
    if _tracker_cache.get("mtime") == mtime:
        return _tracker_cache["data"]
    import openpyxl  # imported here so a missing package only affects portfolio widgets
    wb = openpyxl.load_workbook(TRACKER, data_only=True, read_only=True)

    def rows(name):
        ws = wb[name]
        it = ws.iter_rows(values_only=True)
        header = [str(h).strip() if h else "" for h in next(it)]
        return [dict(zip(header, r)) for r in it if any(v not in (None, "") for v in r)]

    settings = {str(r["Setting"]).strip(): r["Value"] for r in rows("Settings") if r.get("Setting")}
    data = {
        "transactions": sorted(
            [dict(r, Date=_d(r["Date"]), Type=str(r["Type"] or "").strip().upper(),
                  Asset=str(r["Asset"] or "").strip().title(), Code=str(r["Code"] or "").strip().upper())
             for r in rows("Transactions") if _d(r.get("Date")) and r.get("Type")],
            key=lambda r: (r["Date"], r["Type"] != "OPENING")),
        "stocks": {str(r["Ticker"]).strip().upper(): r for r in rows("Stock_Info") if r.get("Ticker")},
        "bonds": {str(r["Code"]).strip().upper(): r for r in rows("Bond_Info") if r.get("Code")},
        "cash_balances": sorted([dict(r, Date=_d(r["Date"])) for r in rows("Cash_Balances") if _d(r.get("Date"))],
                                key=lambda r: r["Date"]),
        "settings": settings,
        "start": _d(settings.get("Start date")) or date(2026, 9, 30),
    }
    wb.close()
    _tracker_cache.update(mtime=mtime, data=data, computed={})
    return data
