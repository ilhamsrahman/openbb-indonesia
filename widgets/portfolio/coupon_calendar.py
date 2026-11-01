"""Portfolio — Coupon Income Calendar

Expected net coupon income per month for the next 12 months (after coupon tax).
"""

from core.portfolio import reports

WIDGET_ID = "portfolio_coupon_calendar"
ORDER = 170

WIDGET = {'name': 'Portfolio — Coupon Income Calendar',
 'description': 'Expected net coupon income per month for the next 12 months (after coupon tax).',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/coupon-calendar',
 'data': {'table': {'showAll': True,
                    'columnsDefs': [{'field': 'month',
                                     'headerName': 'Month',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'SR',
                                     'headerName': 'SR',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'ST',
                                     'headerName': 'ST',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'PBS',
                                     'headerName': 'PBS',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'ORI',
                                     'headerName': 'ORI',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'SBR',
                                     'headerName': 'SBR',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'FR',
                                     'headerName': 'FR',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'total',
                                     'headerName': 'Total',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'}],
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'stackedColumn'}}},
 'gridData': {'w': 10, 'h': 12},
 'params': []}


def get():
    return reports.get_coupon_calendar()
