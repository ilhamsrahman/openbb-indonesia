"""Portfolio — Bond Maturity Ladder — Face value maturing each year, by bond type."""

from core.portfolio import reports

WIDGET_ID = "portfolio_maturity_ladder"
ORDER = 160

WIDGET = {'name': 'Portfolio — Bond Maturity Ladder',
 'description': 'Face value maturing each year, by bond type.',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/maturity-ladder',
 'data': {'table': {'showAll': True,
                    'columnsDefs': [{'field': 'year',
                                     'headerName': 'Year',
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
    return reports.get_maturity_ladder()
