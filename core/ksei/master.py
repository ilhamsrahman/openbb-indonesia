"""Indonesian bond & debt-instrument data from KSEI files.

Joins two monthly KSEI files on `Code`:
  - Data_raw/StatisEfek/StatisEfekYYYYMMDD.txt    (Master Securities: coupon, maturity, issuer, ISIN ...)
  - Data_raw/Balancepos/BalanceposYYYYMM.txt       (Holding Composition: holdings by investor type)

Use from Python:
    from core.ksei.master import load_bonds, list_months
    rows = load_bonds("202608")                      # list of dicts, one per bond
    rows = load_bonds("202608", types={"GOVERNMENT BOND", "SBSN"})

Export CSVs (one per month) to Data_raw/Bonds/ with scripts/export_bonds.py.
"""

import csv
from datetime import date
from pathlib import Path
from typing import Optional

from core.paths import BONDS_DIR as OUT_DIR, KSEI_MASTER as MASTER_DIR, KSEI_MONTHLY as BALANCE_DIR

# Debt instrument types to include (as written in the KSEI files)
BOND_TYPES = {
    "GOVERNMENT BOND",                      # FR, ORI, VR ...
    "SBSN",                                 # government sukuk: PBS, IFR, SR ...
    "SPN",                                  # treasury bills (discount)
    "CORPORATE BOND",
    "SUKUK",                                # corporate sukuk
    "TERM NOTES",
    "NEGOTIABLE CERTIFICATE OF DEPOSIT",
    "EBA",                                  # asset-backed securities
    "PERPETUAL BONDS",
    "COMMERCIAL PAPER",
    "BANK INDONESIA RUPIAH SECURITIES (SRBI)",
    "BANK INDONESIA SUKUK (SUKBI)",
    "BANK INDONESIA FLOATING RATE NOTE (BI-FRN)",
    "Bank Indonesia Foreign Currency Securities (SVBI)",
    "Bank Indonesia Foreign Currency Sukuk (SUVBI)",
}
GOVERNMENT_TYPES = {"GOVERNMENT BOND", "SBSN", "SPN"}

CATEGORIES = {
    "IS": "Insurance", "CP": "Corporate", "PF": "Pension Fund", "IB": "Bank",
    "ID": "Individual", "MF": "Mutual Fund", "SC": "Securities Company",
    "FD": "Foundation", "OT": "Other",
}
_MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


# ---------- helpers ----------
def _parse_date(s: str) -> Optional[date]:
    """'31-AUG-2026' -> date(2026, 8, 31); '' -> None."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        d, m, y = s.split("-")
        return date(int(y), _MONTHS[m.upper()[:3]], int(d))
    except (ValueError, KeyError):
        return None


def _num(s: str) -> Optional[float]:
    s = (s or "").strip().replace(",", "")
    try:
        return float(s) if s else None
    except ValueError:
        return None


def _read_pipe_file(path: Path) -> list[dict]:
    """Read a KSEI pipe file, stitching rows broken by line breaks inside a field."""
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        lines = f.read().splitlines()
    header = lines[0].split("|")
    n = len(header)
    rows, buf = [], ""
    for line in lines[1:]:
        buf = f"{buf} {line}" if buf else line
        parts = buf.split("|")
        if len(parts) < n:
            continue            # row continues on the next line
        rows.append(dict(zip(header, (p.strip() for p in parts[:n]))))
        buf = ""
    return rows


# ---------- file discovery ----------
def list_months() -> list[str]:
    """YYYYMM months that have a master file, newest first."""
    return sorted({p.stem.replace("StatisEfek", "")[:6] for p in MASTER_DIR.glob("StatisEfek*.txt")},
                  reverse=True)


def _master_file(yyyymm: str) -> Path:
    files = sorted(MASTER_DIR.glob(f"StatisEfek{yyyymm}*.txt"))
    if not files:
        raise FileNotFoundError(f"No master file for {yyyymm} in {MASTER_DIR}")
    return files[-1]


# ---------- loaders ----------
def load_master(yyyymm: Optional[str] = None) -> list[dict]:
    """All securities in the KSEI master file for a month (raw columns)."""
    return _read_pipe_file(_master_file(yyyymm or list_months()[0]))


def load_holdings(yyyymm: str) -> dict[str, dict]:
    """Balancepos holdings by code for a month ({} if the file is missing)."""
    path = BALANCE_DIR / f"Balancepos{yyyymm}.txt"
    if not path.exists():
        return {}
    out = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="|")
        next(reader)
        for r in reader:
            if len(r) < 25:
                continue
            code = r[1].strip()
            rec = {"bp_sec_num": _num(r[3])}
            for i, k in enumerate(CATEGORIES):
                rec[f"local_{k}"] = _num(r[5 + i])
                rec[f"foreign_{k}"] = _num(r[15 + i])
            rec["local_total"] = _num(r[14])
            rec["foreign_total"] = _num(r[24])
            out[code] = rec
    return out


def load_bonds(yyyymm: Optional[str] = None, types: Optional[set] = None) -> list[dict]:
    """One row per bond: master details + derived fields + Balancepos holdings."""
    yyyymm = yyyymm or list_months()[0]
    types = types or BOND_TYPES
    master = load_master(yyyymm)
    holdings = load_holdings(yyyymm)

    rows = []
    for m in master:
        if m.get("Type") not in types:
            continue
        as_of = _parse_date(m["Date"])
        maturity = _parse_date(m["Maturity Date"])
        outstanding = _num(m["Current Amt"]) or _num(m["Num. of Sec"])
        row = {
            "as_of": as_of.isoformat() if as_of else None,
            "code": m["Code"],
            "type": m["Type"],
            "segment": "Government" if m["Type"] in GOVERNMENT_TYPES
                       else "Bank Indonesia" if "BANK INDONESIA" in m["Type"].upper()
                       else "Corporate",
            "description": m["Description"],
            "issuer": m["Issuer"],
            "isin": m["Isin Code"],
            "sector": m["Sector"],
            "status": m["Status"],
            "exchange": m["Stock Exchange"],
            "currency": m["Currency"],
            "listing_date": (_parse_date(m["Listing Date"]) or "") and _parse_date(m["Listing Date"]).isoformat(),
            "maturity_date": maturity.isoformat() if maturity else None,
            "years_to_maturity": round((maturity - as_of).days / 365.25, 2) if maturity and as_of else None,
            "coupon_pct": _num(m["Interest"]),         # discount rate for SPN / SRBI
            "coupon_type": m["Interest Type"].upper(),
            "coupon_freq": m["Interest Freq"],
            "nominal_value": _num(m["Nominal Value"]),
            "originated_amt": _num(m["Originated Amt"]),
            "outstanding_amt": outstanding,
            "scripless_amt": _num(m["Total Scripless"]),
            "master_local_pct": _num(m["Local (%)"]),
            "master_foreign_pct": _num(m["Foreign (%)"]),
        }
        h = holdings.get(m["Code"], {})
        row.update(h)
        lt, ft = h.get("local_total"), h.get("foreign_total")
        row["foreign_pct"] = round(ft / (lt + ft) * 100, 2) if lt is not None and ft is not None and (lt + ft) else None
        rows.append(row)
    rows.sort(key=lambda r: (r["segment"], r["type"], r["maturity_date"] or "9999"))
    return rows


# ---------- CSV export ----------
def export_month(yyyymm: str) -> Path:
    rows = load_bonds(yyyymm)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"bonds_{yyyymm}.csv"
    fields = list(dict.fromkeys(k for r in rows for k in r))   # union of keys, in order
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with_h = sum(1 for r in rows if r.get("local_total") is not None)
    print(f"{path.name}: {len(rows)} bonds ({with_h} with Balancepos holdings)")
    return path


