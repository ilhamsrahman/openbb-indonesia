"""IDX Investor Category Trend

Monthly holdings by investor category (Insurance, Corporate, Pension Fund, etc.) for an IDX stock.
"""

from core.ksei import ownership

WIDGET_ID = "indonesian_category_trend"
ORDER = 50

WIDGET = {'name': 'IDX Investor Category Trend',
 'description': 'Monthly holdings by investor category (Insurance, Corporate, Pension Fund, etc.) for an IDX '
                'stock.',
 'category': 'equity',
 'type': 'table',
 'endpoint': '/indonesia/category-trend',
 'data': {'table': {'showAll': True,
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'stackedArea'},
                    'columnsDefs': [{'field': 'label',
                                     'headerName': 'Month',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'Insurance',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Insurance'},
                                    {'field': 'Corporate',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Corporate'},
                                    {'field': 'Pension Fund',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Pension Fund'},
                                    {'field': 'Bank',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Bank'},
                                    {'field': 'Individual',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Individual'},
                                    {'field': 'Mutual Fund',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Mutual Fund'},
                                    {'field': 'Securities Company',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Securities Company'},
                                    {'field': 'Foundation',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Foundation'},
                                    {'field': 'Other',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int',
                                     'headerName': 'Other'},
                                    {'field': 'date',
                                     'headerName': 'Date',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text',
                                     'hide': True}]}},
 'gridData': {'w': 12, 'h': 14},
 'params': [{'paramName': 'symbol', 'type': 'text', 'value': 'BBCA', 'label': 'Symbol', 'show': True}]}


def get(symbol: str):
    return ownership.get_category_trend(symbol)
