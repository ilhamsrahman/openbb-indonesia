"""Create a blank Portfolio_Tracker.xlsx with example rows (made-up data).

    python scripts/make_tracker_template.py                     # -> Data_raw/Portfolio/Portfolio_Tracker.xlsx
    python scripts/make_tracker_template.py path/to/file.xlsx   # custom location

Refuses to overwrite an existing file.
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # project root

import openpyxl  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402
from openpyxl.worksheet.table import Table, TableStyleInfo  # noqa: E402

from core.paths import TRACKER  # noqa: E402

START = dt.datetime(2026, 9, 30)
HDR = (Font(name="Arial", size=10, bold=True, color="FFFFFFFF"), PatternFill("solid", fgColor="FF1F4E78"))
INPUT = Font(name="Arial", size=10, color="FF0000FF")

SHEETS = {
    "Transactions": (["Date", "Type", "Asset", "Code", "Account", "Quantity", "Price", "Amount (IDR)", "Note"],
                     [[START, "OPENING", "Cash", None, "Bank A", None, None, 500_000_000, "Example: starting cash"],
                      [START, "OPENING", "Stock", "BBCA", "Broker", 10_000, 7_500, 75_000_000, "Example: shares at average cost"],
                      [START, "OPENING", "Bond", "SR025T5", "Bank A", 100_000_000, 100, 100_000_000, "Example: bond, price as % of face"],
                      [dt.datetime(2026, 10, 10), "COUPON", "Bond", "SR025T5", "Bank A", None, None, 517_500, "Example: net coupon"]],
                     [12, 11, 8, 11, 12, 16, 11, 17, 50], ["dd mmm yyyy", None, None, None, None, "#,##0", "#,##0.00", "#,##0", None]),
    "Cash_Balances": (["Date", "Account", "Balance (IDR)", "Note"],
                      [[START, "Bank A", 500_000_000, "Actual month-end balance"]],
                      [12, 14, 18, 50], ["dd mmm yyyy", None, "#,##0", None]),
    "Stock_Info": (["Ticker", "Sector", "IDX Code", "Tag", "Note"],
                   [["BBCA", "Financials", "G111", "Core", ""]], [10, 28, 10, 10, 40], [None] * 5),
    "Bond_Info": (["Code", "Type", "Maturity", "Coupon", "Rate Type", "Spread", "Floor", "Coupons per Year", "Source"],
                  [["SR025T5", "SR", dt.datetime(2031, 9, 10), 0.069, "Fixed", None, None, 12, "KSEI master securities"]],
                  [11, 8, 13, 9, 10, 9, 9, 10, 30], [None, None, "dd mmm yyyy", "0.000%", None, "0.00%", "0.00%", "0", None]),
    "Settings": (["Setting", "Value", "Note"],
                 [["Start date", START, "First date of tracking (NAV = 100)"],
                  ["Target equity %", 0.30, "Allocation target"], ["Target fixed income %", 0.70, "Bonds + cash"],
                  ["Target return p.a.", 0.10, "Blended return target"],
                  ["BI Rate", 0.0575, "Reference rate for floating ST/SBR coupons"],
                  ["Coupon tax", 0.10, "Final tax on SBN coupons"], ["Money market yield", 0.058, "Assumed yield on cash"],
                  ["Benchmark", "^JKSE", "Yahoo Finance ticker (IHSG)"]],
                 [24, 14, 50], [None, None, None]),
}


def main(path: Path) -> None:
    if path.exists():
        sys.exit(f"{path} already exists - not overwriting.")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, (headers, rows, widths, fmts) in SHEETS.items():
        ws = wb.create_sheet(name)
        ws.append(headers)
        for c in ws[1]:
            c.font, c.fill = HDR
            c.alignment = Alignment(horizontal="center", wrap_text=True)
        for r in rows:
            ws.append(r)
        for row in ws.iter_rows(min_row=2):
            for i, c in enumerate(row):
                c.font = INPUT
                if fmts[i]:
                    c.number_format = fmts[i]
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
        table = Table(displayName=f"tbl{name.replace('_', '')}",
                      ref=f"A1:{openpyxl.utils.get_column_letter(len(headers))}{ws.max_row}")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
        ws.add_table(table)
        ws.freeze_panes = "A2"
    st = wb["Settings"]
    for r, f in zip(range(2, 10), ["dd mmm yyyy", "0.0%", "0.0%", "0.0%", "0.00%", "0.0%", "0.00%", None]):
        if f:
            st[f"B{r}"].number_format = f
    tx = wb["Transactions"]
    dv = DataValidation(type="list", formula1='"OPENING,BUY,SELL,COUPON,DIVIDEND,MATURITY,DEPOSIT,WITHDRAW,FEE,TAX"')
    tx.add_data_validation(dv)
    dv.add("B2:B5000")
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    print(f"Created {path} - replace the example rows with your own data.")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else TRACKER)
