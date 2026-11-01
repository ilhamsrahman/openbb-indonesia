"""Portfolio — Monthly Returns

Monthly return (NAV method) vs IHSG, month-end value, income received and net deposits.
"""

from core.portfolio import reports

WIDGET_ID = "portfolio_monthly"
ORDER = 180

WIDGET = {'name': 'Portfolio — Monthly Returns',
 'description': 'Monthly return (NAV method) vs IHSG, month-end value, income received and net deposits.',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/monthly',
 'data': {'table': {'showAll': True,
                    'columnsDefs': [{'field': 'month',
                                     'headerName': 'Month',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'portfolio_pct',
                                     'headerName': 'Portfolio %',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'benchmark_pct',
                                     'headerName': 'IHSG %',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'end_value',
                                     'headerName': 'End Value',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'income_received',
                                     'headerName': 'Income Received',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'net_deposits',
                                     'headerName': 'Net Deposits',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'status',
                                     'headerName': 'Status',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text'},
                                    {'field': 'end_date',
                                     'headerName': 'End Date',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text',
                                     'hide': True}],
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'groupedColumn'}}},
 'gridData': {'w': 10, 'h': 12},
 'params': []}


def get():
    return reports.get_monthly_returns()
