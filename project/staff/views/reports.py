import decimal
import operator
from logging import debug #@UnusedImport
from datetime import datetime, timedelta
from pprint import pformat

from django.db import connection, transaction
from django.shortcuts import redirect, get_object_or_404
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django import forms
from django.contrib.auth.models import User
from django.contrib.localflavor.us.us_states import STATE_CHOICES
from django.db.models.aggregates import Count, Sum
from django.contrib.sites.models import Site

from django_snippets.utils.datetime.date_utils import inc_months
from django_snippets.views import simple_view
from django_snippets.views.json_response import JsonResponse
from project.buy_orders.models import BuyOrderStatus, BuyOrderItem, BuyOrder

from project.catalog.models.items import Item
from project.rent.models import RentalPlan, RentOrder, MemberRentalPlan,\
    RentalPlanStatus, MemberRentalPlanHistory
from project.members.models import Campaign, BillingCard, BillingHistory, TransactionStatus, TransactionType
from project.inventory.models import Dropship, INVENTORY_STATUS_STR, Inventory,\
    InventoryStatus, DistributorItem
from project.catalog.models.categories import Category
from project.trade.models import TradeOrder, TradeOrderItem
from decimal import Decimal

def write_xls(file_name, sheet_name, headings, data, callback, heading_xf, data_xfs):
    import xlwt
    book = xlwt.Workbook()
    sheet = book.add_sheet(sheet_name)
    rowx = 0
    for colx, value in enumerate(headings):
        sheet.write(rowx, colx, value, heading_xf)
    sheet.set_panes_frozen(True) # frozen headings instead of split panes
    sheet.set_horz_split_pos(rowx+1) # in general, freeze after last heading row
    sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
    for row in data:
        rowx += 1
        for colx, value in enumerate(callback(row)):
            sheet.write(rowx, colx, value, data_xfs[colx])
    book.save(file_name)


def make_excel(qs, kinds, header, callback, title='Report'):
    import xlwt
    ezxf = xlwt.easyxf
    response = HttpResponse(mimetype="application/vnd.ms-excel")
    response['Content-Disposition'] = 'attachment; filename=report.xls'
    heading_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center')
    kind_to_xf_map = {
        'date': ezxf(num_format_str='mm-dd-yyyy'),
        'int': ezxf(num_format_str='#,##0'),
        'money': ezxf(num_format_str='$#,##0.00'),
        'price': ezxf(num_format_str='#0.00'),
        'float': ezxf(num_format_str='#0.00'),
        'text': ezxf(),
        }
    data_xfs = [kind_to_xf_map[k] for k in kinds]
    write_xls(response, title, header, qs, callback, heading_xf, data_xfs)
    return response



@transaction.commit_on_success
def purchase_forecast(request, **kwargs):
    try:
        enu = int(request.POST.get('enu', 0))
        show_cs = request.POST.get('show_cs', False) == 'True'
    except:
        enu = 0
        show_cs = False
    q = '''
select
    ci.id item_id,
    coalesce((select cast(sum(cast(a.date_returned as date) - cast(a.date_shipped as date) + 1) as double precision) / count(a.user_id)
        from rent_rentorder a
        where a.item_id = ci.id and a.date_returned is not null and a.date_shipped is not null), 0) ard,
    (select count(1)
        from inventory_inventory
        where inventory_inventory.item_id = ci.id and inventory_inventory.status = 1 /* Rented */) rented,
    (select count(distinct a.user_id)
        from rent_rentorder a
        where a.item_id = ci.id and a.status in (0, 1) /* Pending, Shipped */) cur_1,
    (select count(distinct a.user_id)
        from rent_rentlist a
        inner join rent_memberrentalplan b on a.user_id = b.user_id
        inner join auth_user c on c.id = a.user_id
        where a.item_id = ci.id and a."order" < 4 and a.user_id is not null and b.status = 1 and c.is_active = 't') cur_2,
    (select count(1)
        from inventory_inventory a
        where a.item_id = ci.id and a.status in (0, 3) /* Available, InStock */) available,
    (select count(1)
        from rent_rentlist a
        inner join rent_memberrentalplan b on a.user_id = b.user_id
        inner join auth_user c on c.id = a.user_id
        where a.item_id = ci.id and a."order" = 1 and b.status = 1 and c.is_active = 't') p1,
    (select count(1)
        from rent_rentlist a
        inner join rent_memberrentalplan b on a.user_id = b.user_id
        inner join auth_user c on c.id = a.user_id
        where a.item_id = ci.id and a."order" = 2 and b.status = 1 and c.is_active = 't') p2,
    (select count(1)
        from rent_rentlist a
        inner join rent_memberrentalplan b on a.user_id = b.user_id
        inner join auth_user c on c.id = a.user_id
        where a.item_id = ci.id and a."order" = 3 and b.status = 1 and c.is_active = 't') p3,
    (select count(1)
        from rent_rentlist a
        inner join rent_memberrentalplan b on a.user_id = b.user_id
        inner join auth_user c on c.id = a.user_id
        where a.item_id = ci.id and a."order" < 4 and b.status = 1 and c.is_active = 't') p_total,
    (select count(1)
        from buy_orders_buyorderitem a
        inner join buy_orders_buyorder b on b.id = a.order_id
        where a.item_id = ci.id
        and a.status in (1, 2, 3, 4) /* Checkout, Pending, PreOrder, Prepared */) pb,
    (select count(1)
        from buy_orders_buyorderitem a
        inner join buy_orders_buyorder b on a.order_id = b.id
        inner join auth_user c on c.id = b.user_id
        where a.item_id = ci.id and a.status = 1 and c.is_active = 't') buy,
    (select count(distinct b.user_id)
        from buy_orders_buyorderitem a
        inner join buy_orders_buyorder b on b.id = a.order_id
        where a.item_id = ci.id
        and a.status in (1, 2, 3, 4) /* Checkout, Pending, PreOrder, Prepared */) cub,
    (select count(1)
        from rent_rentlist a
        inner join members_profile b on b.user_id = a.user_id
        where a.item_id = ci.id
        and a."order" < 4
        and b.dropship_id = 1) u_in_fl,
    (select count(1)
        from rent_rentlist a
        inner join members_profile b on b.user_id = a.user_id
        where a.item_id = ci.id
        and a."order" < 4
        and b.dropship_id = 2) u_in_nj,
    (select count(1)
        from rent_rentlist a
        inner join members_profile b on b.user_id = a.user_id
        where a.item_id = ci.id
        and a."order" < 4
        and b.dropship_id = 3) u_in_nv,
    (select count(distinct c.user_id)
        from buy_orders_buyorderitem a
        inner join buy_orders_buyorder c on a.order_id = c.id
        inner join members_profile b on b.user_id = c.user_id
        where a.item_id = ci.id
        and a.status in (1, 2, 3, 4) /* Checkout, Pending, PreOrder, Prepared */
        and b.dropship_id = 1) bu_in_fl,
    (select count(distinct c.user_id)
        from buy_orders_buyorderitem a
        inner join buy_orders_buyorder c on a.order_id = c.id
        inner join members_profile b on b.user_id = c.user_id
        where a.item_id = ci.id
        and a.status in (1, 2, 3, 4) /* Checkout, Pending, PreOrder, Prepared */
        and b.dropship_id = 2) bu_in_nj,
    (select count(distinct c.user_id)
        from buy_orders_buyorderitem a
        inner join buy_orders_buyorder c on a.order_id = c.id
        inner join members_profile b on b.user_id = c.user_id
        where a.item_id = ci.id
        and a.status in (1, 2, 3, 4) /* Checkout, Pending, PreOrder, Prepared */
        and b.dropship_id = 3) bu_in_nv
from
    catalog_item ci
where
    ci.rent_status <> 6 /* NotRentable */
    and ci.release_date ''' + ('<=' if not show_cs else '>') + ''' %s
    and ci.release_date <= %s
    and ci.id in (
    select rl.item_id
        from rent_rentlist rl
        inner join rent_memberrentalplan rp on (rl.user_id = rp.user_id)
        where
            rl."order" < 4
            and rp.status = 1 /* Active */
    union
    select boi.item_id
        from buy_orders_buyorderitem boi
        inner join buy_orders_buyorder bo on bo.id = boi.order_id
        where boi.status in (1, 2, 3, 4) /* Checkout, Pending, PreOrder, Prepared */
    )
group by
    ci.id
order by
    p_total desc, cub desc
    '''
    cursor = connection.cursor() #@UndefinedVariable
    cursor.execute(q, [datetime.today(), datetime.today() + timedelta(30)])
    field_names = map(lambda x: x[0], cursor.description)
    rent_total = 0
    ards = []
    report = []
    for row in cursor.fetchall():
        r = dict(zip(field_names, row))
        r['item'] = Item.objects.get(id=r['item_id'])
        r['tot'] = r['rented'] + r['available']
        r['cur'] = r['cur_1'] + r['cur_2']
        rent_total += r['p_total'] + r['pb']
        if r['ard'] > 0:
            ards.append(r['ard'])
        r['u_in_fl'] += r['bu_in_fl']
        r['u_in_nj'] += r['bu_in_nj']
        r['u_in_nv'] += r['bu_in_nv']
        report.append(r)

    to_order_total = 0
    for r in report:
        r['weight'] = float(r['p_total'] + r['pb']) / rent_total if rent_total else 0
        r['enr'] = int(round(r['weight'] * enu))
        r['cutot'] = r['cur'] + r['enr'] + r['cub']
#        r['to_order'] = int(float(r['cutot'] * (r['p_total'] + r['rented'] + r['pb'])) / (r['cur'] + r['cub'])) + r['buy']
#        r['to_order'] = r['cutot'] - r['tot']
        r['to_order'] = r['p_total'] + r['pb'] + r['enr'] + r['cub'] - r['tot']
        if r['to_order'] < 0: r['to_order'] = 0

    report = filter(lambda x: x['to_order'], report)
    report.sort(lambda a, b: cmp(b['to_order'], a['to_order']))
    report = report[:25]

    for r in report:
        user_amount = r['u_in_fl'] + r['u_in_nj'] + r['u_in_nv']
        to_order = r['to_order']
        if user_amount:
            r['to_order_fl'] = to_order * r['u_in_fl'] / user_amount + r['cub']
            r['to_order_nj'] = to_order * r['u_in_nj'] / user_amount
            r['to_order_nv'] = to_order * r['u_in_nv'] / user_amount
        else:
            r['to_order_fl'] = 0
            r['to_order_nj'] = 0
            r['to_order_nv'] = 0
        r['to_order'] = sum([r['to_order_fl'], r['to_order_nj'], r['to_order_nv']])
        to_order_total += r['to_order']

    report.sort(lambda a, b: cmp(b['to_order'], a['to_order']))

    if to_order_total:
        for r in report:
            r['p_order_fl'] = float(r['to_order_fl'] * 100) / to_order_total
            r['p_order_nj'] = float(r['to_order_nj'] * 100) / to_order_total
            r['p_order_nv'] = float(r['to_order_nv'] * 100) / to_order_total
            r['p_order'] = float(r['to_order'] * 100) / to_order_total

    ard = sum(ards) / len(ards) if ards else 0

    return {
        'title': 'Reports: Purchase Forecast',
        'ard': ard,
        'enu': enu,
        'show_cs': show_cs,
        'report': report,
    }, None


def soft_launch(request, **kwargs):
    class FilterForm(forms.Form):
        d0 = forms.DateField(required=False, label='Date From')
        d1 = forms.DateField(required=False, label='Date To')

    cursor = connection.cursor() #@UndefinedVariable

    d_x = datetime(2010, 11, 1)

    data = request.GET.copy()
    data['d0'] = data.get('d0', d_x)
    form = FilterForm(data)
    if form.is_valid():
        d0 = form.cleaned_data.get('d0')
        d1 = form.cleaned_data.get('d1')
        if not d0 and not d1:
            d0 = d_x
    else:
        d0 = d_x
        d1 = None

    def get_date_filter_str(fname, d0, d1):
        r = []
        if d0:
            r.append("%s >= '%s'" % (fname, d0.strftime('%Y-%m-%d')))
        if d1:
            r.append("%s < '%s'" % (fname, (d1 + timedelta(1)).strftime('%Y-%m-%d')))
        return ' and '.join(r)

    #
    # member sign-ups
    #
    q = '''
        select
            coalesce(p.campaign_cid, '0'), count(distinct u.id)
        from
            auth_user u
            inner join members_profile p on p.user_id = u.id
        where
            ''' + get_date_filter_str('u.date_joined', d0, d1) + '''
        group by
            coalesce(p.campaign_cid, '0')
        order by
            count(1) desc
    '''
    cursor.execute(q)

    member_signups_count = 0
    member_signups = []
    for campaign_cid, count in cursor.fetchall():
        member_signups_count += count
        member_signups.append({
            'campaign': Campaign.get_title(campaign_cid),
            'cid': campaign_cid,
            'count': count,
        })

    #
    # email registrations
    #
    q = '''
        select
            coalesce(p.campaign_cid, '0'), count(distinct u.id)
        from
            auth_user u
            left outer join rent_memberrentalplan mrp on mrp.user_id = u.id
            inner join members_profile p on p.user_id = u.id
        where
            ''' + get_date_filter_str('u.date_joined', d0, d1) + '''
            and coalesce(mrp.plan, -1) = -1
        group by
            coalesce(p.campaign_cid, '0')
        order by
            count(1) desc
    '''
    cursor.execute(q)

    email_registrations_count = 0
    email_registrations_signups = {}
    for campaign_cid, count in cursor.fetchall():
        email_registrations_count += count
        email_registrations_signups[campaign_cid] = {
            'campaign': Campaign.get_title(campaign_cid),
            'cid': campaign_cid,
            'count': count,
        }

    q = '''
        select
            coalesce(campaign_cid, '0'), count(1)
        from
            subscription_subscriber
        where
            ''' + get_date_filter_str('timestamp', d0, d1) + '''
        group by
            coalesce(campaign_cid, '0')
    '''
    cursor.execute(q)

    for campaign_cid, count in cursor.fetchall():
        email_registrations_count += count
        d = email_registrations_signups.get(campaign_cid, {
            'campaign': Campaign.get_title(campaign_cid),
            'cid': campaign_cid,
            'count': 0,
        })
        d['count'] += count
        email_registrations_signups[campaign_cid] = d

    email_registrations_signups = email_registrations_signups.values()
    email_registrations_signups.sort(lambda a, b: -cmp(a['count'], b['count']))

    #
    # new registrations
    #
    q = '''
        select
            rp.plan, coalesce(p.campaign_cid, '0'), count(1)
        from
            rent_memberrentalplan rp
            inner join auth_user u on rp.user_id = u.id
            inner join members_profile p on p.user_id = u.id
        where
            ''' + get_date_filter_str('u.date_joined', d0, d1) + '''
        group by
            rp.plan, coalesce(p.campaign_cid, '0')
        order by
            rp.plan, count(1) desc
    '''
    cursor.execute(q)
    new_reqistrations = {}
    new_reqistrations_total = 0
    for plan, campaign_cid, count in cursor.fetchall():
        d = new_reqistrations.get(plan, {
            'plan': plan,
            'total': 0,
            'campaigns': [],
            'title': mark_safe('%s (%s)' % (RentalPlan.get_description(plan), RentalPlan.get_price_display(plan))),
        })
        d['total'] += count
        new_reqistrations_total += count
        d['campaigns'].append({
            'campaign': Campaign.get_title(campaign_cid),
            'cid': campaign_cid,
            'count': count,
        })
        new_reqistrations[plan] = d
    new_reqistrations = new_reqistrations.values()
    new_reqistrations.sort(lambda a, b: cmp(a['plan'], b['plan']))

    #
    # cancellations
    #
    q = '''
        select
            coalesce(p.campaign_cid, '0'), count(1)
        from
            rent_memberrentalplanhistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = u.id
        where
            ''' + get_date_filter_str('u.date_joined', d0, d1) + '''
            and h.status = 7
        group by
            coalesce(p.campaign_cid, '0');
        '''
    cursor.execute(q)
    cancellations = {}
    for campaign_cid, count in cursor.fetchall():
        cancellations[campaign_cid] = {
            'cid': campaign_cid,
            'campaign': Campaign.get_title(campaign_cid),
            'cancelled': count,
            'pending': 0,
        }
    q = '''
        select
            coalesce(p.campaign_cid, '0'), count(1)
        from
            rent_memberrentalplan r
            inner join auth_user u on u.id = r.user_id
            inner join members_profile p on p.user_id = u.id
        where
            ''' + get_date_filter_str('u.date_joined', d0, d1) + '''
            and r.status = 8
        group by
            coalesce(p.campaign_cid, '0');
        '''
    cursor.execute(q)
    for campaign_cid, count in cursor.fetchall():
        if campaign_cid in cancellations:
            c = cancellations[campaign_cid]
        else:
            c = {
                'cid': campaign_cid,
                'campaign': Campaign.get_title(campaign_cid),
                'cancelled': 0,
            }
        c['pending'] = count
    cancellations = cancellations.values()

    cancellations_total = 0
    cancellations_pending_total = 0
    for r in cancellations:
        r['total'] = r['cancelled'] + r['pending']
        cancellations_total += r['cancelled']
        cancellations_pending_total += r['pending']
    cancellations.sort(None, lambda r: -r['total'])
    cancellations_total_all = cancellations_total + cancellations_pending_total

    #
    # buy orders
    #
    q = '''
        select
            coalesce(p.campaign_cid, '0'), count(1)
        from
            buy_orders_buyorderitem i
            inner join buy_orders_buyorder o on i.order_id = o.id
            inner join members_profile p on p.user_id = o.user_id
        where
            ''' + get_date_filter_str('o.create_date', d0, d1) + '''
        group by
            coalesce(p.campaign_cid, '0')
        order by
            count(1) desc
    '''
    cursor.execute(q)
    buy_orders = []
    buy_orders_total = 0
    for campaign_cid, count in cursor.fetchall():
        buy_orders.append({
            'campaign': Campaign.get_title(campaign_cid),
            'count': count,
        })
        buy_orders_total += count

    q = '''
        select
            coalesce(p.campaign_cid, '0'), count(1)
        from
            trade_tradeorder o
            inner join members_profile p on p.user_id = o.user_id
        where
            ''' + get_date_filter_str('o.create_date', d0, d1) + '''
        group by
            coalesce(p.campaign_cid, '0')
        order by
            count(1) desc
    '''
    cursor.execute(q)
    trade_orders = []
    trade_orders_total = 0
    for campaign_cid, count in cursor.fetchall():
        trade_orders.append({
            'campaign': Campaign.get_title(campaign_cid),
            'count': count,
        })
        trade_orders_total += count

    return {
        'title': 'Reports: Soft Launch',
        'member_signups': member_signups,
        'member_signups_count': member_signups_count,
        'email_registrations_count': email_registrations_count,
        'email_registrations_signups': email_registrations_signups,
        'new_reqistrations': new_reqistrations,
        'new_reqistrations_total': new_reqistrations_total,
        'cancellations': cancellations,
        'cancellations_total': cancellations_total,
        'cancellations_pending_total': cancellations_pending_total,
        'cancellations_total_all': cancellations_total_all,
        'buy_orders': buy_orders,
        'buy_orders_total': buy_orders_total,
        'trade_orders': trade_orders,
        'trade_orders_total': trade_orders_total,
        'form': form,
        'd0': d0,
        'd1': d1,
    }, None


def sales_tax_report(request, **kwargs):
    def get_form_choices():
        try:
            d, d0 = datetime.now(), BillingHistory.objects.filter(debit__gt=0).order_by('timestamp')[0].timestamp
        except IndexError:
            return
        while d >= d0:
            yield (d.strftime('%Y%m'), d.strftime('%m/%Y'))
            d = inc_months(d, -1)

    class Form(forms.Form):
        p = forms.ChoiceField(choices=get_form_choices())

    form = Form(request.GET)
    if form.is_valid():
        d = form.cleaned_data.get('p', datetime.now().strftime('%Y%m'))
    else:
        d = datetime.now().strftime('%Y%m')
        form = Form(initial={'d': d})
    d = datetime(int(d[:4]), int(d[4:]), 1).date()
    d1 = inc_months(d, 1)

    cursor = connection.cursor() #@UndefinedVariable

    q = '''
        select
            sum(h.debit - coalesce(r.amount, 0))
        from
            members_billinghistory h
            left outer join members_refund r on h.id = r.payment_id
        where
            h.timestamp >= %s and h.timestamp < %s
            and h.status = 0
    '''
    cursor.execute(q, [d, d1])
    gross_sales =  cursor.fetchall()[0]


    q = '''
    select
        sum(h.tax)
    from
        members_billinghistory h
        left outer join members_refund r on h.id = r.payment_id
    where
        h.timestamp >= %s and h.timestamp < %s
        and h.status = 0
        and h.tax > 0
    '''
    cursor.execute(q, [d, d1])
    tax_collected = cursor.fetchall()[0][0] or '0.00'

    q = '''
    SELECT
        h.user_id, h.payment_method, h.debit - coalesce(r.amount, 0), h.tax
    from members_billinghistory h
        left outer join members_refund r on h.id = r.payment_id
    where
        h.timestamp >= %s and h.timestamp < %s
        and h.tax > 0
        and status = 0
        and r.amount is NULL
        and h.user_id is not NULL;
    '''
    tax_by_states = {}
    cursor.execute(q, [d, d1])
    for user_id, payment_method, amount, tax in cursor.fetchall():
        if amount == 0 or tax == 0:
            continue
        cn = payment_method[-4:]
        try:
            c = BillingCard.objects.get(user__id=user_id, display_number__contains=cn)
            state = c.state
        except BillingCard.DoesNotExist:
            c = BillingCard.objects.get(user__id=user_id)
        state = c.state

        t = tax_by_states.get(state, {'tax': 0.0, 'amount': 0.0})

        t['tax'] += float(tax)
        t['amount'] += float(amount)
        tax_by_states[state] = t

    for k, v in tax_by_states.items():
        tax_by_states[k]['percent'] = '%0.2f' % (100.0 * v['tax'] / v['amount'])

    return {
        'title': 'Reports: Sales Tax Report for %s' % d.strftime('%m/%Y'),
        'gross_sales':'$%s' % gross_sales,
        'tax_collected': '$%s' % tax_collected,
        'tax_by_states': tax_by_states,
        'form': form,
    }, None

def get_gross_sales(d,d1):
    '''recurring billing report'''
    cursor = connection.cursor() #@UndefinedVariable

    q = '''
        select
            sum(h.debit - coalesce(r.amount, 0))
        from
            members_billinghistory h
            left outer join members_refund r on h.id = r.payment_id
        where
            h.timestamp >= %s and h.timestamp < %s
            and h.status = 0
    '''
    cursor.execute(q, [d, d1])
    return cursor.fetchall()[0][0]

def get_new_recurring_capture(d,d1):
    cursor = connection.cursor() #@UndefinedVariable

    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 0
        group by
            h.debit
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d, d1])
    new_registrations = {}
    for plan, amount, users in cursor.fetchall():
        new_registrations[plan] = {'plan': plan,
                                   'captured_amount': amount,
                                   'captured_users': users,}
    return new_registrations

def get_new_recurring_authorize(d,d1, new_registrations):
    cursor = connection.cursor()
    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 3
            and not exists(select * from members_billinghistory h1 where h1.refered_transaction_id = h.id)
        group by
            h.debit
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d, d1])
    for plan, amount, users in cursor.fetchall():
        data = new_registrations.get(plan, {'plan': plan})
        data['authorized_amount'] = amount
        data['authorized_users'] = users
        new_registrations[plan] = data
    return new_registrations

def get_new_recurring_declined(d,d1,new_registrations):
    cursor = connection.cursor()
    """declined"""
    q = '''
        select
            h.debit, count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 1
            and not exists(select * from members_billinghistory h1 where h1.refered_transaction_id = h.id)
        group by
            h.debit, u.id
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d, d1])
    for plan, users in cursor.fetchall():
        data = new_registrations.get(plan, {'plan': plan})
        data['declined_amount'] = plan * users
        data['declined_users'] = users
        new_registrations[plan] = data
    return new_registrations

def get_new_recurring_refunded(d,d1,new_registrations):
    cursor = connection.cursor()
    """refund"""
    q = '''
            select
                h.debit, sum(r.amount), count(distinct h.user_id)
            from
                members_billinghistory h
                inner join auth_user u on u.id = h.user_id
                inner join members_profile p on p.user_id = h.user_id
                left outer join members_refund r on h.id = r.payment_id
            where
                coalesce(r.amount, 0) <> 0
                and h.type = 1
                and h.timestamp >= %s and h.timestamp < %s
                and u.date_joined >= %s and u.date_joined < %s
                and h.debit > 0 and h.debit <> 50
            group by
                h.debit
        order by
            h.debit
        '''
    cursor.execute(q, [d, d1, d, d1])
    for plan,amount, users in cursor.fetchall():
        data = new_registrations.get(plan, {'plan': plan})
        data['refunded_amount'] = amount
        data['refunded_users'] = users
        new_registrations[plan] = data
    return    new_registrations

def get_recurring_captured(d,d1):
    cursor = connection.cursor() #@UndefinedVariable

    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 0
        group by
            h.debit
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d])
    recurring_registrations = {}
    for plan, amount, users in cursor.fetchall():
        recurring_registrations[plan] = {'plan': plan,
                                         'captured_amount': amount,
                                         'captured_users': users,}
    return recurring_registrations

def get_recurring_authorize(d,d1,recurring_registrations):
    cursor = connection.cursor()
    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 3
            and not exists(select * from members_billinghistory h1 where h1.refered_transaction_id = h.id)
        group by
            h.debit, h.status
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d])
    for plan, amount, users in cursor.fetchall():
        data = recurring_registrations.get(plan, {'plan': plan})
        data['authorized_amount'] = amount
        data['authorized_users'] = users
        recurring_registrations[plan] = data
    return recurring_registrations

def get_recurring_declined(d,d1,recurring_registrations):
    cursor = connection.cursor()
    q = '''
        select
            h.debit, count(h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 1
            and not exists(select * from members_billinghistory h1 where h1.refered_transaction_id = h.id)
        group by
            h.debit, h.user_id
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d])
    for plan, users in cursor.fetchall():
        data = recurring_registrations.get(plan, {'plan': plan})
        data['declined_amount'] = plan * users
        data['declined_users'] = users
        recurring_registrations[plan] = data
    return  recurring_registrations

def get_recurring_refunded(d,d1,recurring_registrations):
    cursor = connection.cursor()
    """refund"""
    q = '''
            select
                h.debit, sum(r.amount), count(distinct h.user_id)
            from
                members_billinghistory h
                inner join auth_user u on u.id = h.user_id
                inner join members_profile p on p.user_id = h.user_id
                left outer join members_refund r on h.id = r.payment_id
            where
                coalesce(r.amount, 0) <> 0
                and h.type = 1
                and h.timestamp >= %s and h.timestamp < %s
                and u.date_joined < %s
                and h.debit > 0 and h.debit <> 50
            group by
                h.debit
        order by
            h.debit
        '''
    cursor.execute(q, [d, d1, d])
    for plan,amount, users in cursor.fetchall():
        data = recurring_registrations.get(plan, {'plan': plan})
        data['refunded_amount'] = amount
        data['refunded_users'] = users
        recurring_registrations[plan] = data
    return    recurring_registrations

def get_recurring_cancellations(d,d1,recurring_registrations):
    for mr in MemberRentalPlanHistory.objects.filter(status=RentalPlanStatus.Canceled,
                                          start_date__gte=d,
                                          finish_date__lt=d1):
        p,p1 = RentalPlan.get_prices(mr.plan)
        p = Decimal(p)
        data = recurring_registrations.get(p, {'plan': p})
        data['canceled_amount'] = data.get('canceled_amount',0) + p
        data['canceled_users'] = data.get('canceled_users',0) + 1
        recurring_registrations[p] = data
    return  recurring_registrations

def get_recurring_delinquent(d,d1,recurring_registrations):

    d0 = inc_months(d,-1)
    """recurring billing captured"""
    cursor = connection.cursor() #@UndefinedVariable

    q = '''
        select
            distinct h.user_id
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 0
    '''
    cursor.execute(q, [d0, d, d0])
    ids = []
    for user in cursor.fetchall():
        ids.append(user[0])

    q = '''
        select
            distinct h.user_id
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 0
    '''
    cursor.execute(q, [d0, d, d0, d])
    for user in cursor.fetchall():
        ids.append(user[0])

    """delinquent"""
    for mr in MemberRentalPlan.objects.filter(status=RentalPlanStatus.Delinquent, user__id__in=ids):
        p,p1 = RentalPlan.get_prices(mr.plan)
        p = Decimal(p)
        data = recurring_registrations.get(p, {'plan': p})
        data['delinquent_amount'] = data.get('delinquent_amount',0) + p
        data['delinquent_users'] = data.get('canceled_users',0) + 1
        recurring_registrations[p] = data
    return  recurring_registrations

def get_buy_revenue(d,d1):
    """BUY REVENUE"""
    cursor = connection.cursor()
    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 3
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 0
        group by h.debit;
    '''

    cursor.execute(q, [d, d1, d, d1])
    buy_transactions = {}
    for plan,amount, users in cursor.fetchall():
        buy_transactions[plan] = { 'plan': plan,
                                   'amount': amount,
                                   'users': users,}
    return buy_transactions

def get_buy_revenue_refunded(d,d1,buy_transactions):
    """BUY REVENUE"""
    cursor = connection.cursor()
    q = '''
        select
            h.debit,sum(r.amount), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) <> 0
            and h.type = 3
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 0
        group by h.debit;
    '''

    cursor.execute(q, [d, d1, d, d1])
    for plan, amount, users in cursor.fetchall():
        data = buy_transactions.get(plan, {'plan': plan})
        data['amount_refunded'] = amount
        data['users_refunded'] = users

    return buy_transactions

def calc_totals(lst):
    totals = {}
    for data in lst:
        for k, v in data.iteritems():
            totals[k] = totals.get(k, 0) + v
    return totals

from django.shortcuts import render_to_response
from django.template import RequestContext
def recurring_billing_report_2(request, **kwargs):
    def get_form_choices():
        d, d0 = datetime.now(), BillingHistory.objects.filter(debit__gt=0).order_by('timestamp')[0].timestamp
        while d >= d0:
            yield (d.strftime('%Y%m'), d.strftime('%m/%Y'))
            d = inc_months(d, -1)

    class Form(forms.Form):
        p = forms.ChoiceField(choices=get_form_choices())

    form = Form(request.GET)
    if form.is_valid():
        d = form.cleaned_data.get('p', datetime.now().strftime('%Y%m'))
    else:
        d = datetime.now().strftime('%Y%m')
        form = Form(initial={'d': d})
    d = datetime(int(d[:4]), int(d[4:]), 1).date()
    d1 = inc_months(d, 1)

    '''gross sales'''
    gross_sales = get_gross_sales(d,d1)

    '''new recurring'''
    new_registrations = get_new_recurring_capture(d, d1)
    new_registrations = get_new_recurring_authorize(d,d1,new_registrations)
    new_registrations = get_new_recurring_declined(d,d1,new_registrations)
    new_registrations = get_new_recurring_refunded(d,d1,new_registrations)

    '''recurring registrations'''
    recurring_registrations = get_recurring_captured(d, d1)
    recurring_registrations = get_recurring_authorize(d, d1,recurring_registrations)
    recurring_registrations = get_recurring_declined(d,d1,recurring_registrations)
    recurring_registrations = get_recurring_refunded(d,d1,recurring_registrations)
    recurring_registrations = get_recurring_cancellations(d,d1,recurring_registrations)
    recurring_registrations = get_recurring_delinquent(d,d1,recurring_registrations)

    new_registrations = new_registrations.values()
    new_registrations.sort(lambda a, b: cmp(a['plan'], b['plan']))
    for data in new_registrations:
        data['total'] = data.get('authorized_amount', decimal.Decimal('0.00')) + data.get('captured_amount', decimal.Decimal('0.00'))

    recurring_registrations = recurring_registrations.values()
    recurring_registrations.sort(lambda a, b: cmp(a['plan'], b['plan']))
    for data in recurring_registrations:
        data['total'] = data.get('authorized_amount', decimal.Decimal('0.00')) + data.get('captured_amount', decimal.Decimal('0.00'))

    '''buy revenue'''
    buy_transactions = get_buy_revenue(d,d1)
    buy_transactions = get_buy_revenue_refunded(d,d1,buy_transactions)
    buy_transactions = buy_transactions.values()
    buy_transactions.sort(lambda a, b: cmp(a['plan'], b['plan']))
    for data in buy_transactions:
        data['total'] = data.get('amount', decimal.Decimal('0.00')) - data.get('amount_refunded', decimal.Decimal('0.00'))

    r =RequestContext(request)
    r['gross_sales'] =  gross_sales
    r['new_registrations'] =  new_registrations
    r['new_registrations_totals'] =  calc_totals(new_registrations)
    r['recurring_registrations'] =  recurring_registrations
    r['recurring_registrations_totals'] =  calc_totals(recurring_registrations)
    r['buy_transactions'] =  buy_transactions
    r['buy_transactions_totals'] =  calc_totals(buy_transactions)
    r['form'] = form

    return render_to_response(
        'staff/reports/recurring_billing_report_2.html',
        locals(),
        context_instance=r)


def recurring_income_report(request, **kwargs):
    def get_form_choices():
        d, d0 = datetime.now(), datetime(2010, 10, 1)
        while d >= d0:
            yield (d.strftime('%Y%m'), d.strftime('%m/%Y'))
            d = inc_months(d, -1)

    class Form(forms.Form):
        p = forms.ChoiceField(choices=get_form_choices())

    form = Form(request.GET)
    if form.is_valid():
        d = form.cleaned_data.get('p', datetime.now().strftime('%Y%m'))
    else:
        d = datetime.now().strftime('%Y%m')
        form = Form(initial={'d': d})
    d = datetime(int(d[:4]), int(d[4:]), 1).date()
    d1 = inc_months(d, 1)

    cursor = connection.cursor() #@UndefinedVariable

    q = '''
    select
        sum(h.debit - coalesce(r.amount, 0))
    from
        members_billinghistory h
        left outer join members_refund r on h.id = r.payment_id
    where
        h.timestamp >= %s and h.timestamp < %s
        and h.status = 0
    '''
    cursor.execute(q, [d, d1])
    gross_sales = cursor.fetchall()[0][0]

    q = '''
    select
        sum(h.debit - coalesce(r.amount, 0))
    from
        members_billinghistory h
        left outer join members_refund r on h.id = r.payment_id
    where
        h.timestamp >= %s and h.timestamp < %s
        and h.status = 3
        and not exists(select * from members_billinghistory h2 where h2.refered_transaction_id=h.id)
    '''
    cursor.execute(q, [d, d1])
    authorized_amount = cursor.fetchall()[0][0]

    q = '''
    select
        extract(year from u.date_joined) "year",
        extract(month from u.date_joined) "month",
        sum(h.debit - coalesce(r.amount, 0)) amount
    from
        members_billinghistory h
        left outer join members_refund r on h.id = r.payment_id
        inner join auth_user u on u.id = h.user_id
    where
        h.timestamp >= %s and h.timestamp < %s
        and h.status = 0
    group by
        extract(year from u.date_joined), extract(month from u.date_joined)
    order by
        "year" desc, "month" desc
    limit 6
    '''
    cursor.execute(q, [d, d1])
    data = {}
    for year, month, amount in cursor.fetchall():
        key = int(year) * 100 + int(month)
        data[key] = dict(key=key, year=int(year), month=int(month), earned=amount)

    q = '''
    select
        extract(year from u.date_joined) "year",
        extract(month from u.date_joined) "month",
        sum(h.debit - coalesce(r.amount, 0)) amount
    from
        members_billinghistory h
        left outer join members_refund r on h.id = r.payment_id
        inner join auth_user u on u.id = h.user_id
    where
        h.timestamp >= %s and h.timestamp < %s
        and h.status = 3
        and not exists(select * from members_billinghistory h2 where h2.refered_transaction_id=h.id)
    group by
        extract(year from u.date_joined), extract(month from u.date_joined)
    order by
        "year" desc, "month" desc
    limit 6
    '''
    cursor.execute(q, [d, d1])
    for year, month, amount in cursor.fetchall():
        key = int(year) * 100 + int(month)
        if key in data:
            data[key]['authorized'] = amount
    breakdown = data.values()
    breakdown.sort(key=lambda i: -i['key'])

    return {
        'title': 'Reports: Recurring Income Report for %s' % d.strftime('%m/%Y'),
        'gross_sales': gross_sales,
        'authorized_amount': authorized_amount,
        'breakdown': breakdown,
        'form': form,
    }, None




def inventory(request, **kwargs):
    class FilterForm(forms.Form):
        dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), required=False, label='DC')
        q = forms.CharField(required=False, label='')
        status = forms.ChoiceField(choices=[('', '--------')] + list(INVENTORY_STATUS_STR), required=False)
        platform = forms.ModelChoiceField(queryset=Category.list(), required=False)
        buy_only = forms.ChoiceField(choices=[('', '--------'), (True, 'Yes'), (False, 'No')], required=False)
        cond = forms.ChoiceField(choices=[('', '--------'), ('UG', 'UG'), ('NG', 'NG')], required=False)

    form = FilterForm(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Reports/Inventory')

    qs = Inventory.objects.all()

    dc = form.cleaned_data.get('dc')
    if dc:
        qs = qs.filter(dropship=dc)

    status = form.cleaned_data.get('status')
    if status:
        status = int(status)
        if status == -1:
            qs = qs.filter(status=InventoryStatus.Available, dropship=None)
        elif status == 101:
            qs = qs.filter(status__in=[InventoryStatus.AutoUnknown, InventoryStatus.Sale])
        elif status == InventoryStatus.Available:
            qs = qs.filter(status=InventoryStatus.Available).exclude(dropship=None)
        else:
            qs = qs.filter(status=status)

    platform = form.cleaned_data.get('platform')
    if platform:
        qs = qs.filter(item__category=platform)

    buy_only= form.cleaned_data.get('buy_only', '')
    if buy_only != '':
        if buy_only == 'True':
            qs = qs.filter(buy_only=True)
        else:
            qs = qs.filter(Q(buy_only=False) | Q(buy_only=None))

    cond = form.cleaned_data.get('cond', '')
    if cond != '':
        if cond == 'NG':
            qs = qs.filter(is_new=True)
        else:
            qs = qs.filter(is_new=False)

    q = form.cleaned_data.get('q')
    if q:
        or_q = []
        for f in ['id', 'item__upc', 'item__name', 'item__short_name', 'barcode']:
            or_q.append(Q(**{f + '__icontains': q}))
        qs = qs.filter(reduce(operator.or_, or_q))

    if 'excel' in request.GET:
        DC = {
            'FL': 'Florida',
            'NV': 'Nevada',
            'NJ': 'New Jersey',
        }
        PLATFORM = {
            'PS2': 'PlayStation 2',
            'PS3': 'PlayStation 3',
            'GC': 'GameCube',
            'XBOX 360': 'Xbox 360',
            'XBOX': 'Xbox',
            'Wii': 'Nintendo Wii',
            'NDS': 'Nintendo DS',
            'PSP': 'Sony PSP',
            '3DS': 'Nintendo 3DS',
        }
        return make_excel(qs,
                          ('text', 'text', 'text', 'text', 'date', 'text', 'text'),
                          ('DC', 'UPC', 'GAME TITLE', 'PLATFORM', 'RELEASE DATE', 'BARCODE ID', 'BARCODE STATUS'),
                          lambda o: (DC[o.dropship.code] if o.dropship else '--',
                                     o.item.upc,
                                     o.item.short_name,
                                     PLATFORM[o.item.category.name],
                                     o.item.release_date,
                                     o.barcode,
                                     o.get_status_str()))

    return {
        'title': 'Reports: Inventory',
        'form': form,
        'paged_qs': qs,
    }, None, ('inventories', )


def games(request, **kwargs):
    class FilterForm(forms.Form):
        q = forms.CharField(required=False, label='')
        platform = forms.ModelChoiceField(queryset=Category.list(), required=False)

    form = FilterForm(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Reports/Games')

    qs = Item.objects.all()

    platform = form.cleaned_data.get('platform')
    if platform:
        qs = qs.filter(category=platform)

    q = form.cleaned_data.get('q')
    if q:
        or_q = []
        for f in ['upc', 'short_name', 'name']:
            or_q.append(Q(**{f + '__icontains': q}))
        qs = qs.filter(reduce(operator.or_, or_q))

    site_url = 'http://%s' % Site.objects.get_current().domain

    if 'excel' in request.GET:
        return make_excel(qs,
                          ('text', 'text', 'text', 'date', 'text'),
                          ('UPC', 'Game Title', 'Platform', 'Release Date', 'URL'),
                          lambda o: (o.upc,
                                o.name,
                                o.category.name,
                                o.release_date,
                                site_url + o.get_absolute_url()))

    return {
        'title': 'Reports: Games',
        'form': form,
        'paged_qs': qs,
        'site_url': site_url,
    }, None, ('items', )


@simple_view('staff/reports/partials/inventory_history.html')
def inventory_history(request, id):
    inventory = get_object_or_404(Inventory, id=id)
    if request.user.is_superuser:
        if 'unreconcile' in request.GET:
            inventory.mark_as_unreconciled()
            return JsonResponse({'status': 'OK'})
    rent_orders = RentOrder.objects.filter(inventory=inventory).order_by('-date_rent')
    return {
        'inventory': inventory,
        'rent_orders': rent_orders,
    }


def membership__rent_subscribers(request, **kwargs):
    class Form(forms.Form):
        state = forms.ChoiceField(choices=STATE_CHOICES, required=False)
        dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), required=False, label='Home DC')

    form = Form(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Reports/Membership/Rent-Subscribers')

    plans = MemberRentalPlan.objects.filter(status__in=[RentalPlanStatus.Active, RentalPlanStatus.Pending, RentalPlanStatus.OnHold]).order_by('-start_date').select_related()

    state = form.cleaned_data.get('state')
    if state:
        plans = plans.filter(user__profile__shipping_state=state)

    dc = form.cleaned_data.get('dc')
    if dc:
        plans = plans.filter(user__profile__dropship=dc)

    return {
        'title': 'Membership: Rent (subscribers)',
        'paged_qs': plans,
        'form': form,
    }, None, ('plans', 50, )


def membership__rent_subscribers__future_billings(request, **kwargs):
    plans = MemberRentalPlan.objects.filter(status__in=[RentalPlanStatus.Active, RentalPlanStatus.Pending], next_payment_date__gte=datetime.today(), next_payment_date__lt=datetime.today() + timedelta(30)).order_by('next_payment_date').select_related()

    return {
        'title': 'Rent (subscribers): Future Billings',
        'paged_qs': plans,
    }, None, ('plans', 50, )


def membership__rent_subscribers__no_games_on_list(request, **kwargs):
    plans = MemberRentalPlan.objects.filter(status__in=[RentalPlanStatus.Active, RentalPlanStatus.Pending]).order_by('-start_date').select_related()
    plans = plans.annotate(list_amount=Count('user__rentlist')).filter(list_amount=0)

    return {
        'title': 'Rent (subscribers): No Games On List',
        'paged_qs': plans,
    }, None, ('plans', 50, )


def membership__rent_subscribers__collections(request, **kwargs):
    plans = MemberRentalPlan.objects.filter(status__in=[RentalPlanStatus.Collection]).order_by('-start_date').select_related()

    return {
        'title': 'Rent (subscribers): Collections',
        'paged_qs': plans,
    }, None, ('plans', 50, )


def membership__rent_subscribers__top_rentals(request, **kwargs):
    items = Item.objects.filter(rent_amount__gt=0).order_by('-rent_amount')[:100]

    return {
        'title': 'Rent (subscribers): Top Rentals',
        'paged_qs': items,
    }, None, ('items', 100, )

def membership__rent_subscribers__double_speed_activation(request, **kwargs):
    users = User.objects.extra(where=['exists(select id from rent_rentorder where rent_rentorder.user_id = auth_user.id and speed_2x=\'t\')']).select_related()
    for user in users:
        user.rental_plan = MemberRentalPlan.get_current_plan(user)
    return {
        'title': '2xSPEED Activation',
        'paged_qs': users,
    }, None, ('users', 100, )

def membership__trade_ins(request, **kwargs):
    class Form(forms.Form):
        state = forms.ChoiceField(choices=STATE_CHOICES, required=False)
        dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), required=False, label='Home DC')

    form = Form(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Reports/Membership/Trade-Ins')

    users = User.objects.select_related()

    state = form.cleaned_data.get('state')
    if state:
        users = users.filter(profile__shipping_state=state)

    dc = form.cleaned_data.get('dc')
    if dc:
        users = users.filter(profile__dropship=dc)

    users = users.filter(tradeorder__items__processed=True, tradeorder__items__declined=False).annotate(item_count=Count('tradeorder__items')).filter(item_count__gt=0).order_by('-item_count')

    return {
        'title': 'Membership: Trade-Ins',
        'paged_qs': users,
        'form': form,
    }, None, ('users', 50, )

def membership__trade_ins__top_trades(request, **kwargs):
    items = Item.objects.filter(rent_amount__gt=0).order_by('-trade_amount')[:100]

    return {
        'title': 'Trade-Ins: Top Trades',
        'paged_qs': items,
    }, None, ('items', 100, )

def channel_advisor(request, **kwargs):
    qs = DistributorItem.objects.filter(distributor__id=5).select_related().order_by('item__short_name')

    if 'excel' in request.GET:
        domain = 'http://' + Site.objects.get_current().domain
        return make_excel(qs,
                          ('text',
                           'text',
                           'text',
                           'int',
                           'float',
                           'text',
                           'text',
                           'text',
                           'text',
                           'text',
                           'money',
                           'money',
                           'money',
                           'text',
                           'text',
                           'text'),
                          ('Auction Title',
                           'Inventory Number',
                           'Quantity Update Type',
                           'Quantity',
                           'Weight',
                           'UPC',
                           'Description',
                           'Manufacturer',
                           'Brand',
                           'Condition',
                           'Seller Cost',
                           'Product Margin',
                           'Retail Price',
                           'Picture URLs',
                           'Video Game',
                           'Genres'),
                          lambda i: (i.item.get_cropped_name_80(),
                                     i.item.id,
                                     'IN STOCK',
                                     i.quantity,
                                     i.item.get_game_weight(),
                                     i.item.upc,
                                     i.item.description,
                                     i.item.publisher.name,
                                     i.item.category.name,
                                     'New',
                                     i.retail_price,
                                     i.item.margin(),
                                     i.item.retail_price_new,
                                     i.item.get_large_cover(),
                                     domain + i.item.get_absolute_url() + '?cid=12',
                                     ', '.join(map(str, i.item.genres.all()))))

    return {
        'title': 'Channel Advisor',
        'paged_qs': qs,
    }, None, ('items', 100, )

def membership__buy(request, **kwargs):
    class Form(forms.Form):
        state = forms.ChoiceField(choices=STATE_CHOICES, required=False)
        dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), required=False, label='Home DC')

    form = Form(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Reports/Membership/Buy')

    users = User.objects.select_related()

    state = form.cleaned_data.get('state')
    if state:
        users = users.filter(profile__shipping_state=state)

    dc = form.cleaned_data.get('dc')
    if dc:
        users = users.filter(profile__dropship=dc)

    users = users.exclude(buyorder__status__in=[BuyOrderStatus.New, BuyOrderStatus.AutoCancel, BuyOrderStatus.Canceled]).annotate(item_count=Count('buyorder__items')).filter(item_count__gt=0).order_by('-item_count')

    return {
        'title': 'Membership: Buy (paid users)',
        'paged_qs': users,
        'form': form,
    }, None, ('users', 50, )

def membership__buy__best_sellers(request, **kwargs):
    items = Item.objects.filter(sold_amount__gt=0).order_by('-sold_amount')[:100]

    return {
        'title': 'Buy: Best Sellers',
        'paged_qs': items,
    }, None, ('items', 100, )


def inactive_items(request, **kwargs):
    class Form(forms.Form):
        platform = forms.ModelChoiceField(queryset=Category.list(), required=False)

    items = Item.objects.filter(active=False)

    form = Form(request.GET)
    if form.is_valid():
        d = form.cleaned_data.get('platform')
        if d:
            items = items.filter(category=d)
    else:
        form = Form()

    if 'excel' in request.GET:
        return make_excel(items,
                          ('text', 'text', 'text', 'text', 'date'),
                          ('PID', 'UPC', 'GAME TITLE', 'PLATFORM', 'RELEASE DATE'),
                          lambda o: (str(o.id),
                                     o.upc,
                                     o.short_name,
                                     o.category.name,
                                     o.release_date))

    return {
        'title': 'Inactive Items',
        'paged_qs': items,
        'form': form,
    }, None, ('items', 50)

def affiliates__compliance(request, **kwargs):
    class FilterForm(forms.Form):
        start_date = forms.DateField(required=False, label='start date')
        end_date = forms.DateField(required=False, label='end date')

    cursor = connection.cursor()

    start_date = None
    end_date = None

    data = request.GET.copy()
    form = FilterForm(data)
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

    if not start_date:
       start_date = datetime(2011, 1, 1).now().date()

    def make_date_filter(col, start, end):
        where = []
        if start:
            if end == start or not end:
                where.append("%s = '%s'" % (col, start.strftime('%Y-%m-%d')))
            else:
                if end < start:
                    start, end = end, start
                where.append("%s >= '%s'" % (col, start.strftime('%Y-%m-%d')))
                where.append("%s <= '%s'" % (col, end.strftime('%Y-%m-%d')))
        return ' and '.join(where)

    stats = {
    }

    q = """
select
    p.campaign_cid,
    c.name,
    p.sid,
    count(p.id)
  from
    auth_user u
    inner join members_profile p on u.id = p.user_id
    left join members_campaign c on p.campaign_cid = c.cid
  where
  """ + make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date) + """
  group by
    p.campaign_cid,
    c.name,
    p.sid
;
    """

    cursor.execute(q)

    for cid, cname, sid, user_count in cursor.fetchall():
        k = (cid, sid)
        stats[k] = \
        {
            'campaign': cname,
            'cid': cid,
            'sid': sid,
            'user_count': user_count,
        }

    q = """
select
    u.campaign_cid as campaign_cid,
    u.sid as sid,
    date_trunc('day', min(au.date_joined))
  from
    wat_uids_by_campaign u
    inner join auth_user au on u.user_id = au.id
  group by
    campaign_cid,
    sid
;
    """
    cursor.execute(q)
    for cid, sid, first_activity in cursor.fetchall():
       k = (cid, sid)
       if k in stats:
           stats[k]['age'] = (start_date - first_activity.date()).days


    q = """
select
    p.campaign_cid,
    p.sid,
    count(u.id)
  from
    members_profile p
    inner join auth_user u on p.user_id = u.id
  where
    """ + make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date) + """
    and p.rent_pixels_flag = true
  group by
    p.campaign_cid,
    p.sid
;
    """
    cursor.execute(q)

    for cid, sid, rent_pixel_users in cursor.fetchall():
        k = (cid, sid)
        stats[k]['rent_pixel_users'] = rent_pixel_users

    q = """
select
    u.campaign_cid as campaign_cid,
    u.sid as sid,
    count(distinct u.user_id) as rentplan_active_users
  from
    wat_uids_by_campaign u
    inner join rent_memberrentalplan rentplan on u.user_id = rentplan.user_id
  where
    """ + make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date) + """
    and rentplan.status = 1
  group by
    campaign_cid,
    sid
;
    """
    cursor.execute(q)
    for cid, sid, rentplan_active_users in cursor.fetchall():
        k = (cid, sid)
        stats[k]['rentplan_active_users'] = rentplan_active_users


    q = """
select
    u.campaign_cid as campaign_cid,
    u.sid as sid,
    count(distinct u.user_id) as total_user_count,
    count(distinct rentplan.user_id) as rent_user_count,
    count(distinct rentlist.user_id) as rentlist_user_count,
    count(distinct claims.user_id) as claim_user_count
  from
    wat_uids_by_campaign u
    left join rent_memberrentalplan rentplan on u.user_id = rentplan.user_id
    left join rent_rentlist rentlist on u.user_id = rentlist.user_id
    left join claims_claim claims on u.user_id = claims.user_id
  where
  """ + make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date) + """
  group by
    campaign_cid,
    sid
;
    """
    cursor.execute(q)
    for cid, sid, total_users, rent_users, w_rentlist, w_claims in cursor.fetchall():
        k = (cid, sid)
        stats[k]['total_users'] = total_users
        stats[k]['rent_users'] = rent_users
        stats[k]['count_with_rentlist'] = w_rentlist
        if stats[k]['rent_users']:
            stats[k]['percent_with_rentlist'] = '%3.1f' % (100 * ((float(w_rentlist) / stats[k]['rent_users'])))
        else:
            stats[k]['percent_with_rentlist'] = '-'
        stats[k]['count_with_claims'] = w_claims
        stats[k]['percent_with_claims'] = '%3.1f' % (100 * ((float(w_claims) / stats[k]['user_count'])))

    q = """
select
    u.campaign_cid as campaign_cid,
    u.sid as sid,
    case
      when sum(rentplan.payment_fails_count) is null then 0
      else cast(sum(rentplan.payment_fails_count) as float) / count(distinct u.user_id)
    end as average_rebills
  from
    wat_uids_by_campaign u
    inner join rent_memberrentalplan rentplan on u.user_id = rentplan.user_id
  where
    """ + make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date) + """
  group by
    campaign_cid,
    sid
;
    """
    cursor.execute(q)
    for cid, sid, average_rebills in cursor.fetchall():
        k = (cid, sid)
        stats[k]['average_rebill_count'] = average_rebills


    q = """
select
    u.campaign_cid as campaign_cid,
    u.sid as sid,
    count(distinct u.user_id) as count_rebilled
  from
    wat_uids_by_campaign u
    inner join rent_memberrentalplan rentplan on u.user_id = rentplan.user_id
  where
    """ + make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date) + """
  group by
    campaign_cid,
    sid
;
    """
    cursor.execute(q)
    for cid, sid, count_rebilled in cursor.fetchall():
        k = (cid, sid)
        stats[k]['count_rebilled'] = count_rebilled
        stats[k]['percent_rebilled'] = '%3.1f' % (100 * ((float(count_rebilled) / stats[k]['user_count'])))


    q = """
select
    u.campaign_cid,
    u.sid,
    sum(mbh.debit)
  from
    wat_uids_by_campaign u
    inner join members_billinghistory mbh on u.user_id = mbh.user_id
  where
    """ + make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date) + """
    and mbh.status = 0
  group by
    u.campaign_cid,
    u.sid
;
    """
    cursor.execute(q)
    for cid, sid, sum in cursor.fetchall():
        k = (cid, sid)
        stats[k]['amount_approved'] = sum

    q = """
select
    u.campaign_cid,
    u.sid,
    sum(mbh.debit)
  from
    wat_uids_by_campaign u
    inner join members_billinghistory mbh on u.user_id = mbh.user_id
  where
    """ + make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date) + """
    and mbh.status = 3
  group by
    u.campaign_cid,
    u.sid
;
    """
    cursor.execute(q)
    for cid, sid, sum in cursor.fetchall():
        k = (cid, sid)
        stats[k]['amount_authorized'] = sum

    # fill in any missing values (as blanks) so we don't have to worry about them during rendering
    #keys = set()
    #for campaign in stats:
    #    keys = keys.union(set(stats[campaign].keys()))
    for campaign in stats:
        if not stats[campaign]['sid']:
            stats[campaign]['sid'] = ''
        #for key in keys:
        #    if not key in stats[campaign]:
        #        stats[campaign] = ''

    def sort_by_keys(stats):
        r = []
        for k in sorted(stats):
            r.append(stats[k])
        return r

    return {
        'title': 'Affiliate Compliance Report',
        'start_date': start_date,
        'end_date': end_date,
        'form': form,
        'stats': sort_by_keys(stats),
        'debug': pformat(stats),
        'datespec': make_date_filter("date_trunc('day', u.date_joined)", start_date, end_date)
    }, None


def membership__rent_subscribers__canceled(request, **kwargs):
    items = MemberRentalPlanHistory.objects.filter(status=RentalPlanStatus.Canceled).order_by('-finish_date').select_related()

    if 'excel' in request.GET:
        return make_excel(items,
                          (
                           'int',
                           'text',
                           'text',
                           'text',
                           'text',
                           'text',
                           'text',
                           'text',
                           'text',
                           'date',
                           'date',
                           'date',
                           'text',
                           'int',
                           'int',
                           'int',
                           'int',
                           'text',
                           'text',
                           'text',
                           'text',
                           'text',
                           'text',
                           'int'
                          ),
                          (
                           'Member ID',
                           'Login ID',
                           'Member Name',
                           'Address',
                           'City',
                           'State',
                           'Zip Code',
                           'Home DC',
                           'Phone Number',
                           'Registration Date',
                           'Cancellation Date',
                           'Last Login Date',
                           'Account Status',
                           'Games Out',
                           'Games In',
                           'Rental Queue',
                           'Days Active',
                           'Promo Code',
                           'CID',
                           'SID',
                           'Ip Address',
                           'Plan Type',
                           'Reason',
                           'Billing Cycles'
                          ),
                          lambda d: (
                            d.user.id,
                            d.user.email or d.user.username,
                            d.user.get_full_name(),
                            ' '.join((d.user.profile.shipping_address1 or '', d.user.profile.shipping_address2 or '', )),
                            d.user.profile.shipping_city,
                            d.user.profile.shipping_state,
                            d.user.profile.shipping_zip,
                            d.user.profile.dropship.code if d.user.profile.dropship else '--',
                            d.user.profile.phone or '',
                            d.user.date_joined,
                            d.finish_date,
                            d.user.last_login,
                            d.get_status_display(),
                            d.get_games_out_amount(),
                            d.get_games_in_amount(),
                            d.user.rentlist_set.all().count(),
                            d.get_active_days().days,
                            '',
                            d.user.profile.get_campaign_cid_display(),
                            '',
                            '',
                            d.get_plan_display(),
                            d.get_cancel_reason(),
                            d.get_billing_cycles(),
                          ))

    return {
        'title': 'Cancellations By Members',
        'paged_qs': items,
    }, None, ('data', 50)


def membership__rent_subscribers__canceled_by_active_days(request, **kwargs):
    items = MemberRentalPlanHistory.objects.filter(status=RentalPlanStatus.Canceled).order_by('-finish_date').select_related()
    data = [0, 0, 0, 0, 0]
    for i in items:
        d = i.get_active_days().days
        if d == 1:
            index = 0
        elif d < 4:
            index = 1
        elif d < 11:
            index = 2
        elif d < 31:
            index = 3
        else:
            index = 4
        data[index] += 1

    return {
        'title': 'Cancellations By Active Days',
        'data': data,
    }, None,


def membership__rent_subscribers__canceled_by_affiliate(request, **kwargs):
    data = {}
    items = MemberRentalPlanHistory.objects.filter(status=RentalPlanStatus.Canceled).order_by('-finish_date').select_related()
    for i in items:
        cid = i.user.profile.campaign_cid or '0'
        dd = data.get(cid, {'cid': cid,
                            'description': i.user.profile.get_campaign_cid_display(),
                            'values': [0, 0, 0, 0, 0]})
        d = i.get_active_days().days
        if d == 1:
            index = 0
        elif d < 4:
            index = 1
        elif d < 11:
            index = 2
        elif d < 31:
            index = 3
        else:
            index = 4
        dd['values'][index] += 1

        data[cid] = dd

    data = data.values()
    data.sort(lambda a, b: cmp(a['cid'], b['cid']))

    return {
        'title': 'Cancellations By Affiliate',
        'data': data,
    }, None,


def membership__rent_subscribers__canceled_by_reason(request, **kwargs):
    items = MemberRentalPlanHistory.objects.filter(status=RentalPlanStatus.Canceled).order_by('-finish_date').select_related()
    data = (
        ['Shipping too slow', 0, 0, 0, 0, 0],
        ['Too many shipping problems', 0, 0, 0, 0, 0],
        ['Website is not user friendly', 0, 0, 0, 0, 0],
        ['Switching to another service', 0, 0, 0, 0, 0],
        ['Not enough variety of games', 0, 0, 0, 0, 0],
        ['Moving / Traveling', 0, 0, 0, 0, 0],
        ['Poor customer service', 0, 0, 0, 0, 0],
        ['Service costs too much', 0, 0, 0, 0, 0],
        ['Only signed up for promotion', 0, 0, 0, 0, 0],
        ['Poor inventory availability', 0, 0, 0, 0, 0],
    )
    for i in items:
        r = i.cancel_reason()
        if not r:
            continue
        d = i.get_active_days().days
        if d == 1:
            index = 0
        elif d < 4:
            index = 1
        elif d < 11:
            index = 2
        elif d < 31:
            index = 3
        else:
            index = 4
        if r.shipping_to_slow: data[0][index + 1] += 1
        if r.too_many_shipping_problems: data[1][index + 1] += 1
        if r.website_is_not_user_friendly: data[2][index + 1] += 1
        if r.switching_to_another_service: data[3][index + 1] += 1
        if r.not_enough_variety_of_games: data[4][index + 1] += 1
        if r.moving_traveling: data[5][index + 1] += 1
        if r.poor_customer_service: data[6][index + 1] += 1
        if r.service_costs_too_much: data[7][index + 1] += 1
        if r.only_signed_up_for_promotion: data[8][index + 1] += 1
        if r.poor_inventory_availability: data[9][index + 1] += 1

    return {
        'title': 'Cancellations By Reason',
        'data': data,
    }, None,


def membership__by_summary(request, **kwargs):
    years = [x for x in range(datetime.now().year - 2, datetime.now().year + 1)]
    data = {
        'rent': {},
        'buy': {}
    }

    cursor = connection.cursor() #@UndefinedVariable

    def change_percent(data):
        d = map(lambda val, prev: decimal.Decimal(str(100 * prev / val)) if val else decimal.Decimal('0.0'),
                data,
                [0] + data[:-1])
        return d + [sum(d)/(len(d) - 1)]

    def calc_billing_history_stat(y, q, type):
        query = '''
            select
                ''' + q + '''
            from members_billinghistory h
            where
                h.status = %d and
                h.type = %d and
                not exists (select r.id from members_refund r where h.id = r.payment_id) and
                h."timestamp" between '%d-01-01 00:00:00' and '%d-12-31 23:59:59.999999'
        '''
        cursor.execute(query % (TransactionStatus.Passed, type, y, y))
        return cursor.fetchone()

    #
    # Rent
    #

    # Subscribers: beginning of period
    beginning_of_period = [User.objects.filter(date_joined__lt=datetime(y, 1, 1)).count() for y in years]
    data['rent']['beginning_of_period'] = beginning_of_period + [beginning_of_period[0]]

    # Gross subscribers additions: during period
    gross_subscribers_additions = [User.objects.filter(date_joined__year=y).count() for y in years]
    data['rent']['gross_subscribers_additions_during_period'] = gross_subscribers_additions + [sum(gross_subscribers_additions)]

    # Gross subscriber additions year-to-year change
    data['rent']['gross_subscriber_additions_year_to_year_change'] = change_percent(gross_subscribers_additions)

    # Less subscriber cancellations: during period
    less_subscriber_cancellations = [0 for y in years]
    data['rent']['less_subscriber_cancellations_during_period'] = less_subscriber_cancellations + [sum(less_subscriber_cancellations)]

    # Subscribers: end of period
    end_of_period = map(lambda b, g, l: b + g - l,
        beginning_of_period,
        gross_subscribers_additions,
        less_subscriber_cancellations)
    data['rent']['subscribers_end_of_period'] = end_of_period + [end_of_period[-1]]

    # Subscribers year-to-year change
    data['rent']['subscribers_year_to_year_change'] = change_percent(end_of_period)

    # Rent subscribers: end of period
    def calc_rent_subscribers_end_of_period(y):
        query = '''
            select
                count(1)
            from
                auth_user u
            where
                exists (select p.id
                        from rent_memberrentalplan p
                        where p.user_id = u.id
                          and p.start_date <= %s)
                or exists (select h.id
                        from rent_memberrentalplanhistory h
                        where h.user_id = u.id
                          and %s between h.start_date and h.finish_date)
        '''
        end_of_year = datetime(y, 12, 31)
        cursor.execute(query, [end_of_year, end_of_year])
        return cursor.fetchone()[0]

    rent_subscribers_end_of_period = map(calc_rent_subscribers_end_of_period, years)
    data['rent']['rent_subscribers_end_of_period'] = rent_subscribers_end_of_period + [rent_subscribers_end_of_period[-1]]

    # Paid subscribers year-to-year change
    data['rent']['paid_subscribers_year_to_year_change'] = change_percent(rent_subscribers_end_of_period)

    # Average monthly revenue per paying subscriber
    d = map(lambda y: calc_billing_history_stat(y, 'sum(h.debit) / count(distinct h.user_id) / 12.0', TransactionType.RentPayment)[0] or 0, years)
    data['rent']['average_monthly_revenue_per_paying_subscriber'] = d + [sum(d)]

    # Churn
    #
    # Churn is calculated by dividing terminations (cancels and suspends) of rent subscriptions during the period
    # by the total number of subscribers at the beginning of that period.
    #
    d = []
    for y, total in zip(years, beginning_of_period):
        end_of_year = datetime(y, 12, 31)
        cancels = MemberRentalPlanHistory.objects.filter(status=RentalPlanStatus.Canceled, start_date__lt=end_of_year, finish_date__gte=end_of_year).count()
        suspends = MemberRentalPlan.objects.filter(status=RentalPlanStatus.Suspended, suspend_date__year=y).count()
        if total:
            d.append(100.0 * (cancels + suspends) / total)
    if d:
        data['rent']['churn'] = d + [sum(d) / len(d)]
    else:
        data['rent']['churn'] = []

    # Subscriber acquisition cost
    d = [30 for y in years]
    if d:
        data['rent']['subscriber_acquisition_cost'] = d + [sum(d) / len(d)]
    else:
        data['rent']['subscriber_acquisition_cost'] = []

    # Revenue
    rent_revenue = map(lambda y: calc_billing_history_stat(y, 'sum(h.debit)', TransactionType.RentPayment)[0] or 0, years)
    data['rent']['revenue'] = rent_revenue + [sum(rent_revenue)]

    #
    # Buy
    #

    # Customers: beginning of period
    def calc_buy_beginning_of_period(y):
        query = '''
            select
                count(distinct h.user_id)
            from members_billinghistory h
            where
                h.status = %d and
                h.type = %d and
                not exists (select r.id from members_refund r where h.id = r.payment_id) and
                h."timestamp" < '%d-01-01 00:00:00'
        '''
        cursor.execute(query % (TransactionStatus.Passed, TransactionType.BuyCheckout, y))
        return cursor.fetchone()[0]

    buy_beginning_of_period = map(calc_buy_beginning_of_period, years)
    data['buy']['beginning_of_period'] = buy_beginning_of_period + [buy_beginning_of_period[0]]

    # Gross Customers additions: during period
    def calc_buy_gross(y):
        query = '''
            select
                count(distinct h.user_id)
            from members_billinghistory h
            where
                h.status = %d and
                h.type = %d and
                not exists (select r.id from members_refund r where h.id = r.payment_id) and
                h."timestamp" between '%d-01-01 00:00:00' and '%d-12-31 23:59:59.999999' and
                not exists (
                    select b.id
                    from members_billinghistory b
                    where b.user_id = h.user_id
                      and h."timestamp" < '%d-01-01 00:00:00')
        '''
        cursor.execute(query % (TransactionStatus.Passed, TransactionType.BuyCheckout, y, y, y))
        return cursor.fetchone()[0]
    gross_customers_additions_during_period = map(calc_buy_gross, years)
    data['buy']['gross_customers_additions_during_period'] = gross_customers_additions_during_period + [sum(gross_customers_additions_during_period)]

    # Gross Customer additions year-to-year change
    data['buy']['gross_customers_additions_year_to_year_change'] = change_percent(gross_customers_additions_during_period)

    # Customers: end of period
    buy_end_of_period = map(lambda b, g: b+g, buy_beginning_of_period, gross_customers_additions_during_period) +\
        [buy_beginning_of_period[0] + sum(gross_customers_additions_during_period)]

    data['buy']['end_of_period'] = buy_end_of_period

    # Customers year-to-year change
    data['buy']['customers_year_to_year_change'] = change_percent(buy_end_of_period[:-1])

    # New video game software
    new_games = [
        BuyOrderItem.objects.filter(
                order__status=BuyOrderStatus.Checkout,
                order__create_date__year=y,
                is_new=True)\
            .aggregate(d=Sum('price'))['d'] or 0
        for y in years]
    data['buy']['new_games'] = new_games + [sum(new_games)]

    # Used video game software
    used_games = [
        BuyOrderItem.objects.filter(
                order__status=BuyOrderStatus.Checkout,
                order__create_date__year=y,
                is_new=False)\
            .aggregate(d=Sum('price'))['d'] or 0
        for y in years]
    data['buy']['used_games'] = used_games + [sum(used_games)]

    # Average monthly revenue per paying Customer
    def calc_average_monthly_revenue_per_paying_customer(y):
        query = '''
            select
                sum(i.price) / count(distinct u.id) / 12.0
            from buy_orders_buyorderitem i
            inner join buy_orders_buyorder o on o.id = i.order_id
            inner join auth_user u on u.id = o.user_id
            where o.status = %d
              and o.create_date between '%d-01-01 00:00:00' and '%d-12-31 23:59:59.999999'
        '''
        cursor.execute(query % (BuyOrderStatus.Checkout, y, y))
        return cursor.fetchone()[0] or 0
    average_monthly_revenue_per_paying_customer = map(calc_average_monthly_revenue_per_paying_customer, years)
    data['buy']['average_monthly_revenue_per_paying_customer'] = average_monthly_revenue_per_paying_customer + [sum(average_monthly_revenue_per_paying_customer) / len(average_monthly_revenue_per_paying_customer)]

    # Returns
    data['buy']['returns'] = [0 for y in years] + [0]

    # Customer acquisition cost
    d = [30 for y in years]
    data['buy']['customer_acquisition_cost'] = d + [sum(d) / len(d)]

    # Projected Revenue
    buy_revenue = [
        BuyOrderItem.objects.filter(
                order__status=BuyOrderStatus.Checkout,
                order__create_date__year=y)\
            .aggregate(d=Sum('price'))['d'] or 0
        for y in years]
    data['buy']['projected_revenue'] = buy_revenue + [sum(buy_revenue)]

    total_revenue = map(lambda r, b: r + b, rent_revenue, buy_revenue)
    data['total_revenue'] = total_revenue + [sum(total_revenue)]

    return {
        'title': 'Membership by Summary',
        'years': years,
        'data': data,
    }, None


def membership__by_business(request, **kwargs):
    class FilterForm(forms.Form):
        d0 = forms.DateField(required=False, label='Date From')
        d1 = forms.DateField(required=False, label='Date To')

    d_x = datetime(datetime.now().year, datetime.now().month, 1)
    d_y = datetime.today()

    data = request.GET.copy()
    data['d0'] = data.get('d0', d_x)
    data['d1'] = data.get('d1', d_y)
    form = FilterForm(data)
    if form.is_valid():
        d0 = form.cleaned_data.get('d0')
        d1 = form.cleaned_data.get('d1')
        if not d0 and not d1:
            d0 = d_x
            d1 = d_y
    else:
        d0 = d_x
        d1 = d_y

    def get_date_filter_str(fname, d0, d1):
        r = []
        if d0:
            r.append("%s >= '%s'" % (fname, d0.strftime('%Y-%m-%d')))
        if d1:
            r.append("%s < '%s'" % (fname, d1.strftime('%Y-%m-%d')))
        return ' and '.join(r)


    d0 = datetime(2000, 1, 1)
    d1 = datetime(2020, 1, 1)

    ##########################################

    buy = {}

    buy_order_items = BuyOrderItem.objects.filter(order__status=BuyOrderStatus.Checkout,
                                                  order__create_date__gte=d0,
                                                  order__create_date__lt=d1)

    buy_orders = BuyOrder.objects.filter(status=BuyOrderStatus.Checkout,
                                         create_date__gte=d0,
                                         create_date__lt=d1)

    r = buy_orders.filter(payment_transaction__status=TransactionStatus.Passed).aggregate(r1 = Sum('payment_transaction__debit'), r2 = Sum('payment_transaction__applied_credits'))
    revenue_credits = r['r2'] or 0
    revenue_money = (r['r1'] or 0) - (r['r2'] or 0)

    buy['subs'] = {
        'order_stats': {
            'received': {
                'new': buy_order_items.filter(is_new=True).count(),
                'used': buy_order_items.filter(is_new=False).count(),
                'money': buy_order_items.filter(order__payment_transaction__applied_credits=0).count(),
                'credits': buy_order_items.filter(order__payment_transaction__applied_credits__gt=0).count(),
                'gifts': 0,

                'total': buy_order_items.count(),
            },
            'revenue': {
                'money': revenue_money,
                'credits': revenue_credits,
                'total': revenue_money + revenue_credits,
            },
        },
    }

    r = {}
    for o in buy_orders:
        code = o.user.profile.dropship.code
        d = r.get(code, set())
        d.add(o.user.id)
        r[code] = d

    buy['fulf'] = {
        'paid_subs': {
            'FL': len(r.get('FL', set())),
            'NJ': len(r.get('NJ', set())),
            'NV': len(r.get('NV', set())),
        },
    }
    buy['fulf']['paid_subs']['total'] = sum(buy['fulf']['paid_subs'].values())
    buy['fulf']['proc'] = {
        'prepared': buy_order_items.filter(pack_slip_item__slip__date_shipped=None).count(),
        'shipped': buy_order_items.exclude(pack_slip_item__slip__date_shipped=None).count(),
        'total': buy_order_items.count(),
    }

    inv = Inventory.objects.filter(buy_only=True, status=InventoryStatus.InStock)
    sold_items = buy_order_items.exclude(inventory=None)
    buy['inv'] = {
        'in_stock': {
            'new': inv.filter(is_new=True).count(),
            'used': inv.filter(is_new=False).count(),

            'total': inv.count(),
        },
        'sold': {
            'new': sold_items.filter(is_new=True).count(),
            'used': sold_items.filter(is_new=False).count(),

            'total': sold_items.count(),
        },
    }

    ##########################################

    trade = {}

    trade_orders_items = TradeOrderItem.objects.filter(order__create_date__gte=d0,
                                                       order__create_date__lt=d1)

    trade_orders = TradeOrder.objects.filter(create_date__gte=d0,
                                             create_date__lt=d1)

    trade['subs'] = {
        'pending': trade_orders_items.filter(processed=False).count(),
        'processed': trade_orders_items.filter(processed=True).count(),

        'total': trade_orders_items.count(),
    }

    r = {}
    for o in trade_orders:
        code = o.user.profile.dropship.code
        d = r.get(code, set())
        d.add(o.user.id)
        r[code] = d

    trade['fulf'] = {
        'subs': {
            'FL': len(r.get('FL', set())),
            'NJ': len(r.get('NJ', set())),
            'NV': len(r.get('NV', set())),
        },
    }
    trade['fulf']['subs']['total'] = sum(trade['fulf']['subs'].values())

    trade['inv'] = {
        'approved': trade_orders_items.filter(processed=True, declined=False).count(),
        'declined': trade_orders_items.filter(processed=True, declined=True).count(),

        'total': trade_orders_items.filter(processed=True).count(),
    }

    ##########################################

    rent = {}

    rental_plans = MemberRentalPlan.objects.all()

    recc = rental_plans.filter(start_date__lt=datetime.today() - timedelta(30))

    rent['subs'] = {
        'new': {
            'pending': rental_plans.filter(status=RentalPlanStatus.Pending).count(),
            'active': rental_plans.filter(status=RentalPlanStatus.Active, start_date__gte=datetime.today() - timedelta(30)).count()
        },
        'billing': {
            'active': recc.filter(status=RentalPlanStatus.Active).count(),
            'delinquent': recc.filter(status=RentalPlanStatus.Delinquent).count(),
#            'canceled': {
#                'all': recc.filter(status__in=[RentalPlanStatus.Canceled, RentalPlanStatus.CanceledP]).count(),
#                'c': recc.filter(status=RentalPlanStatus.Canceled).count(),
#                'p': recc.filter(status=RentalPlanStatus.CanceledP).count(),
#            },
            'on_hold': rental_plans.filter(status=RentalPlanStatus.OnHold).count(),
            'suspended': rental_plans.filter(status=RentalPlanStatus.Suspended).count(),
        },
    }
    rent['subs']['new']['total'] = sum(rent['subs']['new'].values())

    c = connection.cursor() #@UndefinedVariable
    c.execute("select rent_status, count(rent_status) from catalog_item where active = 't' group by rent_status order by rent_status;")
    game_avalaibility = dict(c.fetchall())
    game_avalaibility['total'] = sum(game_avalaibility.values())

    c = connection.cursor() #@UndefinedVariable
    c.execute('select d.code, count(distinct p.user_id) from members_profile p inner join inventory_dropship d on d.id = p.dropship_id where exists (select 1 from rent_memberrentalplan mrp where mrp.user_id = p.user_id) group by 1')
    r = dict(c.fetchall())

    c.execute('select d.code, count(1) from rent_rentorder ro inner join inventory_dropship d on d.id = ro.source_dc_id where ro.date_returned is null and ro.status in (1, 9) and d.code is not null group by 1')
    r1 = dict(c.fetchall())

    rent['fufl'] = {
        'game_avalaibility': game_avalaibility,
        'subs': {
            'FL': r.get('FL', 0),
            'NJ': r.get('NJ', 0),
            'NV': r.get('NV', 0),
        },
        'matrix': {
            'shipped': {
                'FL': r1.get('FL', 0),
                'NJ': r1.get('NJ', 0),
                'NV': r1.get('NV', 0),
            },
        },
    }
    rent['fufl']['subs']['total'] = sum(rent['fufl']['subs'].values())
    rent['fufl']['matrix']['shipped']['total'] = sum(rent['fufl']['matrix']['shipped'].values())

    inv = Inventory.objects.exclude(buy_only=True)

    rent['inv'] = {
        'assets': {
            0: inv.filter(status=InventoryStatus.InStock).count(), # In Stock
            1: inv.filter(status=InventoryStatus.Pending).count(), # Pending
            2: inv.filter(status=InventoryStatus.Rented).count(), # Rented
            3: None,
            4: inv.filter(status__in=[InventoryStatus.Sale, InventoryStatus.Sold]).count(),
            5: inv.filter(status=InventoryStatus.Unreconciled).count(),
            6: inv.filter(status=InventoryStatus.Unknown).count(),
            7: inv.filter(status__in=[InventoryStatus.Damaged, InventoryStatus.Lost, InventoryStatus.USPSLost]).count(),
        },
    }

    ##########################################

    data = {
        'buy': buy,
        'trade': trade,
        'rent': rent,
    }

    return {
        'title': 'Membership by Business',
        'form': form,
        'data': data,
    }, None



def recurring_billing_report(request, **kwargs):
    def get_form_choices():
        try:
            d, d0 = datetime.now(), BillingHistory.objects.filter(debit__gt=0).order_by('timestamp')[0].timestamp
        except IndexError:
            return
        while d >= d0:
            yield (d.strftime('%Y%m'), d.strftime('%m/%Y'))
            d = inc_months(d, -1)

    class Form(forms.Form):
        p = forms.ChoiceField(choices=get_form_choices())

    form = Form(request.GET)
    if form.is_valid():
        d = form.cleaned_data.get('p', datetime.now().strftime('%Y%m'))
    else:
        d = datetime.now().strftime('%Y%m')
        form = Form(initial={'d': d})
    d = datetime(int(d[:4]), int(d[4:]), 1).date()
    d1 = inc_months(d, 1)


    cursor = connection.cursor() #@UndefinedVariable

    q = '''
        select
            sum(h.debit - coalesce(r.amount, 0))
        from
            members_billinghistory h
            left outer join members_refund r on h.id = r.payment_id
        where
            h.timestamp >= %s and h.timestamp < %s
            and h.status = 0
    '''
    cursor.execute(q, [d, d1])
    gross_sales =  cursor.fetchall()[0][0]

    cursor = connection.cursor() #@UndefinedVariable

    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 0
        group by
            h.debit
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d, d1])
    new_registrations = {}
    for plan, amount, users in cursor.fetchall():
        new_registrations[plan] = {'plan': plan,
                                   'captured_amount': amount,
                                   'captured_users': users,}

    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 3
            and not exists(select * from members_billinghistory h1 where h1.refered_transaction_id = h.id)
        group by
            h.debit
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d, d1])
    for plan, amount, users in cursor.fetchall():
        data = new_registrations.get(plan, {'plan': plan})
        data['authorized_amount'] = amount
        data['authorized_users'] = users
        new_registrations[plan] = data

    q = '''
        select
            h.debit, count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined >= %s and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 1
            and not exists(select * from members_billinghistory h1 where h1.refered_transaction_id = h.id)
        group by
            h.debit, u.id
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d, d1])
    for plan, users in cursor.fetchall():
        data = new_registrations.get(plan, {'plan': plan})
        data['declined_amount'] = plan * users
        data['declined_users'] = users
        new_registrations[plan] = data

    ###############################3

    cursor = connection.cursor() #@UndefinedVariable

    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 0
        group by
            h.debit
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d])
    recurring_registrations = {}
    for plan, amount, users in cursor.fetchall():
        recurring_registrations[plan] = {'plan': plan,
                                         'captured_amount': amount,
                                         'captured_users': users,}

    q = '''
        select
            h.debit, sum(h.debit), count(distinct h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 3
            and not exists(select * from members_billinghistory h1 where h1.refered_transaction_id = h.id)
        group by
            h.debit, h.status
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d])
    for plan, amount, users in cursor.fetchall():
        data = new_registrations.get(plan, {'plan': plan})
        data['authorized_amount'] = data.get('authorized_amount', 0) + amount
        data['authorized_users'] = data.get('authorized_users', 0) + users
        new_registrations[plan] = data

    q = '''
        select
            h.debit, count(h.user_id)
        from
            members_billinghistory h
            inner join auth_user u on u.id = h.user_id
            inner join members_profile p on p.user_id = h.user_id
            left outer join members_refund r on h.id = r.payment_id
        where
            coalesce(r.amount, 0) = 0
            and h.type = 1
            and h.timestamp >= %s and h.timestamp < %s
            and u.date_joined < %s
            and h.debit > 0 and h.debit <> 50
            and h.status = 1
            and not exists(select * from members_billinghistory h1 where h1.refered_transaction_id = h.id)
        group by
            h.debit, h.user_id
    order by
        h.debit
    '''
    cursor.execute(q, [d, d1, d])
    for plan, users in cursor.fetchall():
        data = recurring_registrations.get(plan, {'plan': plan})
        data['declined_amount'] = plan * users
        data['declined_users'] = users
        recurring_registrations[plan] = data

    #################################################

    new_registrations = new_registrations.values()
    new_registrations.sort(lambda a, b: cmp(a['plan'], b['plan']))
    for data in new_registrations:
        data['total'] = data.get('authorized_amount', decimal.Decimal('0.00')) + data.get('captured_amount', decimal.Decimal('0.00'))

    recurring_registrations = recurring_registrations.values()
    recurring_registrations.sort(lambda a, b: cmp(a['plan'], b['plan']))
    for data in recurring_registrations:
        data['total'] = data.get('authorized_amount', decimal.Decimal('0.00')) + data.get('captured_amount', decimal.Decimal('0.00'))

    return {
        'title': 'Recurring Billing Report',
        'gross_sales': gross_sales,
        'new_registrations': new_registrations,
        'new_registrations_totals': calc_totals(new_registrations),
        'recurring_registrations': recurring_registrations,
        'recurring_registrations_totals': calc_totals(recurring_registrations),
        'form': form,
    }, None
