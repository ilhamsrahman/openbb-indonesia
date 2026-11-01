"""IDX Ownership Trend — Monthly local vs foreign ownership trend for an IDX stock (KSEI balance position)."""

from core.ksei import ownership

WIDGET_ID = "indonesian_ownership_trend"
ORDER = 30

WIDGET = {'name': 'IDX Ownership Trend',
 'description': 'Monthly local vs foreign ownership trend for an IDX stock (KSEI balance position).',
 'category': 'equity',
 'type': 'table',
 'endpoint': '/indonesia/ownership-trend',
 'data': {'table': {'showAll': True,
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'groupedColumn'},
                    'columnsDefs': [{'field': 'label',
                                     'headerName': 'Month',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'local',
                                     'headerName': 'Local Holdings',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'foreign',
                                     'headerName': 'Foreign Holdings',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'date',
                                     'headerName': 'Date',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text',
                                     'hide': True}]}},
 'gridData': {'w': 12, 'h': 14},
 'params': [{'paramName': 'symbol', 'type': 'text', 'value': 'BBCA', 'label': 'Symbol', 'show': True}]}


def get(symbol: str):
    return ownership.get_ownership_trend(symbol)
