import os
import tempfile

from reportlab.pdfgen import canvas #@UnresolvedImport
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.paragraph import Paragraph

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings

from project.staff.views import staff_only
from models import Inventory

def ellipsize(s, l):
    if len(s) > l:
        return s[:l] + '...'
    return s


def _draw_tyvek(p, inventory):
    p.line(15, 245, 345, 245)
    p.line(15, 188, 345, 188)
    p.line(15, 115, 345, 115)

    p.setFontSize(12)
    p.drawString(26, 290, 'DC-%0.3d' % inventory.dropship.id)
    p.drawString(295, 290, str(inventory.item.id))

    if len(inventory.item.name) > 55:
        p.setFont('Helvetica-Bold', 8)
    else:
        p.setFont('Helvetica-Bold', 10)
    p.drawString(26, 260, ellipsize(inventory.item.name, 75))

    p.setFont('Helvetica-Bold', 10)
    p.drawString( 26, 224, 'Console:')
    p.drawString(120, 224, inventory.item.category.name)
    p.drawString( 26, 200, 'Rating:')
    p.drawString(120, 200, inventory.item.rating.title)

    p.drawImage(inventory.item.rating.image.path, 211, 197, width=20, height=30)

    p.setFont('Helvetica', 10)
    styles = getSampleStyleSheet()
    para = Paragraph(ellipsize(inventory.item.description, 305), styles['Normal'])
    para.wrap(290, 10000)
    i = 0
    ll = para.breakLines(290)
    for l in ll.lines:
        if ll.kind == 0:
            p.drawString(25, 170 - i, ' '.join(l[1]))
        else:
            p.drawString(25, 170 - i, ' '.join([x.text for x in l.words]))
        i += 10

    from code128 import Code128
    bar = Code128()
    image = bar.getImage(inventory.barcode, 50, "png")
    _fd, n = tempfile.mkstemp()
    image.save(n, "PNG")
    p.drawImage(n, 196, 60, width=140, height=50)

    p.setFont('Helvetica-Bold', 10)
    p.drawString(236, 50, inventory.barcode)

    p.drawImage(
        os.path.join(settings.STATIC_ROOT, "img/bw-logo.png"),
        26, 80, width=87, height=22)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(25, 70, 'PO Box 6487')
    p.drawString(25, 58, 'Delray Beach, FL 33482-9901')
    p.showPage()


@staff_only
def inventory_tyvek(request, inventory_id):
    inventory = get_object_or_404(Inventory, id=inventory_id)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'filename=inventory-tyvek.pdf'

    p = canvas.Canvas(response, pagesize=(360, 360))

    _draw_tyvek(p, inventory)

    p.save()
    return response


def print_tyveks(request, inventories):
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'filename=inventory-tyvek.pdf'

    p = canvas.Canvas(response, pagesize=(360, 360))

    for inventory in inventories:
        _draw_tyvek(p, inventory)

    p.save()
    return response
