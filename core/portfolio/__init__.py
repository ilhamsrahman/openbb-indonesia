"""Portfolio engine (reads Data_raw/Portfolio/Portfolio_Tracker.xlsx).

Modules, lowest to highest:
  tracker -> prices, ownership -> holdings -> performance -> reports

- Holdings are rebuilt by replaying the Transactions sheet (OPENING rows = 30 Sep 2026 start).
- Stocks: Yahoo Finance daily closes (Data_raw/Prices cache, refreshed via fetchers.get_prices);
  falls back to the latest KSEI StatisEfek closing price if Yahoo has no data (e.g. WSKT).
- Bonds: retail SR/ST/ORI/SBR at face value; PBS/FR at purchase price; coupons count as income when received.
- Cash: derived from transactions; a Cash_Balances entry overrides it from that date on
  (the gap is reported in checks).
- Performance: daily NAV index (start = 100), unit method, so DEPOSIT/WITHDRAW are not returns.
"""
