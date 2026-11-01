"""IDX Foreign Ownership %

Latest foreign ownership percentage for an IDX stock, with month-over-month change in percentage
points.
"""

from core.ksei import ownership

WIDGET_ID = "indonesian_foreign_pct"
ORDER = 60

WIDGET = {'name': 'IDX Foreign Ownership %',
 'description': 'Latest foreign ownership percentage for an IDX stock, with month-over-month change in '
                'percentage points.',
 'category': 'equity',
 'type': 'metric',
 'endpoint': '/indonesia/foreign-pct',
 'gridData': {'w': 4, 'h': 5},
 'params': [{'paramName': 'symbol', 'type': 'text', 'value': 'BBCA', 'label': 'Symbol', 'show': True}]}


def get(symbol: str):
    return ownership.get_foreign_ownership_metric(symbol)
