# OpenBB Indonesia

**Indonesian capital-market data and a personal portfolio dashboard for [OpenBB Workspace](https://openbb.co).**

A custom OpenBB backend that turns public Indonesian market data — KSEI ownership files, KSEI master securities,
and IDX daily prices — into 21 interactive Workspace widgets, plus a portfolio engine that tracks a mixed
stock/bond portfolio from a simple Excel transaction log.

![Python](https://img.shields.io/badge/python-3.12%2B-blue) ![OpenBB](https://img.shields.io/badge/OpenBB-Platform%20%2B%20Workspace-black) ![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)

---

## What it does

| Area | Widgets | Data |
|---|---|---|
| **Stocks** | Daily OHLCV chart for any IDX ticker (custom OpenBB provider `indonesia`) | Yahoo Finance, cached locally |
| **Ownership (KSEI)** | Local vs foreign breakdown · ownership trend · market-wide foreign flow · 9 investor-category trend · foreign-ownership tile | KSEI *Balancepos* (monthly holding composition) |
| **Bonds** | Retail SBN yield curve (ORI / SR / ST / SBR / SWR, three months compared) · coupon trend by tenor | KSEI *StatisEfek* (master securities) |
| **Portfolio** | Summary · performance vs IHSG · allocation · rebalancing · stock & bond holdings · sector exposure · ownership signals · dividends · maturity ladder · coupon calendar · monthly returns · data checks | Your Excel tracker + the data above |

Highlights:
- **Performance done properly** — daily NAV index using the unit method, so deposits and withdrawals are never counted
  as returns; benchmarked against IHSG.
- **Market context for each holding** — foreign-ownership changes (1/3/12 months) and mutual-fund flows from KSEI,
  dividend yield from Yahoo, and each bond's coupon compared with the latest new issue of the same type and tenor.
- **Self-checking** — the dashboard flags cash that doesn't reconcile, matured bonds not yet booked, dividends to log
  and missing prices.
- **One file per widget** — each widget's Workspace definition and its endpoint live together; `widgets.json` is
  generated automatically.

> Screenshots: add a few images of your dashboards to `docs/images/` and link them here.

---

## Architecture

```
Browser ─► OpenBB Workspace (self-hosted Docker, or pro.openbb.co)
              │  reads /widgets.json, calls widget endpoints
              ▼
         run.py  ── FastAPI app from openbb-core (port 8000)
              ├─ widgets/        one file per widget: WIDGET definition + get() endpoint (auto-registered)
              ├─ core/           shared logic: KSEI readers, bond analytics, portfolio engine
              ├─ openbb_indonesia/   OpenBB provider → /api/v1/equity/price/historical?provider=indonesia
              └─ Data_raw/       local data (KSEI files, price cache, your tracker) — not in git
```

### Project layout

```
openbb-indonesia/
├── run.py                     data server (auto-registers every widget)
├── start.bat                  one-click start on Windows (Docker → Workspace → conda → server)
├── pyproject.toml             package, dependencies, provider entry point
├── openbb_indonesia/          OpenBB provider: IDX daily prices via yfinance + local CSV cache
├── core/
│   ├── paths.py               all data folders in one place
│   ├── ksei/ownership.py      Balancepos readers (ownership by local/foreign × investor type)
│   ├── ksei/master.py         StatisEfek readers + bond table (terms joined with holdings)
│   ├── bonds/retail.py        retail SBN series, coupon curve, coupon trend
│   └── portfolio/             tracker → prices / ownership → holdings → performance → reports
├── widgets/
│   ├── stocks/                stock_chart
│   ├── ksei/                  ownership_breakdown, ownership_trend, market_foreign_flow, category_trend, foreign_pct
│   ├── bonds/                 retail_yield_curve, retail_coupon_trend
│   ├── portfolio/             summary, nav, allocation, rebalance, stocks, sectors, ownership, dividends,
│   │                          bonds, maturity_ladder, coupon_calendar, monthly, checks
│   └── options.py             dropdown endpoints (report months, bond types)
├── scripts/
│   ├── bulk_download_prices.py    full price history for every KSEI-listed equity
│   ├── export_bonds.py            bond table → CSV
│   └── make_tracker_template.py   blank portfolio tracker with example rows
└── docs/                      provider guide, widget ideas
```

### Adding a widget

Create a file anywhere under `widgets/` and restart `run.py`:

```python
# widgets/ksei/my_widget.py
from core.ksei import ownership

WIDGET_ID = "my_widget"
ORDER = 999                                   # position in the widget list
WIDGET = {
    "name": "My Widget", "description": "…", "category": "equity", "type": "table",
    "endpoint": "/indonesia/my-widget",
    "params": [{"paramName": "symbol", "type": "text", "value": "BBCA", "label": "Symbol", "show": True}],
}

def get(symbol: str):                         # query parameters = function arguments
    return ownership.get_ownership_trend(symbol)
```

Delete the file to remove the widget. Rules for Workspace v7.8: every table column needs `headerName`, and every
endpoint must return 200 for its default parameters (otherwise "Validate widgets" rejects the backend).

---

## Getting started

### Requirements
- Python 3.12+ (conda or venv) and an **OpenBB Workspace**: self-hosted ([OpenBB-finance/workspace](https://github.com/OpenBB-finance/workspace),
  Docker) or the hosted app at [pro.openbb.co](https://pro.openbb.co) — both can connect to a backend on `localhost`.
- Data you download yourself (see below). KSEI and price data are not included in this repository.

### Install
```bash
git clone https://github.com/<you>/openbb-indonesia.git
cd openbb-indonesia
pip install -e .            # openbb-core, openbb-equity, yfinance, openpyxl, …
```

### Add data
| Folder | What to put there | Source |
|---|---|---|
| `Data_raw/Balancepos/` | `BalanceposYYYYMM.txt` | [KSEI — Holding Composition](https://web.ksei.co.id/archive_download/holding_composition) |
| `Data_raw/StatisEfek/` | `StatisEfekYYYYMMDD.txt` (unzipped) | [KSEI — Master Securities](https://web.ksei.co.id/archive_download/master_securities) |
| `Data_raw/Prices/` | filled automatically | `python scripts/bulk_download_prices.py` (optional, full history) |
| `Data_raw/Portfolio/` | `Portfolio_Tracker.xlsx` | `python scripts/make_tracker_template.py`, then enter your own data |

### Run
```bash
python run.py               # → http://127.0.0.1:8000  (Windows: double-click start.bat)
```
In Workspace: **Connections → Connect Backend →** `http://localhost:8000`, *Validate widgets: Yes*. Then add
widgets with **Ctrl+K**.

---

## How the numbers are produced

**KSEI files.** *Balancepos* answers "who owns it" (holdings by local/foreign × 9 investor types); *StatisEfek*
answers "what is it" (ISIN, issuer, maturity, coupon, frequency). Both are monthly and joined on `Code`.
Government-bond holdings in Balancepos are partial (most SBN settle at Bank Indonesia), so its foreign share is not
the official SBN foreign ownership; corporate bonds are complete.

**Prices.** Yahoo Finance via `yfinance` (`BBCA` → `BBCA.JK`), one CSV per stock. The first request downloads full
history; afterwards only missing days are fetched, once per server session. Codes Yahoo doesn't carry are skipped
and fall back to the KSEI month-end close.

**Retail bond curve.** KSEI has no bond prices, so the curve uses coupons of outstanding retail SBN (sold at par,
so coupon = yield at issue), interpolated at 6M…6Y. Coupons missing from KSEI are filled from
`Data_raw/Bonds/retail_coupons_manual.csv` (with sources).

**Portfolio.** The tracker is a transaction log (`BUY, SELL, COUPON, DIVIDEND, MATURITY, DEPOSIT, WITHDRAW, FEE,
TAX`, plus `OPENING` rows). Holdings are replayed at average cost; stocks are valued at Yahoo closes, retail
SR/ST/ORI/SBR at face, PBS/FR at purchase price, cash from transactions (overridden by month-end balances when
entered). Expected coupons = face × coupon ÷ frequency × (1 − tax); floating coupons = max(BI Rate + spread, floor).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Widgets empty / "Failed to fetch" | `run.py` isn't running — check its window |
| Old errors after changing a widget | Refresh the connection in Workspace (or use `localhost` instead of `127.0.0.1`) |
| `No module named …` | `pip install -e .` |
| Portfolio widgets error | Create the tracker (`scripts/make_tracker_template.py`) and close it in Excel before refreshing |
| Price download rate-limited | `python scripts/bulk_download_prices.py --sleep 3` (finished stocks are skipped) |
| `GET /apps.json` 404 in the log | Normal — optional files Workspace looks for |

---

## Disclaimer

For personal research and education. Not investment advice. Market data belongs to its providers (KSEI, Yahoo
Finance) and is not redistributed here — download it yourself under their terms.
