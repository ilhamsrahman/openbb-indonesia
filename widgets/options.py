"""Endpoints that feed widget dropdowns (no widget of their own)."""
from typing import Optional

from core.bonds import retail
from core.ksei import master, ownership

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def ksei_dates():
    """Report months available in Balancepos files, newest first."""
    return sorted(ownership.list_available_dates(), key=lambda option: option["value"], reverse=True)


def bond_months():
    """Months available in the KSEI master securities files."""
    return [{"label": f"{MONTH_LABELS[int(m[4:]) - 1]} {m[:4]}", "value": m} for m in master.list_months()]


def retail_bond_types():
    return retail.list_retail_types()


def retail_curve(bond_type: str = "ORI", date: Optional[str] = None):
    """Bond-by-bond retail curve (coupon, years to maturity, duration) — used for analysis, not a widget."""
    return retail.get_retail_curve(bond_type, date)


ROUTES = {
    "/indonesia/dates": ksei_dates,
    "/indonesia/bond-months": bond_months,
    "/indonesia/retail-bond-types": retail_bond_types,
    "/indonesia/retail-curve": retail_curve,
}
