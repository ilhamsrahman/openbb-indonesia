"""Indonesian Stock Chart — Live historical daily prices for IDX stocks."""

WIDGET_ID = "indonesian_historical_price"
ORDER = 10

WIDGET = {'name': 'Indonesian Stock Chart',
 'description': 'Live historical daily prices for IDX stocks.',
 'category': 'equity',
 'type': 'table',
 'endpoint': '/api/v1/equity/price/historical',
 'data': {'dataKey': 'results'},
 'gridData': {'w': 8, 'h': 12},
 'params': [{'paramName': 'symbol', 'type': 'text', 'value': 'BBCA', 'label': 'Symbol', 'show': True},
            {'paramName': 'provider',
             'type': 'text',
             'value': 'indonesia',
             'label': 'Provider',
             'show': True}]}

# Served by the OpenBB API itself (provider 'indonesia' in openbb_indonesia/), so there is no get() here.
