"""Portfolio Rebalancing

Current vs target allocation (targets from the Settings sheet). Gap > 0 = amount to add.
"""

from core.portfolio import reports

WIDGET_ID = "portfolio_rebalance"
ORDER = 120

WIDGET = {'name': 'Portfolio Rebalancing',
 'description': 'Current vs target allocation (targets from the Settings sheet). Gap > 0 = amount to add.',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/rebalance',
 'data': {'table': {'showAll': True,
                    'columnsDefs': [{'field': 'bucket',
                                     'headerName': 'Bucket',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'current_pct',
                                     'headerName': 'Current %',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'target_pct',
                                     'headerName': 'Target %',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'current_value',
                                     'headerName': 'Current Value',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'target_value',
                                     'headerName': 'Target Value',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'gap_value',
                                     'headerName': 'Gap (IDR)',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'}],
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'groupedColumn'}}},
 'gridData': {'w': 10, 'h': 12},
 'params': []}


def get():
    return reports.get_rebalance()
