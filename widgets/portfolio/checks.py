"""Portfolio — Data Checks

Things to fix or confirm in Portfolio_Tracker.xlsx (cash gaps, matured bonds, missing prices).
"""

from core.portfolio import reports

WIDGET_ID = "portfolio_checks"
ORDER = 190

WIDGET = {'name': 'Portfolio — Data Checks',
 'description': 'Things to fix or confirm in Portfolio_Tracker.xlsx (cash gaps, matured bonds, missing '
                'prices).',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/checks',
 'data': {'table': {'showAll': True,
                    'columnsDefs': [{'field': 'severity',
                                     'headerName': 'Severity',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'check',
                                     'headerName': 'Check',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text'},
                                    {'field': 'detail',
                                     'headerName': 'Detail',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text'}]}},
 'gridData': {'w': 20, 'h': 8},
 'params': []}


def get():
    return reports.get_checks()
