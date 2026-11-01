"""IDX Market Foreign Flow

Market-wide local vs foreign holdings trend by instrument type (KSEI balance position).
"""

from core.ksei import ownership

WIDGET_ID = "indonesian_market_foreign_flow"
ORDER = 40

WIDGET = {'name': 'IDX Market Foreign Flow',
 'description': 'Market-wide local vs foreign holdings trend by instrument type (KSEI balance position).',
 'category': 'equity',
 'type': 'table',
 'endpoint': '/indonesia/market-foreign-flow',
 'data': {'table': {'showAll': True,
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'line'},
                    'columnsDefs': [{'field': 'label',
                                     'headerName': 'Month',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'local_total',
                                     'headerName': 'Local Total',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'foreign_total',
                                     'headerName': 'Foreign Total',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'int'},
                                    {'field': 'foreign_pct',
                                     'headerName': 'Foreign %',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'date',
                                     'headerName': 'Date',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text',
                                     'hide': True}]}},
 'gridData': {'w': 12, 'h': 14},
 'params': [{'paramName': 'instrument_type',
             'type': 'text',
             'value': 'EQUITY',
             'label': 'Instrument Type',
             'show': True,
             'options': [{'label': 'Equity', 'value': 'EQUITY'},
                         {'label': 'Structured Warrant', 'value': 'STRUCTURED WARRANT'},
                         {'label': 'SRBI (BI Rupiah Securities)',
                          'value': 'BANK INDONESIA RUPIAH SECURITIES (SRBI)'},
                         {'label': 'Perpetual Bonds', 'value': 'PERPETUAL BONDS'},
                         {'label': 'Electronic Gold Receipts', 'value': 'ELECTRONIC GOLD RECEIPTS'}]}]}


def get(instrument_type: str = "EQUITY"):
    return ownership.get_market_foreign_flow(instrument_type)
