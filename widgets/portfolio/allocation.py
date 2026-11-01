"""Portfolio Allocation

Current value by asset class (stocks at Yahoo daily close; retail bonds at face, PBS at purchase
price; cash).
"""

from core.portfolio import reports

WIDGET_ID = "portfolio_allocation"
ORDER = 110

WIDGET = {'name': 'Portfolio Allocation',
 'description': 'Current value by asset class (stocks at Yahoo daily close; retail bonds at face, PBS at '
                'purchase price; cash).',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/allocation',
 'data': {'table': {'showAll': True,
                    'columnsDefs': [{'field': 'asset',
                                     'headerName': 'Asset Class',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'value',
                                     'headerName': 'Value (IDR)',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'weight_pct',
                                     'headerName': 'Weight %',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'}],
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'donut'}}},
 'gridData': {'w': 10, 'h': 12},
 'params': []}


def get():
    return reports.get_allocation()
