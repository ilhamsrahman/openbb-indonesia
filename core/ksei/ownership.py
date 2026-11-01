"""KSEI Balancepos (holding composition) readers: ownership by local/foreign and investor type."""
import csv
from pathlib import Path
from typing import Optional

from core.paths import KSEI_MONTHLY

CATEGORY_LABELS = {
    "IS": "Insurance",
    "CP": "Corporate",
    "PF": "Pension Fund",
    "IB": "Bank",
    "ID": "Individual",
    "MF": "Mutual Fund",
    "SC": "Securities Company",
    "FD": "Foundation",
    "OT": "Other",
}

DATA_DIR = KSEI_MONTHLY

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _latest_file() -> Path:
    files = sorted(DATA_DIR.glob("Balancepos*.txt"))
    if not files:
        raise FileNotFoundError(f"No Balancepos files found in {DATA_DIR}")
    return files[-1]


def _file_for_date(date_str: str) -> Path:
    # date_str expected as YYYYMM, e.g. "202608"
    path = DATA_DIR / f"Balancepos{date_str}.txt"
    if not path.exists():  # also accept BalanceposYYYYMMDD.txt
        matches = sorted(DATA_DIR.glob(f"Balancepos{date_str}*.txt"))
        path = matches[-1] if matches else path
    if not path.exists():
        raise FileNotFoundError(f"No file for date {date_str} at {path}")
    return path


def list_available_dates() -> list[dict]:
    """Return dropdown options for every Balancepos file present, newest first."""
    files = sorted(DATA_DIR.glob("Balancepos*.txt"), reverse=True)
    options = []
    for f in files:
        date_str = f.stem.replace("Balancepos", "")[:6]  # accepts YYYYMM or YYYYMMDD names  # e.g. "202608"
        if len(date_str) != 6:
            continue
        year, month = date_str[:4], date_str[4:6]
        label = f"{MONTH_NAMES[int(month) - 1]} {year}"
        options.append({"label": label, "value": date_str})
    return options


def get_ownership_breakdown(symbol: str, date: Optional[str] = None) -> list[dict]:
    file_path = _file_for_date(date) if date else _latest_file()
    symbol = symbol.upper()

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="|")
        next(reader)  # skip header
        for row in reader:
            if len(row) < 25:
                continue
            if row[1].upper() == symbol:
                local_vals = row[5:14]
                foreign_vals = row[15:24]
                codes = list(CATEGORY_LABELS.keys())
                return [
                    {
                        "category": CATEGORY_LABELS[code],
                        "code": code,
                        "local": float(local_v or 0),
                        "foreign": float(foreign_v or 0),
                        "total": float(local_v or 0) + float(foreign_v or 0),
                    }
                    for code, local_v, foreign_v in zip(codes, local_vals, foreign_vals)
                ]

    raise ValueError(f"Symbol '{symbol}' not found in {file_path.name}")




def get_ownership_trend(symbol: str) -> list[dict]:
    """Scan every monthly file and return local/foreign totals for one symbol, oldest to newest."""
    symbol = symbol.upper()
    files = sorted(DATA_DIR.glob("Balancepos*.txt"))  # ascending = chronological
    results = []

    for f in files:
        date_str = f.stem.replace("Balancepos", "")[:6]  # accepts YYYYMM or YYYYMMDD names
        if len(date_str) != 6:
            continue

        with open(f, "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter="|")
            next(reader)  # skip header
            for row in reader:
                if len(row) < 25:
                    continue
                if row[1].upper() == symbol:
                    year, month = date_str[:4], date_str[4:6]
                    label = f"{MONTH_NAMES[int(month) - 1][:3]} {year}"  # e.g. "Aug 2026"
                    results.append({
                        "date": date_str,
                        "label": label,
                        "local": float(row[14] or 0),    # Local Total column
                        "foreign": float(row[24] or 0),  # Foreign Total column
                    })
                    break  # found it in this file, move to the next month

    if not results:
        raise ValueError(f"Symbol '{symbol}' not found in any monthly file")
    return results



def get_market_foreign_flow(instrument_type: str = "EQUITY") -> list[dict]:
    """Aggregate local/foreign holdings across the whole market, per month, for one instrument type."""
    files = sorted(DATA_DIR.glob("Balancepos*.txt"))  # ascending = chronological
    instrument_type = instrument_type.strip().upper()
    results = []

    for f in files:
        date_str = f.stem.replace("Balancepos", "")[:6]  # accepts YYYYMM or YYYYMMDD names
        if len(date_str) != 6:
            continue

        local_sum = 0.0
        foreign_sum = 0.0

        with open(f, "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter="|")
            next(reader)  # skip header
            for row in reader:
                if len(row) < 25:
                    continue
                if row[2].strip().upper() != instrument_type:
                    continue
                try:
                    local_sum += float(row[14] or 0)
                    foreign_sum += float(row[24] or 0)
                except ValueError:
                    continue

        year, month = date_str[:4], date_str[4:6]
        label = f"{MONTH_NAMES[int(month) - 1][:3]} {year}"
        total = local_sum + foreign_sum
        foreign_pct = round((foreign_sum / total * 100), 2) if total else 0.0

        results.append({
            "date": date_str,
            "label": label,
            "local_total": local_sum,
            "foreign_total": foreign_sum,
            "foreign_pct": foreign_pct,
        })

    if not results:
        raise ValueError(f"No data found for instrument type '{instrument_type}'")
    return results


def get_category_trend(symbol: str) -> list[dict]:
    """Monthly trend of Local+Foreign combined holdings, broken out by all 9 investor categories, for one stock."""
    symbol = symbol.upper()
    files = sorted(DATA_DIR.glob("Balancepos*.txt"))  # ascending = chronological
    codes = list(CATEGORY_LABELS.keys())
    results = []

    for f in files:
        date_str = f.stem.replace("Balancepos", "")[:6]  # accepts YYYYMM or YYYYMMDD names
        if len(date_str) != 6:
            continue

        with open(f, "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter="|")
            next(reader)  # skip header
            for row in reader:
                if len(row) < 25:
                    continue
                if row[1].upper() == symbol:
                    local_vals = row[5:14]
                    foreign_vals = row[15:24]
                    year, month = date_str[:4], date_str[4:6]
                    label = f"{MONTH_NAMES[int(month) - 1][:3]} {year}"

                    entry = {"date": date_str, "label": label}
                    for code, local_v, foreign_v in zip(codes, local_vals, foreign_vals):
                        entry[CATEGORY_LABELS[code]] = float(local_v or 0) + float(foreign_v or 0)
                    results.append(entry)
                    break  # found it, move to next month

    if not results:
        raise ValueError(f"Symbol '{symbol}' not found in any monthly file")
    return results


def get_foreign_ownership_metric(symbol: str) -> dict:
    """Latest foreign ownership % for a stock, with month-over-month delta in percentage points."""
    symbol = symbol.upper()
    files = sorted(DATA_DIR.glob("Balancepos*.txt"))  # ascending
    if not files:
        raise FileNotFoundError(f"No data files found in {DATA_DIR}")

    def pct_for_file(file_path: Path) -> Optional[float]:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="|")
            next(reader)
            for row in reader:
                if len(row) < 25:
                    continue
                if row[1].upper() == symbol:
                    local_total = float(row[14] or 0)
                    foreign_total = float(row[24] or 0)
                    total = local_total + foreign_total
                    return (foreign_total / total * 100) if total else 0.0
        return None

    latest_pct = pct_for_file(files[-1])
    if latest_pct is None:
        raise ValueError(f"Symbol '{symbol}' not found in {files[-1].name}")

    delta = 0.0
    if len(files) >= 2:
        prev_pct = pct_for_file(files[-2])
        if prev_pct is not None:
            delta = round(latest_pct - prev_pct, 2)

    return {
        "label": f"{symbol} Foreign Ownership",
        "value": f"{latest_pct:.1f}%",
        "delta": str(delta),
    }





