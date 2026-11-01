"""Portfolio Summary

Headline numbers: total value, return since start vs IHSG, month to date, equity allocation,
expected bond income.
"""

from core.portfolio import reports

WIDGET_ID = "portfolio_summary"
ORDER = 90

WIDGET = {'name': 'Portfolio Summary',
 'description': 'Headline numbers: total value, return since start vs IHSG, month to date, equity '
                'allocation, expected bond income.',
 'category': 'portfolio',
 'type': 'metric',
 'endpoint': '/portfolio/summary',
 'gridData': {'w': 20, 'h': 5},
 'params': []}


def get():
    return reports.get_summary()
