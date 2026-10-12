"""Illustrative cabin fares and GST for the current domestic demo routes."""
from decimal import Decimal, ROUND_HALF_UP

CABINS = {
    'Economy': {'multiplier': Decimal('1.00'), 'gst': 5, 'rows': range(12,36), 'letters': 'ABCDEF'},
    'Premium Economy': {'multiplier': Decimal('1.45'), 'gst': 18, 'rows': range(6,11), 'letters': 'ACDF'},
    'Business': {'multiplier': Decimal('2.20'), 'gst': 18, 'rows': range(1,5), 'letters': 'ACDF'},
}
TAX_SOURCE = 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2163560&lang=2&reg=48'


def fare_quote(base_fare, passengers, cabin):
    if cabin not in CABINS:
        raise ValueError('Choose Economy, Premium Economy or Business.')
    if isinstance(base_fare,bool) or not isinstance(base_fare,int) or base_fare<=0:
        raise ValueError('The selected flight has an invalid base fare.')
    if isinstance(passengers,bool) or not isinstance(passengers,int) or not 1<=passengers<=6:
        raise ValueError('Choose between 1 and 6 passengers.')
    rule=CABINS[cabin]
    per_person=int((Decimal(base_fare)*rule['multiplier']*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    subtotal=per_person*passengers
    gst=int((Decimal(subtotal)*Decimal(rule['gst'])/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    return {'version':2,'cabin':cabin,'passengers':passengers,'base_per_person_paise':per_person,
            'subtotal_paise':subtotal,'gst_percent':rule['gst'],'gst_paise':gst,
            'other_fees_paise':0,'total_paise':subtotal+gst,'tax_source':TAX_SOURCE,
            'note':'Illustrative cabin fares and tax estimate. Other charges are not modelled. Not a tax invoice.'}


def cabin_seats(cabin):
    if cabin not in CABINS:
        raise ValueError('Choose a valid travel class.')
    rule=CABINS[cabin]
    return [f'{row}{letter}' for row in rule['rows'] for letter in rule['letters']]


def seat_label(seat):
    kind='Window' if seat[-1] in 'AF' else 'Aisle' if seat[-1] in 'CD' else 'Middle'
    return f'{seat} · {kind}'


def money(paise):
    return f'INR {paise/100:,.2f}'
