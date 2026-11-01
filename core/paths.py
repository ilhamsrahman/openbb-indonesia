"""Every data folder in one place. All paths are relative to the project root."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "Data_raw"

KSEI_MONTHLY = DATA_RAW / "Balancepos"       # BalanceposYYYYMM.txt  (holding composition)
KSEI_MASTER = DATA_RAW / "StatisEfek"        # StatisEfekYYYYMMDD.txt (master securities)
PRICE_DIR = DATA_RAW / "Prices"              # <CODE>.csv daily prices, _dividends/, _failed.txt
BONDS_DIR = DATA_RAW / "Bonds"               # bonds_YYYYMM.csv exports, retail_coupons_manual.csv
PORTFOLIO_DIR = DATA_RAW / "Portfolio"       # personal files (never committed)
TRACKER = PORTFOLIO_DIR / "Portfolio_Tracker.xlsx"
