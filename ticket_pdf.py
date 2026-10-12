"""Original SkyAerovia PDF ticket layout; never an airline-issued boarding pass."""
from io import BytesIO
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from fares import money

ROOT=Path(__file__).resolve().parent
from city_catalog import CODES
NAVY=colors.HexColor('#071B3A'); BLUE=colors.HexColor('#145DA0'); INK=colors.HexColor('#243B53')
LIGHT=colors.HexColor('#EDF3FB'); MUTED=colors.HexColor('#526D82')


def ticket_pdf(ticket):
    output=BytesIO(); c=canvas.Canvas(output,pagesize=(842,595))
    c.setTitle('SkyAerovia demo ticket - '+ticket['reference']); c.setAuthor('SkyAerovia')
    f=ticket['flight']; q=ticket['pricing']; cabin=ticket['cabin']
    def text(x,y,value,size=11,bold=False,color=INK):
        c.setFillColor(color);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,str(value))
    def fitted(x,y,value,width,size=13,bold=False,color=INK):
        font='Helvetica-Bold' if bold else 'Helvetica'
        while c.stringWidth(str(value),font,size)>width and size>6:size-=0.5
        text(x,y,value,size,bold,color)
    def right(x,y,value,size=11,bold=False,color=INK):
        c.setFillColor(color);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawRightString(x,y,str(value))
    c.setFillColor(LIGHT);c.rect(0,0,842,595,fill=1,stroke=0)
    c.setFillColor(colors.white);c.setStrokeColor(colors.HexColor('#D6E1ED'));c.roundRect(25,37,792,531,16,fill=1,stroke=1)
    c.setFillColor(NAVY);c.roundRect(25,480,792,88,16,fill=1,stroke=0);c.rect(25,480,792,40,fill=1,stroke=0)
    logo=ROOT/'assets/logo.jpg'
    if logo.exists():c.drawImage(str(logo),41,493,width=105,height=62,preserveAspectRatio=True,mask='auto')
    text(164,527,'SkyAerovia',28,True,colors.white);text(166,505,'Your way through the sky',11,False,colors.HexColor('#D2E6FA'))
    right(794,531,'DEMO FLIGHT TICKET',14,True,colors.white);right(794,507,cabin.upper(),11,True,colors.HexColor('#D2E6FA'))
    c.setFillColor(colors.HexColor('#FFF3DE') if ticket['status']=='confirmed' else colors.HexColor('#FDEAEA'))
    c.roundRect(44,442,752,24,6,fill=1,stroke=0)
    text(56,450,'SIMULATED RESERVATION - NOT VALID FOR TRAVEL',9,True)
    right(782,450,ticket['status'].upper(),10,True,color=BLUE if ticket['status']=='confirmed' else colors.HexColor('#AA2833'))
    text(46,415,'FROM',9,True,MUTED);text(318,415,'TO',9,True,MUTED)
    text(46,370,CODES.get(f['from'],f['from'][:3].upper()),37,True,NAVY)
    text(318,370,CODES.get(f['to'],f['to'][:3].upper()),37,True,NAVY)
    text(47,350,f['from'],13);text(319,350,f['to'],13)
    c.setStrokeColor(BLUE);c.setLineWidth(2);c.line(174,384,280,384);c.line(280,384,271,390);c.line(280,384,271,378)
    text(46,320,'AIRLINE / FLIGHT',9,True,MUTED);fitted(46,302,f['airline'],244,13,True)
    fitted(46,286,f['id'],244,10)
    text(318,320,'TRAVEL DATE',9,True,MUTED);text(318,302,f['date'],13,True)
    text(318,282,f'{f["departure"]} - {f["arrival"]} IST',12)
    if f.get("arrival_date",f["date"]) != f["date"]:text(318,267,"Arrival: "+f["arrival_date"],8,False,MUTED)
    c.setStrokeColor(colors.HexColor('#CCDAE8'));c.setDash(3,4);c.line(591,269,591,424);c.setDash()
    text(611,415,'BOOKING REFERENCE',9,True,MUTED)
    # Keep the human-readable reference separate from its QR, with no external URL.
    fitted(611,396,ticket['reference'],183,10,True,NAVY)
    text(611,379,'Save this ID for cancellation',9,False,MUTED)
    qr=QrCodeWidget(ticket['reference']);bounds=qr.getBounds();size=90
    drawing=Drawing(size,size,transform=[size/(bounds[2]-bounds[0]),0,0,size/(bounds[3]-bounds[1]),0,0]);drawing.add(qr)
    renderPDF.draw(drawing,c,666,279)
    text(616,266,'QR contains this demo reference',8,False,MUTED)
    text(46,259,'PASSENGER',9,True,MUTED);text(406,259,'CLASS',9,True,MUTED);text(548,259,'SEAT',9,True,MUTED)
    for i,name in enumerate(ticket['passenger_names']):
        y=239-i*19
        fitted(46,y,name,340,11);text(406,y,cabin,10)
        text(548,y,ticket['seats'][i] if i<len(ticket['seats']) else 'Unassigned',10,True)
    text(611,246,'Demo seat assignments',9,True,MUTED)
    text(611,229,'No airport gate or check-in',8,False,MUTED)
    text(611,216,'has been issued.',8,False,MUTED)
    c.setFillColor(LIGHT);c.roundRect(44,53,752,66,8,fill=1,stroke=0)
    text(58,98,f'Cabin fare ({ticket["passengers"]} passenger(s))',9,False,MUTED)
    text(58,80,money(q['subtotal_paise']),13,True)
    gst_label=f'GST ({q["gst_percent"]}%)' if q['version']==2 else 'GST not recorded'
    text(257,98,gst_label,9,False,MUTED);text(257,80,money(q['gst_paise']),13,True)
    text(430,98,'Other fees (not modelled)',9,False,MUTED);text(430,80,money(q['other_fees_paise']),13,True)
    right(781,98,'DEMO TOTAL',9,True,BLUE);right(781,78,money(q['total_paise']),20,True,NAVY)
    text(46,132,'Save this reference to find or cancel your demo reservation in SkyAerovia.',8,False,MUTED)
    text(30,20,'Tax estimate for current domestic demo fares. Not a tax invoice. No payment was taken.',8,False,MUTED)
    c.showPage();c.save();return output.getvalue()
