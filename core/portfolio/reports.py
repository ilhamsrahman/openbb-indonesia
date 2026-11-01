"""Widget-ready tables built from the engine (one function per portfolio widget)."""

from collections import defaultdict
from datetime import date
from datetime import datetime
from datetime import timedelta

from .holdings import _tenor_from_code, bond_coupon, bond_maturity, coupon_dates, holdings_cash_derived, holdings_on, latest_new_issues
from .ownership import _signal, ownership_for
from .performance import TRADABLE_AT_COST, _bond_value, nav_series, value_on
from .prices import _benchmark_prices, _dividends, _stock_prices, price_on
from .tracker import EXTERNAL_FLOW, _add_months, _f, load_tracker


def warm_up_prices() -> None:
    """Fetch all held tickers + benchmark in parallel (call once at run.py startup)."""
    from concurrent.futures import ThreadPoolExecutor
    try:
        t = load_tracker()
    except Exception:
        return
    tickers = {r["Code"] for r in t["transactions"] if r["Asset"] == "Stock"}
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_stock_prices, tickers))
        list(ex.map(_dividends, tickers))
    _benchmark_prices(str(t["settings"].get("Benchmark") or "^JKSE"))
    try:
        latest_new_issues()          # reads all KSEI master files once (a few seconds)
    except Exception:
        pass

# ---------------------------------------------------------------- API-facing functions
def get_summary() -> list[dict]:
    nav = nav_series()
    last, first = nav[-1], nav[0]
    t = load_tracker()
    d_last = date.fromisoformat(last["date"])
    prev_month_end = max((r for r in nav if date.fromisoformat(r["date"]) < d_last.replace(day=1)), default=first,
                         key=lambda r: r["date"])
    mtd = last["nav"] / prev_month_end["nav"] - 1
    since = last["nav"] / first["nav"] - 1
    bench_since = (last["benchmark"] / first["benchmark"] - 1) if last["benchmark"] and first["benchmark"] else None
    income = sum(r["annual_net_income"] for r in get_bonds() if r["status"] == "Active")
    eq = last["stocks"] / last["total_value"] if last["total_value"] else 0
    tgt = _f(t["settings"].get("Target equity %"))
    return [
        {"label": "Total Portfolio (IDR bn)", "value": f"{last['total_value'] / 1e9:,.2f}",
         "delta": f"{(last['total_value'] - first['total_value']) / 1e9:+,.2f} since {first['date']}"},
        {"label": f"Return since {first['date']}", "value": f"{since * 100:.2f}%",
         "delta": f"{(since - bench_since) * 100:+.2f} pp vs IHSG" if bench_since is not None else ""},
        {"label": f"Month to date ({d_last.strftime('%b %Y')})", "value": f"{mtd * 100:.2f}%", "delta": ""},
        {"label": "Equity allocation", "value": f"{eq * 100:.1f}%", "delta": f"{(eq - tgt) * 100:+.1f} pp vs target {tgt * 100:.0f}%"},
        {"label": "Expected bond income / yr (net)", "value": f"{income / 1e9:,.3f} bn", "delta": ""},
        {"label": "Expected dividends / yr (gross, TTM)",
         "value": f"{sum(r['expected_dividends'] for r in get_stocks()) / 1e9:,.3f} bn", "delta": ""},
        {"label": "Prices as of", "value": last["date"], "delta": ""},
    ]

def get_allocation() -> list[dict]:
    v = value_on(date.today())
    tot = v["total"] or 1
    rows = [("Stocks — Core", v["stocks_core"]), ("Stocks — Dibuang", v["stocks_dibuang"]),
            ("Bonds / Sukuk", v["bonds"]), ("Cash", v["cash"])]
    return [{"asset": a, "value": round(x), "weight_pct": round(x / tot * 100, 2)} for a, x in rows]

def get_rebalance() -> list[dict]:
    t = load_tracker()
    v = value_on(date.today())
    tot = v["total"] or 1
    teq, tfi = _f(t["settings"].get("Target equity %")), _f(t["settings"].get("Target fixed income %"))
    eq, fi = v["stocks"], v["bonds"] + v["cash"]
    return [
        {"bucket": "Equity (stocks)", "current_value": round(eq), "current_pct": round(eq / tot * 100, 2),
         "target_pct": round(teq * 100, 2), "target_value": round(teq * tot), "gap_value": round(teq * tot - eq)},
        {"bucket": "Fixed income (bonds + cash)", "current_value": round(fi), "current_pct": round(fi / tot * 100, 2),
         "target_pct": round(tfi * 100, 2), "target_value": round(tfi * tot), "gap_value": round(tfi * tot - fi)},
    ]

def get_stocks() -> list[dict]:
    t = load_tracker()
    today = date.today()
    h = holdings_on(today)
    rows = []
    for code, s in h["stocks"].items():
        if s["qty"] <= 0:
            continue
        p, pd, src = price_on(code, today)
        info = t["stocks"].get(code, {})
        mv = (p or 0) * s["qty"]
        rows.append({"ticker": code, "sector": info.get("Sector"), "tag": info.get("Tag") or "Core",
                     "quantity": s["qty"], "avg_cost": round(s["cost"] / s["qty"], 2), "price": p,
                     "price_date": pd.isoformat() if pd else None, "price_source": src,
                     "cost": round(s["cost"]), "market_value": round(mv), "pnl": round(mv - s["cost"]),
                     "return_pct": round((mv / s["cost"] - 1) * 100, 2) if s["cost"] else None,
                     "dividends": round(s["dividends"]), "realized_pnl": round(s["realized"])})
    tot = sum(r["market_value"] for r in rows) or 1
    for r in rows:
        o = ownership_for(r["ticker"])
        r["foreign_pct"], r["foreign_chg_1m"] = o.get("foreign_pct"), o.get("foreign_chg_1m")
        divs = _dividends(r["ticker"])
        ttm = sum(v for d, v in divs.items() if d > today - timedelta(days=365))
        r["div_yield_pct"] = round(ttm / r["price"] * 100, 2) if (r["price"] and ttm) else 0
        r["expected_dividends"] = round(ttm * r["quantity"])
    for r in rows:
        r["weight_pct"] = round(r["market_value"] / tot * 100, 2)
    return sorted(rows, key=lambda r: -r["market_value"])

def get_sectors() -> list[dict]:
    agg = defaultdict(lambda: {"market_value": 0, "cost": 0})
    for r in get_stocks():
        a = agg[r["sector"] or "Other"]
        a["market_value"] += r["market_value"]; a["cost"] += r["cost"]
    tot = sum(a["market_value"] for a in agg.values()) or 1
    return sorted([{"sector": k, "market_value": v["market_value"], "cost": v["cost"],
                    "pnl": v["market_value"] - v["cost"],
                    "return_pct": round((v["market_value"] / v["cost"] - 1) * 100, 2) if v["cost"] else None,
                    "weight_pct": round(v["market_value"] / tot * 100, 2)} for k, v in agg.items()],
                  key=lambda r: -r["market_value"])

def get_bonds() -> list[dict]:
    t = load_tracker()
    today = date.today()
    tax = _f(t["settings"].get("Coupon tax"))
    h = holdings_on(today)
    rows = []
    for (code, acct), b in h["bonds"].items():
        if b["face"] <= 0:
            continue
        cpn, rate_type = bond_coupon(code)
        mat = bond_maturity(code)
        info = t["bonds"].get(code, {})
        nxt = next(iter(coupon_dates(code, today + timedelta(days=1), today + timedelta(days=400))), None)
        status = "Matured" if (mat and mat <= today) else "Active"
        ty = str(info.get("Type") or "").upper()
        rows.append({"code": code, "type": info.get("Type"), "account": acct, "face_value": round(b["face"]),
                     "value": round(_bond_value(code, b)),
                     "valuation": "Purchase price" if ty in TRADABLE_AT_COST else "Face value",
                     "cost": round(b["cost"]), "price_pct": round(b["cost"] / b["face"] * 100, 3) if b["face"] else None,
                     "coupon_pct": round(cpn * 100, 3) if cpn is not None else None, "rate_type": rate_type,
                     "maturity": mat.isoformat() if mat else None,
                     "years_to_maturity": round(max(0, (mat - today).days) / 365.25, 2) if mat else None,
                     "status": status, "next_coupon": nxt.isoformat() if nxt and status == "Active" else None,
                     "annual_net_income": round(b["face"] * (cpn or 0) * (1 - tax)) if status == "Active" else 0,
                     "coupons_received": round(b["coupons"])})
    issues = latest_new_issues()
    for r in rows:
        ni = issues.get((str(r["type"] or "").upper(), _tenor_from_code(r["code"]) or 0))
        if ni and ni["code"] != r["code"] and r["coupon_pct"] is not None:
            r["new_issue"] = ni["code"]
            r["new_issue_coupon_pct"] = ni["coupon_pct"]
            r["coupon_vs_new_bp"] = round((r["coupon_pct"] - ni["coupon_pct"]) * 100)
        else:
            r["new_issue"] = ni["code"] if ni else None
            r["new_issue_coupon_pct"] = ni["coupon_pct"] if ni else None
            r["coupon_vs_new_bp"] = 0 if ni else None
    return sorted(rows, key=lambda r: (r["maturity"] or "9999", r["code"], r["account"]))

def get_maturity_ladder() -> list[dict]:
    agg = defaultdict(lambda: defaultdict(float))
    types = set()
    for r in get_bonds():
        if r["status"] != "Active" or not r["maturity"]:
            continue
        agg[r["maturity"][:4]][r["type"] or "Other"] += r["face_value"]
        types.add(r["type"] or "Other")
    out = []
    for y in sorted(agg):
        row = {"year": y}
        for ty in ("SR", "ST", "PBS", "ORI", "SBR", "FR", "Other"):
            row[ty] = round(agg[y].get(ty, 0))
        row["total"] = round(sum(agg[y].values()))
        out.append(row)
    return out

def get_coupon_calendar(months: int = 12) -> list[dict]:
    t = load_tracker()
    tax = _f(t["settings"].get("Coupon tax"))
    today = date.today()
    first = date(today.year, today.month, 1)
    end = _add_months(first, months) - timedelta(days=1)
    agg = defaultdict(lambda: defaultdict(float))
    h = holdings_on(today)
    for (code, _), b in h["bonds"].items():
        if b["face"] <= 0:
            continue
        cpn, _ = bond_coupon(code)
        freq = int(_f(t["bonds"].get(code, {}).get("Coupons per Year")) or 2)
        ty = t["bonds"].get(code, {}).get("Type") or "Other"
        for d in coupon_dates(code, first, end):
            agg[d.strftime("%Y-%m")][ty] += b["face"] * (cpn or 0) / freq * (1 - tax)
    out = []
    m = first
    while m <= end:
        k = m.strftime("%Y-%m")
        row = {"month": m.strftime("%b %Y")}
        for ty in ("SR", "ST", "PBS", "ORI", "SBR", "FR", "Other"):
            row[ty] = round(agg[k].get(ty, 0))
        row["total"] = round(sum(agg[k].values()))
        out.append(row)
        m = _add_months(m, 1)
    return out

def get_monthly_returns() -> list[dict]:
    nav = nav_series()
    t = load_tracker()
    by_month = {}
    for r in nav:
        by_month[r["date"][:7]] = r            # last trading day of each month
    months = sorted(by_month)
    out, prev = [], nav[0]
    income = defaultdict(float)
    flows_ext = defaultdict(float)
    for r in t["transactions"]:
        k = r["Date"].isoformat()[:7]
        if r["Type"] in ("COUPON", "DIVIDEND"):
            income[k] += _f(r.get("Amount (IDR)"))
        if r["Type"] in EXTERNAL_FLOW:
            flows_ext[k] += EXTERNAL_FLOW[r["Type"]] * _f(r.get("Amount (IDR)"))
    for k in months:
        cur = by_month[k]
        if cur["date"] == prev["date"]:
            continue
        out.append({"month": datetime.strptime(k, "%Y-%m").strftime("%b %Y"), "end_date": cur["date"],
                    "portfolio_pct": round((cur["nav"] / prev["nav"] - 1) * 100, 2),
                    "benchmark_pct": round((cur["benchmark"] / prev["benchmark"] - 1) * 100, 2)
                    if cur["benchmark"] and prev["benchmark"] else None,
                    "end_value": cur["total_value"], "income_received": round(income.get(k, 0)),
                    "net_deposits": round(flows_ext.get(k, 0)),
                    "status": "Month to date" if k == date.today().strftime("%Y-%m") else "Complete"})
        prev = cur
    return out

def get_checks() -> list[dict]:
    t = load_tracker()
    today = date.today()
    out = []
    h = holdings_on(today)
    for cb_date in sorted({cb["Date"] for cb in t["cash_balances"]}):
        bal = sum(_f(x.get("Balance (IDR)")) for x in t["cash_balances"] if x["Date"] == cb_date)
        gap = bal - holdings_cash_derived(cb_date)
        if abs(gap) > 1000:
            out.append({"severity": "Warning", "check": "Cash reconciliation",
                        "detail": f"{cb_date}: actual cash {bal:,.0f} vs transactions {bal - gap:,.0f} "
                                  f"(gap {gap:+,.0f}). A coupon, dividend, deposit or fee may be missing."})
    for (code, acct), b in h["bonds"].items():
        mat = bond_maturity(code)
        if b["face"] > 0 and mat and mat <= today:
            out.append({"severity": "Action", "check": "Matured bond",
                        "detail": f"{code} ({acct}) matured on {mat}. Add a MATURITY transaction for {b['face']:,.0f}."})
        if b["face"] > 0 and code not in t["bonds"]:
            out.append({"severity": "Action", "check": "Bond_Info missing",
                        "detail": f"{code}: add coupon, maturity and coupons per year to Bond_Info."})
    for code, s in h["stocks"].items():
        if s["qty"] <= 0:
            continue
        p, pd, src = price_on(code, today)
        if src == "missing":
            out.append({"severity": "Warning", "check": "No price", "detail": f"{code}: no Yahoo or KSEI price; valued at 0."})
        elif src != "Yahoo":
            out.append({"severity": "Info", "check": "Fallback price",
                        "detail": f"{code}: not on Yahoo Finance; using KSEI month-end close {p:,.0f} ({pd})."})
        elif pd and (today - pd).days > 7:
            out.append({"severity": "Info", "check": "Stale price", "detail": f"{code}: last price {pd}."})
        if code not in t["stocks"]:
            out.append({"severity": "Info", "check": "Stock_Info missing", "detail": f"{code}: add its sector to Stock_Info."})
    opening_cash = [r for r in t["transactions"] if r["Asset"] == "Cash" and r["Type"] == "OPENING"]
    if opening_cash and len(t["cash_balances"]) <= 1:
        out.append({"severity": "Info", "check": "Opening cash",
                    "detail": f"Opening cash {sum(_f(r['Amount (IDR)']) for r in opening_cash):,.0f} is an estimate — "
                              "confirm it against your 30 Sep 2026 bank statements."})
    try:
        out.extend(dividend_reminders())
    except Exception:
        pass
    if not out:
        out.append({"severity": "OK", "check": "All checks passed", "detail": ""})
    return out

def get_ownership_signals() -> list[dict]:
    rows = []
    for s in get_stocks():
        o = ownership_for(s["ticker"])
        rows.append({"ticker": s["ticker"], "sector": s["sector"], "weight_pct": s["weight_pct"],
                     "market_value": s["market_value"], **o, "signal": _signal(o)})
    return sorted(rows, key=lambda r: -(r["market_value"] or 0))

def get_dividends() -> list[dict]:
    t = load_tracker()
    today = date.today()
    received = defaultdict(float)
    for r in t["transactions"]:
        if r["Type"] == "DIVIDEND":
            received[r["Code"]] += _f(r.get("Amount (IDR)"))
    rows = []
    for s in get_stocks():
        divs = _dividends(s["ticker"])
        last = max(divs) if divs else None
        ttm = sum(v for d, v in divs.items() if d > today - timedelta(days=365))
        rows.append({"ticker": s["ticker"], "sector": s["sector"], "quantity": s["quantity"], "price": s["price"],
                     "last_ex_date": last.isoformat() if last else None,
                     "last_dps": divs[last] if last else None,
                     "ttm_dps": round(ttm, 2), "yield_pct": round(ttm / s["price"] * 100, 2) if (s["price"] and ttm) else 0,
                     "expected_annual_income": round(ttm * s["quantity"]),
                     "received_since_start": round(received.get(s["ticker"], 0)),
                     "payments_per_year": sum(1 for d in divs if d > today - timedelta(days=365))})
    return sorted(rows, key=lambda r: -r["expected_annual_income"])

def dividend_reminders() -> list[dict]:
    """Ex-dates since the start date for stocks held on that date, with no DIVIDEND logged afterwards."""
    t = load_tracker()
    today, start = date.today(), t["start"]
    out = []
    for code in sorted({r["Code"] for r in t["transactions"] if r["Asset"] == "Stock"}):
        for ex, dps in sorted(_dividends(code).items()):
            if not (start < ex <= today):
                continue
            qty = holdings_on(ex - timedelta(days=1))["stocks"].get(code, {}).get("qty", 0)
            if qty <= 0:
                continue
            logged = any(r["Type"] == "DIVIDEND" and r["Code"] == code and r["Date"] >= ex for r in t["transactions"])
            if not logged:
                out.append({"severity": "Action", "check": "Dividend to log",
                            "detail": f"{code} went ex-dividend on {ex}: IDR {dps:,.2f}/share × {qty:,.0f} ≈ "
                                      f"{dps * qty:,.0f} gross. Add a DIVIDEND row (net amount) when it is paid."})
    return out
