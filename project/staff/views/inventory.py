import operator
from string import strip
from logging import debug #@UnusedImport
import tempfile
import datetime
import csv

from django.db import connection, transaction
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django_snippets.views.json_response import JsonResponse
from django.template.context import RequestContext
from django.http import Http404, HttpResponseBadRequest, HttpResponse
from django import forms
from django.db.models.aggregates import Count
from django.db.models.query_utils import Q

from django_snippets.views import paged

from project.members.models import Group
from project.catalog.models.report import ReportUpload
from project.catalog.models import Item
from project.inventory.models import Inventory, Dropship, InventoryStatus,\
    Distributor, DistributorItem
from project.staff.forms import InventoryCheckInForm
from project.staff.views import staff_only
import decimal
from project.inventory.views import print_tyveks
from project.catalog.models.categories import Category
from project.catalog.models.publishers import Publisher


def check_in(request, **kwargs):
    if request.method == 'POST':
        form = InventoryCheckInForm(request.POST)
        if form.is_valid():
            purchase = form.cleaned_data['purchase']
            quantity = form.cleaned_data['quantity']
            is_new = form.cleaned_data['condition'] == 'True'
            buy_only = form.cleaned_data.get('buy_only', False)
            
            for _q in range(quantity):
                inventory = Inventory()
                inventory.dropship = form.cleaned_data['dc']
                inventory.item = form.cleaned_data['upc']
                inventory.purchase_item = form.cleaned_data['purchase_item']
                inventory.buy_only = buy_only
                inventory.fill_barcode() 
                inventory.is_new = purchase.is_new if purchase else is_new
                inventory.save()

            return redirect('staff:page', 'Inventory/Check-In'), None
        item = Item.find_by_upc(form['upc'].data)
    else:
        form = InventoryCheckInForm()
        item = None
    
    return {
        'title': 'Check-In',
        'form': form,
        'item': item,
    }, None


def admin(request, **kwargs):
    class FilterForm(forms.Form):
        q = forms.CharField(required=False, label='')
        platform = forms.ModelChoiceField(queryset=Category.list(), required=False)
    
    form = FilterForm(request.GET)
    if not form.is_valid():
        return redirect('staff:page', 'Inventory/Admin')

    qs = Item.objects.all() 
        
    platform = form.cleaned_data.get('platform')
    if platform:
        qs = qs.filter(category=platform)
        
    q = form.cleaned_data.get('q')
    if q:
        or_q = []
        for f in ['id', 'upc', 'name', 'short_name']:
            or_q.append(Q(**{f + '__icontains': q}))
        qs = qs.filter(reduce(operator.or_, or_q))
    
    return {
        'title': 'Inventory Admin (Under Construction)',
        'paged_qs': qs,
        'form': form,
    }, None, ('items', 50, )


def admin_entries(request, item_id):
    class Form(forms.Form):
        dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), required=True)
    
    if request.method == 'POST':
        form = Form(request.POST)
        if form.is_valid():
            return HttpResponse('OK')
    else:
        form = Form()
        
    def get_ids():
        ids = request.GET.get('ids', '').split(',')
        if ids:
            ids = map(int, ids)
        return ids
        
    action = request.GET.get('action')
    if action == 'allocate_to_buy':
        ids = get_ids()
        for i in Inventory.objects.filter(id__in=ids):
            if i.status != InventoryStatus.InStock:
                continue
            i.buy_only = True
            i.save()
    elif action == 'allocate_to_rent':
        ids = get_ids()
        for i in Inventory.objects.filter(id__in=ids):
            if i.status != InventoryStatus.InStock:
                continue
            i.buy_only = False
            i.save()
            
    item = get_object_or_404(Item, id=item_id)
    inventories = Inventory.objects.filter(item=item).order_by('status', 'dropship__code', 'buy_only')
    unassigned_exists = Inventory.objects.filter(item=item, dropship=None).count() > 0
    return render_to_response('staff/inventory/partials/admin_entries.html', {
        'item': item,
        'inventories': inventories,
        'unassigned_exists': unassigned_exists,
        'form': form,
    }, RequestContext(request))


def get_dc_inventory_query(dc_id, queued=False, ordered=False):
#    sql = '''
#      select
#          catalog_item.*,
#          (select count(1) from inventory_inventory av where
#              av.item_id = catalog_item.id and
#              av.dropship_id = %d and
#              av.status = %d) available_count,
#          (select count(1) from inventory_inventory st where
#              st.item_id = catalog_item.id and
#              st.dropship_id = %d and
#              st.status = %d) instock_count,
#          (select count(1) from inventory_inventory tc where
#              tc.item_id = catalog_item.id and
#              tc.dropship_id = %d) total_count
#      from catalog_item  
#      where exists(select id from inventory_inventory av1 
#          where av1.item_id = catalog_item.id and
#            av1.dropship_id = %d)       
#    ''' % (dc_id, InventoryStatus.Available,
#           dc_id, InventoryStatus.InStock,
#           dc_id,
#           dc_id)
#    if queued:
#        sql += ' and available_count > 0 '
#    else:
#        sql += ' and total_count > 0 '
    
    sql = '''
      select
          catalog_item.id,
          catalog_item.upc,
          catalog_item.short_name,
          catalog_item.category_id,
          catalog_item.publisher_id,
          catalog_item.release_date,
          count(distinct av.id) available_count,
          count(distinct st.id) instock_count,
          count(distinct tc.id) total_count
      from catalog_item
          left join inventory_inventory av on
              av.item_id = catalog_item.id and
              av.dropship_id = %d and
              av.status = %d
          left join inventory_inventory st on
              st.item_id = catalog_item.id and
              st.dropship_id = %d and
              st.status = %d
          left join inventory_inventory tc on
              tc.item_id = catalog_item.id and
              tc.dropship_id = %d
      group by
          catalog_item.id,
          catalog_item.upc,
          catalog_item.short_name,
          catalog_item.category_id,
          catalog_item.publisher_id,
          catalog_item.release_date
    ''' % (dc_id, InventoryStatus.Available,
           dc_id, InventoryStatus.InStock,
           dc_id)

    if queued:
        sql += 'having count(distinct av.id) > 0 '
    else:
        sql += 'having count(distinct tc.id) > 0 '

    if ordered:
        sql += 'order by catalog_item.id, catalog_item.upc'
    return sql

def get_inventory_query(queued=False, ordered=False):
    sql = '''
      select
          catalog_item.id,
          catalog_item.upc,
          catalog_item.short_name,
          catalog_item.category_id,
          catalog_item.publisher_id,
          catalog_item.release_date,
          count(distinct tc.id) total_count
      from catalog_item
          left join inventory_inventory tc on
              tc.item_id = catalog_item.id and
              tc.dropship_id is null
      group by
          catalog_item.id,
          catalog_item.upc,
          catalog_item.short_name,
          catalog_item.category_id,
          catalog_item.publisher_id,
          catalog_item.release_date
    '''

    if queued:
        sql += 'having count(distinct av.id) > 0 '
    else:
        sql += 'having count(distinct tc.id) > 0 '

    if ordered:
        sql += 'order by catalog_item.id, catalog_item.upc'
    return sql

def dc_queue(request, **kwargs):
    profile = request.user.get_profile()
    if profile.group == Group.DC_Operator:
        dc = profile.dc
        dcs = None
    else:
        dc = Dropship.objects.filter(code=request.GET.get('dc'))
        dc = dc[0] if dc.count() else None
        dcs = Dropship.objects.all()

    if dc:
        sql = get_dc_inventory_query(dc.id, queued=True, ordered=True)
        items = Item.objects.raw(sql)
    else:
        items = None

    return {
        'title': 'Inventory',
        'dc': dc,
        'dcs': dcs,
        'items': items,
    }, None


def physical(request, dc_code=None, **kwargs):
    if 'dc' in request.GET:
        return redirect('staff:physical_inventory', request.GET['dc'])
    
    
    class FilterForm(forms.Form):
        platform = forms.ModelChoiceField(Category.list(), empty_label='(All)', required=False)
        publisher = forms.ModelChoiceField(Publisher.objects.all().order_by('name'), empty_label='(All)', required=False)
        q = forms.CharField(required=False, label='')
    
    
    profile = request.user.get_profile()
    if profile.group == Group.DC_Operator:
        if dc_code:
            raise Http404()
        dc = profile.dc
        dsc = None
    else:
        dc = Dropship.objects.filter(code=dc_code)
        dc = dc[0] if dc.count() else None
        dsc = Dropship.objects.all()

    search_form = FilterForm(request.GET)
    search_form.is_valid() # bound the form
    sd = search_form.cleaned_data

    qs = Inventory.objects.all()
    qs = qs.filter(dropship=dc)
    if not dc:
        qs = qs.order_by('-id')
    
    qs1 = qs
    if sd.get('platform'):
        qs1 = qs1.filter(item__category=sd['platform'].id)
    if sd.get('publisher'):
        qs1 = qs1.filter(item__publisher=sd['publisher'].id)
    if sd.get('q'):
        q = sd['q']
        filters = []
        for f in ('upc', 'id', 'short_name', 'genre_list', 'tag_list'):
            filters.append(Q(**{'item__%s__icontains' % f: q}))
        qs1 = qs1.filter(reduce(operator.or_, filters))

    class ItemWrapper(object):
        def __init__(self, id, total_count):
            self.id = id
            self.total_count = total_count
            
        def item(self):
            if hasattr(self, '__item'):
                return self.__item
            self.__item = Item.objects.get(pk=self.id)
            return self.__item
        
        def instock_count(self):
            return qs.filter(item__id=self.id, status=InventoryStatus.InStock).count()
    
    items = []
    for i in qs1.values('item').annotate(total_count=Count('item')):
        items.append(ItemWrapper(i['item'], i['total_count']))

    ctx = {
        'title': 'Physical Games',
        'dc_code': dc.code if dc else 'GMS',
        'dcs': dsc, 
        'paged_qs': items,
        'search_form': search_form,
    }
    if not dc_code:
        return ctx, None, ('items', )
    else:
        def wrapper(request, *args, **kwargs): return ctx
        ctx = paged('items')(wrapper)(request)
        return render_to_response('staff/inventory/physical.html', ctx, RequestContext(request))

@staff_only
def entries(request, dc_code, item_id):
    if dc_code == 'GMS':
        dc = None
    else:
        dc = get_object_or_404(Dropship, code=dc_code)
    item = get_object_or_404(Item, id=item_id)

    inventories = Inventory.objects.filter(item=item).order_by('status', 'barcode')
    if dc:
        inventories = inventories.filter(dropship=dc) 

    can_unreconcile = request.user.is_superuser or request.user.get_profile().group in [Group.DC_Manager] 

    if 'print' in request.REQUEST:
        ids = request.REQUEST['print'].split(',')
        if ids and ids[0] != '':
            ids = map(strip, ids)
            inventories = inventories.filter(id__in=map(int, ids))
        return print_tyveks(request, inventories)
    elif 'unreconcile' in request.REQUEST and can_unreconcile:
        inventory = Inventory.find_by_barcode(request.REQUEST['unreconcile'])
        if inventory:
            inventory.mark_as_unreconciled() 
    elif request.method == 'POST':
        if not dc:
            dc = get_object_or_404(Dropship, code=request.POST.get('dc', ''))

        for inventory in inventories:
            if inventory.status == InventoryStatus.Available:
                if request.POST.get('checked_inventory_%d' % inventory.id, False):
                    if inventory.dropship:
                        inventory.status = InventoryStatus.InStock
                    else:
                        inventory.dropship = dc
                        inventory.fill_barcode()
                    inventory.save()
        return JsonResponse({'success': True}) 

    ctx = {
        'dc_code': dc_code,
        'dcs': Dropship.objects.all(),
        'item': item,
        'inventories': inventories,
        'can_unreconcile': can_unreconcile, 
    }
    return render_to_response('staff/inventory/entries.html', ctx, context_instance=RequestContext(request))


@transaction.commit_on_success
def upload__master_product_list(request, **kwargs):
    class UploadMPLForm(forms.Form):
        file = forms.FileField()

    message = None
    if request.method == 'POST':
        form = UploadMPLForm(request.POST, request.FILES)
        if form.is_valid():
            with tempfile.NamedTemporaryFile() as f:
                for chunk in form.cleaned_data['file'].chunks():
                    f.write(chunk)
                f.flush()

                from project.management.commands.importmpl import Command
                command = Command()
                command.handle(xls_filename=f.name)
                message = "Done"
    else:
        form = UploadMPLForm()        
    return {
        'title': 'Upload Master Product List',
        'form': form,
        'message': message,
    }, None


@transaction.commit_on_success
def upload__new(request, **kwargs):
    class UploadInventoryForm(forms.Form):
        retailer = forms.ModelChoiceField(Distributor.objects.filter(new_games_vendor=True))
        file = forms.FileField()

    message = None    
    not_founded_upc = []
    if request.method == 'POST':
        form = UploadInventoryForm(request.POST, request.FILES)
        if form.is_valid():
            dtn = datetime.datetime.now()
            reader = csv.reader(form.cleaned_data['file'], delimiter='\t')
            
            lineno = 0
            unrecognized_lines = []
            founded_upc = []
            error_upc = []
            
            retailer = form.cleaned_data['retailer']
            retailer.items.all().delete()
            
            for row in reader:
                lineno += 1
                if lineno == 1:
                    continue
                
                try:
                    UPC, PRODUCT_NAME, PLATFORM, WHOLESALE_PRICE, QUANTITY, DROPSHIP_KEY, DISTRIBUTOR, CONDITION = row #@UnusedVariable
                except:
                    unrecognized_lines.append(lineno)
                    continue
                try:
                    item = Item.objects.get(upc=UPC)
                    founded_upc.append(UPC)
                    
                    di = DistributorItem(
                        distributor = retailer,
                        item=item,
                        wholesale_price = WHOLESALE_PRICE.replace('$',''),
                        quantity = QUANTITY,
                        is_new=True,
                    )
                    di.save()
                    item.recalc_prices()
                    
                except Item.DoesNotExist:
                    not_founded_upc.append(row)
                except:
                    import traceback
                    traceback.print_exc()
                    error_upc.append((UPC, lineno, row)) 

            message = """
Elapsed Time: %s<br />
Total Lines: %d<br />
Unrecognized Lines: %d<br />
Found UPC: %d<br />
Not Found UPC: %d<br />
Error UPC: %d<br />
            """ % (datetime.datetime.now()-dtn, lineno, len(unrecognized_lines), len(founded_upc), len(not_founded_upc), len(error_upc))
            
            if len(error_upc)>0:
                message += '<p><b>Errors:</b><ul>\n'
                message += ''.join("<li>line:%d | %s</li>\n" % (lineno, str(row)) for (upc, lineno, row) in error_upc) #@UnusedVariable
                message += '</ul>\n'
                
            r = ReportUpload(
                created = datetime.datetime.now(),
                type = 'New Inventory and Price',
                source = form.cleaned_data['file'],
                report = message.replace('<br />', ''),
                unknown_upc_count = len(not_founded_upc),
                unknown_upc = '\n'.join(map(lambda x: '\t'.join(x), not_founded_upc))
            )
            r.save()
    else:
        form = UploadInventoryForm()

    return {
        'title': 'Upload New Inventory Feed',
        'form': form,
        'message': message,
        'not_found': '\n'.join(map(lambda x: '\t'.join(x), not_founded_upc)),
    }, None


@transaction.commit_on_success
def upload__used(request, **kwargs):
    class UploadInventoryForm(forms.Form):
        retailer = forms.ModelChoiceField(Distributor.objects.filter(new_games_vendor=False))
        file = forms.FileField()

    message = None    
    not_founded_upc = []
    if request.method == 'POST':
        form = UploadInventoryForm(request.POST, request.FILES)
        if form.is_valid():
            dtn = datetime.datetime.now()
            reader = csv.reader(form.cleaned_data['file'], delimiter='\t')
            
            lineno = 0
            unrecognized_lines = []
            founded_upc = []
            error_upc = []
            
            retailer = form.cleaned_data['retailer']
            retailer.items.all().delete()
            
            for row in reader:
                lineno += 1
                if lineno == 1:
                    continue
                
                try:
                    UPC, PRODUCT_NAME, PLATFORM, WHOLESALE_PRICE, QUANTITY, DROPSHIP_KEY_GAMEMINE, DISTRIBUTOR, CONDITION = row #@UnusedVariable
                except:
                    unrecognized_lines.append(lineno)
                    continue
                try:
                    item = Item.objects.get(upc=UPC)
                    founded_upc.append(UPC)
                    
                    di = DistributorItem(
                        distributor = retailer,
                        item=item,
                        wholesale_price = WHOLESALE_PRICE.replace('$',''),
                        quantity = QUANTITY,
                        is_new=False,
                    )
                    di.save()
                    
                except Item.DoesNotExist:
                    not_founded_upc.append(row)
                except:
                    import traceback
                    traceback.print_exc()
                    error_upc.append((UPC, lineno, row)) 

            message = """
Elapsed Time: %s<br />
Total Lines: %d<br />
Unrecognized Lines: %d<br />
Found UPC: %d<br />
Not Found UPC: %d<br />
Error UPC: %d<br />
            """ % (datetime.datetime.now()-dtn, lineno, len(unrecognized_lines), len(founded_upc), len(not_founded_upc), len(error_upc))
            
            if len(error_upc)>0:
                message += '<p><b>Errors:</b><ul>\n'
                message += ''.join("<li>line:%d | %s</li>\n" % (lineno, str(row)) for (upc, lineno, row) in error_upc) #@UnusedVariable
                message += '</ul>\n'
                
            r = ReportUpload(
                created = datetime.datetime.now(),
                type = 'New Inventory and Price',
                source = form.cleaned_data['file'],
                report = message.replace('<br />', ''),
                unknown_upc_count = len(not_founded_upc),
                unknown_upc = '\n'.join(map(lambda x: '\t'.join(x), not_founded_upc))
            )
            r.save()
    else:
        form = UploadInventoryForm()

    return {
        'title': 'Upload Used Inventory Feed',
        'form': form,
        'message': message,
        'not_found': '\n'.join(map(lambda x: '\t'.join(x), not_founded_upc)),
    }, None
    
    
@transaction.commit_on_success
def upload__used_prices(request, **kwargs):
    class UploadUsedInventoryForm(forms.Form):
        file = forms.FileField()
    
    message = None    
    not_found_upc = []
    if request.method == "POST":
        form = UploadUsedInventoryForm(request.POST, request.FILES)
        if form.is_valid():
            dtn = datetime.datetime.now()
            reader = csv.reader(form.cleaned_data['file'], delimiter='\t')
            
            lineno = 0
            unrecognized_lines = []
            found_upc = []
            error_upc = []

            cursor = connection.cursor() #@UndefinedVariable
#            cursor.execute("update catalog_item set base_retail_price_used='0.0', retail_price_used='0.0', base_trade_price='0.0', trade_price='0.0', trade_price_incomplete='0.0', trade_flag=False")
            cursor.execute("update catalog_item set base_retail_price_used='0.0', retail_price_used='0.0', base_trade_price='0.0', trade_price='0.0', trade_price_incomplete='0.0'")
            
            for row in reader:
                lineno += 1
                if lineno == 1:
                    continue
                
                try:
                    row = [r.decode("utf-8", "ignore") for r in row]
                    UPC, BRE_ID, PLATFORM, PRODUCT, RETAIL_PRICE_USED, TRADE_PRICE_COMPLETE = row #@UnusedVariable
                except:
                    unrecognized_lines.append(lineno)
                    continue

                try:
                    try:
                        item = Item.objects.get(upc=UPC)
                        item.bre_id = BRE_ID 
                    except Item.DoesNotExist:
                        item = Item.objects.get(bre_id=BRE_ID)
                    item.base_retail_price_used = decimal.Decimal(RETAIL_PRICE_USED.replace('$',''))
                    item.base_trade_price = decimal.Decimal(TRADE_PRICE_COMPLETE.replace('$',''))
                    
#                    item.trade_flag = item.base_trade_price != decimal.Decimal('0.0')
                    item.trade_flag = item.trade_flag and item.base_trade_price != decimal.Decimal('0.0')
                    item.recalc_prices(prices=['retail_price_used', 'trade_price'], save=False)
                    
                    item.save()
                    found_upc.append(UPC)
                except Item.DoesNotExist:
                    not_found_upc.append(row)
                except Exception, e:
                    debug(e)
                    error_upc.append((UPC, lineno, row)) 

            message = """
Elapsed Time: %s<br />
Total Lines: %d<br />
Unrecognized Lines: %d<br />
Found UPC: %d<br />
Not Found UPC: %d<br />
Error UPC: %d<br />
            """ % (datetime.datetime.now()-dtn, lineno, len(unrecognized_lines), len(found_upc), len(not_found_upc), len(error_upc))
            
            if len(error_upc)>0:
                message += '<p><b>Errors:</b><ul>\n'
                message += ''.join("<li>line:%d | %s</li>\n" % (lineno, str(row)) for (upc, lineno, row) in error_upc) #@UnusedVariable
                message += '</ul>\n'

            r = ReportUpload(
                created = datetime.datetime.now(),
                type = 'Used Price and Trade Values',
                source = form.cleaned_data['file'],
                report = message.replace('<br />', ''),
                unknown_upc_count = len(not_found_upc),
                unknown_upc = '\n'.join(map(lambda x: '\t'.join(x), not_found_upc))
            )
            r.save()
    else:
        form = UploadUsedInventoryForm()
    
    return {
        'title': 'Upload Used Inventory Prices',
        'form': form,
        'message': message,
        'not_found': '\n'.join(map(lambda x: '\t'.join(x), not_found_upc)),
    }, None


class CheckFormA(forms.Form):
    barcode = forms.CharField()


class CheckFormB(CheckFormA):
    dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), label='DC')


class UPCCheckForm(forms.Form):
    upc = forms.CharField()
    is_new = forms.BooleanField(label='Condition', required=False, 
                                widget=forms.Select(choices=((False, 'UG'), (True, 'NG'))))
    
    def clean_upc(self):
        upc = self.cleaned_data.get('upc')
        try:
            self.item = Item.objects.get(upc__iexact=upc)
        except Item.DoesNotExist:
            raise forms.ValidationError('No game with UPC %s found.' % upc)
        return upc


class UPCCheckFormA(CheckFormA, UPCCheckForm):
    barcode = forms.CharField(widget=forms.HiddenInput())

class UPCCheckFormB(CheckFormB, UPCCheckForm):
    barcode = forms.CharField(widget=forms.HiddenInput())

class ConfirmFormA(forms.Form):
    barcode = forms.CharField(widget=forms.HiddenInput())
    upc = forms.CharField(widget=forms.HiddenInput())
    is_new = forms.BooleanField(widget=forms.HiddenInput(), required=False)

class ConfirmFormB(ConfirmFormA):
    dc = forms.ModelChoiceField(queryset=Dropship.objects.all(), widget=forms.HiddenInput())


def check(request, **kwargs):
    profile = request.user.get_profile()
    dc = profile.dc
    if dc:
        FormClass = CheckFormA
    else:
        FormClass = CheckFormB
    title = 'Process Games (%s)' % dc.code if dc else 'Process Games'
    message = None
    
    if request.method == 'GET':     
        form = FormClass()
        return {
            'title': title,
            'form': form,
        }, None
        
    if 'upc' not in request.POST: # first step
        form = FormClass(request.POST)
        barcode = None
        found_item = None 
        if form.is_valid():
            barcode = request.POST.get('barcode', '')
            FormClass = UPCCheckFormA if dc else UPCCheckFormB
            try:
                inventory = Inventory.objects.get(barcode=barcode)
                upc = inventory.item.upc
                is_new = inventory.is_new
                found_item = inventory.item
            except Inventory.DoesNotExist:
                upc = ''
                is_new = False
                message = 'Inventory <strong>%s</strong> not found in the database. Please enter corresponding UPC.' % barcode
            initial = {
                'barcode': barcode,
                'upc': upc,
                'is_new': is_new,
            }              
            if dc:
                initial['dc'] = dc.id
            elif 'dc' in request.POST:
                initial['dc'] = Dropship.objects.get(id=request.POST['dc']).id
            form = FormClass(initial = initial)

        return {
            'title': title,
            'form': form,
            'barcode': barcode,
            'message': message,
            'found_item': found_item,
        }, None
    
    if 'action' not in request.POST: # second step
        FormClass = UPCCheckFormA if dc else UPCCheckFormB 
        form = FormClass(request.POST)
        barcode = request.POST.get('barcode', '')
        if not form.is_valid():
            return {
                'title': title,
                'form': form,
                'barcode': barcode,
            }, None

        item = form.item
        is_new = form.cleaned_data.get('is_new', False)
        the_dc = dc or form.cleaned_data['dc'] 
        
        FormClass = ConfirmFormA if dc else ConfirmFormB
        form = FormClass(initial=request.POST) 
        return {
            'title': title,
            'form': form,
            'barcode': barcode,
            'item': item,
            'is_new': is_new,
            'dc': the_dc, 
        }, None

    debug(request.POST)
    FormClass = ConfirmFormA if dc else ConfirmFormB
    form = FormClass(request.POST)
    if not form.is_valid():
        debug(form.errors)
        return HttpResponseBadRequest('Bad Request!')
    
    the_dc = dc or form.cleaned_data['dc']
    d = form.cleaned_data
    
    inventory, c = Inventory.objects.get_or_create(barcode=d['barcode'])
    inventory.dropship = the_dc
    inventory.item = Item.objects.get(upc=d['upc'])
    inventory.is_new = d['is_new']
    inventory.not_expected_to_return = False
    inventory.manual_checked = True
    inventory.manual_checked_dc = the_dc
    if c:
        inventory.added_at_manual_check = True
    inventory.manual_check(the_dc)
    inventory.save()

    return redirect('staff:page', 'Inventory/Check')
