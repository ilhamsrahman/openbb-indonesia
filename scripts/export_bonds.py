"""Export the KSEI bond table (master securities + Balancepos holdings) to Data_raw/Bonds/bonds_YYYYMM.csv.

    python scripts/export_bonds.py            # latest month
    python scripts/export_bonds.py 202608     # one month
    python scripts/export_bonds.py all        # every month that has a master file
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # project root

from core.ksei.master import export_month, list_months  # noqa: E402

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    for ym in (list_months() if arg == "all" else [arg or list_months()[0]]):
        export_month(ym)
