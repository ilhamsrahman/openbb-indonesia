"""Portfolio — Sector Exposure — Stock market value, cost and P/L by sector."""

from core.portfolio import reports

WIDGET_ID = "portfolio_sectors"
ORDER = 140

WIDGET = {'name': 'Portfolio — Sector Exposure',
 'description': 'Stock market value, cost and P/L by sector.',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/sectors',
 'data': {'table': {'showAll': True,
                    'columnsDefs': [{'field': 'sector',
                                     'headerName': 'Sector',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'market_value',
                                     'headerName': 'Market Value',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'cost',
                                     'headerName': 'Cost',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'pnl',
                                     'headerName': 'P/L',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'return_pct',
                                     'headerName': 'Return %',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'weight_pct',
                                     'headerName': 'Weight %',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'}],
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'groupedBar'}}},
 'gridData': {'w': 10, 'h': 12},
 'params': []}


def get():
    return reports.get_sectors()
