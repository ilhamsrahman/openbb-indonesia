"""IDX Ownership Breakdown

Local vs foreign ownership by investor category (KSEI monthly balance position).
"""

from typing import Optional

from core.ksei import ownership

WIDGET_ID = "indonesian_ownership_breakdown"
ORDER = 20

WIDGET = {'name': 'IDX Ownership Breakdown',
 'description': 'Local vs foreign ownership by investor category (KSEI monthly balance position).',
 'category': 'equity',
 'type': 'table',
 'endpoint': '/indonesia/ownership',
 'gridData': {'w': 8, 'h': 12},
 'params': [{'paramName': 'symbol', 'type': 'text', 'value': 'BBCA', 'label': 'Symbol', 'show': True},
            {'paramName': 'date',
             'type': 'endpoint',
             'optionsEndpoint': '/indonesia/dates',
             'value': '202609',
             'label': 'Report Month',
             'show': True}]}


def get(symbol: str, date: Optional[str] = None):
    return ownership.get_ownership_breakdown(symbol, date)
