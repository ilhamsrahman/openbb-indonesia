"""Portfolio — Dividends

Dividend history from Yahoo Finance for each stock you hold: last ex-date, trailing-12-month
dividend per share, yield, expected yearly income (gross) and dividends logged since the start date.
"""

from core.portfolio import reports

WIDGET_ID = "portfolio_dividends"
ORDER = 210

WIDGET = {'name': 'Portfolio — Dividends',
 'description': 'Dividend history from Yahoo Finance for each stock you hold: last ex-date, '
                'trailing-12-month dividend per share, yield, expected yearly income (gross) and dividends '
                'logged since the start date.',
 'category': 'portfolio',
 'type': 'table',
 'endpoint': '/portfolio/dividends',
 'data': {'table': {'showAll': True,
                    'enableCharts': True,
                    'chartView': {'enabled': False, 'chartType': 'bar'},
                    'columnsDefs': [{'field': 'ticker',
                                     'headerName': 'Ticker',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text',
                                     'pinned': 'left'},
                                    {'field': 'expected_annual_income',
                                     'headerName': 'Expected Income / yr',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'yield_pct',
                                     'headerName': 'Yield % (TTM)',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'ttm_dps',
                                     'headerName': 'Dividend / Share (TTM)',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'last_ex_date',
                                     'headerName': 'Last Ex-Date',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text'},
                                    {'field': 'last_dps',
                                     'headerName': 'Last Dividend / Share',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'payments_per_year',
                                     'headerName': 'Payments (12M)',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'received_since_start',
                                     'headerName': 'Logged Since Start',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'quantity',
                                     'headerName': 'Shares',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'price',
                                     'headerName': 'Price',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'sector',
                                     'headerName': 'Sector',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text'}]}},
 'gridData': {'w': 20, 'h': 12},
 'params': []}


def get():
    return reports.get_dividends()
