"""IDX Retail Bond Coupon Trend

Coupon set at issuance for each retail government bond series, by tenor (2Y–6Y), oldest to newest.
Source: KSEI master securities + offering announcements.
"""

from core.bonds import retail

WIDGET_ID = "indonesian_retail_coupon_trend"
ORDER = 80

WIDGET = {'name': 'IDX Retail Bond Coupon Trend',
 'description': 'Coupon set at issuance for each retail government bond series, by tenor (2Y–6Y), oldest to '
                'newest. Source: KSEI master securities + offering announcements.',
 'category': 'fixed_income',
 'type': 'table',
 'endpoint': '/indonesia/retail-coupon-trend',
 'data': {'table': {'showAll': True,
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'line'},
                    'columnsDefs': [{'field': 'label',
                                     'headerName': 'Series (issued)',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': '2Y',
                                     'headerName': '2Y',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': '3Y',
                                     'headerName': '3Y',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': '4Y',
                                     'headerName': '4Y',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': '5Y',
                                     'headerName': '5Y',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': '6Y',
                                     'headerName': '6Y',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'series',
                                     'headerName': 'Series',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text',
                                     'hide': True},
                                    {'field': 'issue_date',
                                     'headerName': 'Issue Date',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text',
                                     'hide': True}]}},
 'gridData': {'w': 12, 'h': 14},
 'params': [{'paramName': 'bond_type',
             'type': 'text',
             'value': 'ORI',
             'label': 'Bond Type',
             'show': True,
             'options': [{'label': 'ORI – Obligasi Negara Ritel', 'value': 'ORI'},
                         {'label': 'SR – Sukuk Ritel', 'value': 'SR'},
                         {'label': 'ST – Sukuk Tabungan', 'value': 'ST'},
                         {'label': 'SBR – Savings Bond Ritel', 'value': 'SBR'},
                         {'label': 'SWR – Sukuk Wakaf Ritel', 'value': 'SWR'}]}]}


def get(bond_type: str = "ORI"):
    return retail.get_retail_coupon_trend(bond_type)
