"""Portfolio Performance vs IHSG

Daily NAV index (30 Sep 2026 = 100, deposits/withdrawals excluded) vs IHSG rebased to 100.
"""

from core.portfolio import performance

WIDGET_ID = "portfolio_nav"
ORDER = 100

WIDGET = {'name': 'Portfolio Performance vs IHSG',
 'description': 'Daily NAV index (30 Sep 2026 = 100, deposits/withdrawals excluded) vs IHSG rebased to 100.',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/nav',
 'data': {'table': {'showAll': True,
                    'columnsDefs': [{'field': 'date',
                                     'headerName': 'Date',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'nav',
                                     'headerName': 'Portfolio (index)',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'benchmark',
                                     'headerName': 'IHSG (index)',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'total_value',
                                     'headerName': 'Total Value',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'stocks',
                                     'headerName': 'Stocks',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'bonds',
                                     'headerName': 'Bonds',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'cash',
                                     'headerName': 'Cash',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'external_flow',
                                     'headerName': 'Deposits / Withdrawals',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'}],
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'line'}}},
 'gridData': {'w': 20, 'h': 14},
 'params': []}


def get():
    return performance.nav_series()
