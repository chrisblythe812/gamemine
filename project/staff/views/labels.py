from datetime import datetime
from os import path
from logging import debug  #@UnusedImport

from reportlab.pdfgen import canvas  #@UnresolvedImport
from reportlab.lib.units import inch  #@UnresolvedImport

from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.context import RequestContext

from project.staff.views import staff_only
from project.rent.models import RentOrder
from project.buy_orders.models import PackSlip
from project.trade.models import TradeOrderItem


@staff_only
def rent(request):
    """
    Returns mail label PDFs for given ``RentOrders`` ids.
    """
    type = request.REQUEST.get('t', 'both')
    ids = request.REQUEST.get('ids', '')
    if not ids:
        return HttpResponseNotFound()

    response = HttpResponse(mimetype='application/pdf')
#    response['Content-Disposition'] = 'attachment; filename=labels.pdf'
    response['Content-Disposition'] = 'filename=labels.pdf'

    p = canvas.Canvas(response, pagesize=(540, 162))

    def draw_image(filename):
        img = path.join(settings.MEDIA_ROOT, str(filename))
        p.drawImage(img, 0, 0, width=7.5 * inch, height=2.25 * inch)
        p.showPage()

    for id in ids.split(','):
        if not id:
            continue
        order = RentOrder.objects.get(id=int(id))
        if type == 'mailing' or type == 'both':
            r, m = order.request_outgoing_mail_label()
            if not r:
                return HttpResponse('Endicia is unable to process request right now (%s). Please try again later.' % (m if m else '--'))
            draw_image(order.outgoing_mail_label)
        if type == 'return' or type == 'both':
            r, m = order.request_incoming_mail_label()
            if not r:
                return HttpResponse('Endicia is unable to process request right now (%s). Please try again later.' % (m if m else '--'))
            draw_image(order.incoming_mail_label)

    p.save()
    return response


@staff_only
def buy(request):
    ids = request.REQUEST.get('ids', '')
    if not ids:
        return HttpResponseNotFound()

    response = HttpResponse(mimetype='application/pdf')
#    response['Content-Disposition'] = 'attachment; filename=labels.pdf'
    response['Content-Disposition'] = 'filename=labels.pdf'

    p = canvas.Canvas(response, pagesize=(288, 432))

    def draw_image(filename):
        img = path.join(settings.MEDIA_ROOT, str(filename))
        p.drawImage(img, 0, 0, width=4 * inch, height=6 * inch)
        p.showPage()

    for id in ids.split(','):
        if not id:
            continue
        slip = PackSlip.objects.get(id=int(id))
        r, m = slip.request_mail_label()
        if not r:
            return HttpResponse('Endicia is unable to process request right now (%s). Please try again later.' % (m if m else '--'))
#        slip.mark_as_shipped()
        draw_image(slip.mail_label)

    p.save()
    return response


@staff_only
def buy_pack_slips(request):
    from ho import pisa #@UnresolvedImport

    ids = request.REQUEST.get('ids', '')
    if not ids:
        return HttpResponseNotFound()

    pack_slips = []
    for id in ids.split(','):
        if not id:
            continue
        pack_slips.append(get_object_or_404(PackSlip, id=id))

    src = render_to_string('staff/labels/pack_slips.html', {
            'pack_slips': pack_slips,
            'today': datetime.today(),
        }, RequestContext(request))

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'filename=packslip.pdf'

    def link_callback(uri, rel):
        import os
        return os.path.join(settings.MEDIA_ROOT, uri.replace(settings.STATIC_URL, ""))

    pisa.CreatePDF(src, response, show_error_as_pdf=True, link_callback=link_callback)
    return response


@staff_only
def trade(request):
    ids = request.REQUEST.get('ids', '')
    if not ids:
        return HttpResponseNotFound()

    response = HttpResponse(mimetype='application/pdf')
#    response['Content-Disposition'] = 'attachment; filename=labels.pdf'
    response['Content-Disposition'] = 'filename=labels.pdf'

    p = canvas.Canvas(response, pagesize=(288, 432))

    def draw_image(filename):
        img = path.join(settings.MEDIA_ROOT, str(filename))
        p.drawImage(img, 0, 0, width=4 * inch, height=6 * inch)
        p.showPage()

    for id in ids.split(','):
        if not id:
            continue
        item = get_object_or_404(TradeOrderItem, id=int(id), declined=True)
        r, m = item.request_returning_label()
        if not r:
            return HttpResponse('Endicia is unable to process request right now (%s). Please try again later.' % (m if m else '--'))
#        slip.mark_as_shipped()
        draw_image(item.returning_mail_label)

    p.save()
    return response
