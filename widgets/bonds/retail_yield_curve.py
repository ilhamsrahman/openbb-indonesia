"""IDX Retail Bond Yield Curve

Retail government bond curve (ORI, SR, ST, SBR, SWR) at fixed tenors, comparing a selected month
with two other months (default: 1 month and 1 year earlier). Built from coupons of outstanding
bonds, linearly interpolated by years to maturity — not market yields.
"""

from typing import Optional

from core.bonds import retail

WIDGET_ID = "indonesian_retail_curve"
ORDER = 70

WIDGET = {'name': 'IDX Retail Bond Yield Curve',
 'description': 'Retail government bond curve (ORI, SR, ST, SBR, SWR) at fixed tenors, comparing a selected '
                'month with two other months (default: 1 month and 1 year earlier). Built from coupons of '
                'outstanding bonds, linearly interpolated by years to maturity — not market yields.',
 'category': 'fixed_income',
 'type': 'table',
 'endpoint': '/indonesia/retail-yield-curve',
 'data': {'table': {'showAll': True,
                    'enableCharts': True,
                    'chartView': {'enabled': True, 'chartType': 'line'},
                    'columnsDefs': [{'field': 'tenor',
                                     'headerName': 'Tenor',
                                     'chartDataType': 'category',
                                     'cellDataType': 'text'},
                                    {'field': 'selected',
                                     'headerName': 'Selected Month %',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'compare_1',
                                     'headerName': 'Compare 1 %',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'compare_2',
                                     'headerName': 'Compare 2 %',
                                     'chartDataType': 'series',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'change_1_bp',
                                     'headerName': 'Chg vs Compare 1 (bp)',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'change_2_bp',
                                     'headerName': 'Chg vs Compare 2 (bp)',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none'},
                                    {'field': 'years',
                                     'headerName': 'Years',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'number',
                                     'formatterFn': 'none',
                                     'hide': True},
                                    {'field': 'months',
                                     'headerName': 'Months',
                                     'chartDataType': 'excluded',
                                     'cellDataType': 'text',
                                     'hide': True}]}},
 'gridData': {'w': 12, 'h': 16},
 'params': [{'paramName': 'bond_type',
             'type': 'text',
             'value': 'ORI',
             'label': 'Bond Type',
             'show': True,
             'options': [{'label': 'ORI – Obligasi Negara Ritel', 'value': 'ORI'},
                         {'label': 'SR – Sukuk Ritel', 'value': 'SR'},
                         {'label': 'ST – Sukuk Tabungan', 'value': 'ST'},
                         {'label': 'SBR – Savings Bond Ritel', 'value': 'SBR'},
                         {'label': 'SWR – Sukuk Wakaf Ritel', 'value': 'SWR'}]},
            {'paramName': 'date',
             'type': 'endpoint',
             'optionsEndpoint': '/indonesia/bond-months',
             'value': '202609',
             'label': 'Selected Month',
             'show': True},
            {'paramName': 'compare_1',
             'type': 'endpoint',
             'optionsEndpoint': '/indonesia/bond-months',
             'value': '202608',
             'label': 'Compare 1',
             'show': True},
            {'paramName': 'compare_2',
             'type': 'endpoint',
             'optionsEndpoint': '/indonesia/bond-months',
             'value': '202509',
             'label': 'Compare 2',
             'show': True}]}


def get(bond_type: str = "ORI", date: Optional[str] = None,
        compare_1: Optional[str] = None, compare_2: Optional[str] = None):
    return retail.get_retail_yield_curve(bond_type, date, compare_1, compare_2)
