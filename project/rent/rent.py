import sys
import re
import itertools
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import LabelCommand
from django.core.urlresolvers import reverse
from django.db import transaction

from django_snippets.utils.datetime.date_utils import inc_months
from endiciapy.endicia import Endicia

from project.rent.allocation_matrix import RentAllocationMatrix
from project.rent.models import MemberRentalPlan, RentOrder, RentList, \
    RentOrderStatus, RentalPlanStatus, RentalPlan, MemberRentalPlanHistory
from project.members.models import BillingCard, BillingHistory,\
    TransactionStatus, TransactionType, Profile
from project.utils.mailer import mail
from project.inventory.models import Dropship, InventoryStatus, Inventory
from project.buy_orders.models import BuyOrderItem
from project.claims.models import Claim


info = logging.getLogger('crontab').info
error = logging.getLogger('crontab').error
debug = logging.getLogger('crontab').debug
warn = logging.getLogger('crontab').warn


class Command(LabelCommand):
    args = '[activate_plans, purge, weight_matrix, process_matrix]'
    help = 'Working with rent plans'
    label = 'command'

    def handle_label(self, label, **options):
        getattr(self, 'do_' + label)()

    def do_purge(self):
        MemberRentalPlan.purge_expired_plans()
        MemberRentalPlan.cleanup_expired_cancellations()
        RentList.purge()

    def do_test(self):
        for o in RentOrder.objects.all():
            o.request_outgoing_mail_label()
            o.request_incoming_mail_label()

    def do_weight_matrix(self):
        for o in RentList.get_priority1():
            w = RentAllocationMatrix.calculate_weight(o)
            debug('Allocation weight for %s - %s %s (%s): %s (old: %s)', o.id, o.item, o.item.category, o.user, w, o.weight)
            if w != o.weight:
                o.weight = w
                o.save()

    def do_allocate_inventory_for_buy_orders(self):
        try:
            from project.management.commands.cart import Command
            Command().handle_label('update_order_items')
        except Exception, _e:
            error('Error occurs when allocate inventory for buy orders', exc_info=sys.exc_info())


    def do_process_matrix(self):
        debug('Allocate inventory for buy orders...')
        self.do_allocate_inventory_for_buy_orders()
        debug('Canceling dead plans...')
        MemberRentalPlan.cancel_dead_plans()
        debug('Canceling expired plans...')
        MemberRentalPlan.cancel_expired_plans()
        debug('Calculating weights...')
        self.do_weight_matrix()
        debug('OK')
        debug('Processing matrix...')
        for o in RentList.get_priority1():
            debug('--------------------------')
            debug('Allocation matrix for %s - %s %s (%s) %s', o.id, o.item, o.item.category, o.user, o.weight)
            RentAllocationMatrix.process_item(o)
        debug('OK')
        
    def do_move_orders(self):
        info('Moving orders...', extra={'url': 'task://rent/move_orders'})
        for o in RentOrder.objects.filter(status=RentOrderStatus.Pending):
            try:
                if o.source_dc.is_game_available(o.item, exclude_rent_order=o, for_rent=True):
                    continue
                p = o.user.get_profile()
                zip = p.shipping_zip
                if not zip:
                    o.put_back_to_list()
                    continue
                o.source_dc = None
                o.save()
                dc = Dropship.find_closest_dc(zip, o.item, p.dropship)
                if dc:
                    o.source_dc = dc
                    o.save()
                    info('%s --> %s  %s', o.source_dc.code, dc.code, o)
                else:
                    info('Put back to list  %s', o)
                    o.put_back_to_list()
            except Exception, _e:
                error('Error occurs when moving order %s', o.id,
                      exc_info=sys.exc_info(), extra={'url': reverse('staff:rent_order_details', args=[o.id])})
        info('Moving orders... DONE', extra={'url': 'task://rent/move_orders'})
        
    def do_update_shipped_statuses(self):
        def parse_time(s):
            try:
                s = re.search(r'(?P<time>\d{2}:\d{2} (AM|PM) on \d{2}/\d{2}/\d{4})', s).groupdict()['time']
                d = datetime.strptime(s, '%I:%M %p on %m/%d/%Y')
            except Exception, e:
                debug(e)
                d = datetime.now()
            debug(d)
            return d
        
        endicia = Endicia(**settings.ENDICIA_CONF)
        info('Checking mail shipped statuses...', extra={'url': 'task://rent/update_shipped_statuses'})
        for order in RentOrder.objects.filter(status=RentOrderStatus.Shipped, date_delivered=None):
            try:
                pic = order.outgoing_tracking_number
                if not pic:
#                    warn('No PLANET ID (outgoing) for this order',
#                          extra={'url': reverse('staff:rent_order_details', args=[order.id])})
                    continue
                res = endicia.status_request(pic)
                code = res.StatusList.PICNumber.StatusCode
                debug('%s: %s %s', pic, code, res.StatusList.PICNumber.Status)
                if code == 'D':
                    order.date_delivered = parse_time(res.StatusList.PICNumber.Status)
                scans = order.outgoing_tracking_scans or {}
                if code != '0' and code not in scans:
                    scans[code] = datetime.now()
                    order.outgoing_tracking_scans = scans
                    order.save()
                    order.add_mail_tracking_scan_event(code)
            except Exception, _e:
                error('Error occurs when processing order %s', order.id,
                      exc_info=sys.exc_info(), extra={'url': reverse('staff:rent_order_details', args=[order.id])})
        info('Checking return shipped statuses...', extra={'url': 'task://rent/update_shipped_statuses'})
        for order in RentOrder.objects.filter(status=RentOrderStatus.Shipped, date_shipped_back=None):
            try:
                pic = order.incoming_tracking_number
                if not pic:
#                    warn('No PLANET ID (incoming) for this order',
#                          extra={'url': reverse('staff:rent_order_details', args=[order.id])})
                    continue
                res = endicia.status_request(pic)
                code = res.StatusList.PICNumber.StatusCode
                debug('%s: %s %s', pic, code, res.StatusList.PICNumber.Status)
                if code == 'A':
                    order.date_shipped_back = parse_time(res.StatusList.PICNumber.Status)
                scans = order.incoming_tracking_scans or {}
                if code != '0' and code not in scans:
                    scans[code] = datetime.now()
                    order.incoming_tracking_scans = scans
                    order.save()
                    order.add_return_tracking_scan_event(code)
            except Exception, _e:
                error('Error occurs when processing order %s', order.id,
                      exc_info=sys.exc_info(), extra={'url': reverse('staff:rent_order_details', args=[order.id])})


    def do_recurring_billing(self):
        date_x = datetime.now().date()
        info('Start recurring billing process (%s)', date_x, extra={'url': 'task://rent/recurring_billing'})
        qs = MemberRentalPlan.objects.filter(status=RentalPlanStatus.Active)
        qs = qs.filter(next_payment_date__lte=date_x).exclude(user__email__in=self.plan_with_billing_problem)
        if settings.DEBUG:
            qs = qs.filter(user__id=1)
        for member_plan in qs:
            try:
                if member_plan.scheduled_plan is not None:
                    member_plan.activate_scheduled_plan()
                else:
                    member_plan.take_recurring_billing()
            except Exception, _e:
                user = member_plan.user
                user_id = user.id if user else None
                user_email = user.email if user else None
                error('Error occurs when processing payment for rental plan: %s (%s, %s)', member_plan.id, user_id, user_email,
                      exc_info=sys.exc_info(), extra={'url': 'task://rent/recurring_billing'})
        info('Recurring billing process finished (%s)', date_x, extra={'url': 'task://rent/recurring_billing'})


    def do_delinquent_billing(self):
        date_x = datetime.now().date()
        info('Start delinquent billing process (%s)', date_x, extra={'url': 'task://rent/delinquent_billing'})
        qs = MemberRentalPlan.objects.filter(status=RentalPlanStatus.Delinquent)
        qs = qs.filter(delinquent_next_check__lte=date_x)
        if settings.DEBUG:
            qs = qs.filter(user__id=1)
        for member_plan in qs:
            try:
                member_plan.take_delinquent_payment()
            except Exception, _e:
                user = member_plan.user
                user_id = user.id if user else None
                user_email = user.email if user else None
                error('Error occurs when processing payment for rental plan: %s (%s, %s)', member_plan.id, user_id, user_email,
                      exc_info=sys.exc_info(), extra={'url': 'task://rent/delinquent_billing'})
        info('Delinquent billing process finished (%s)', date_x, extra={'url': 'task://rent/delinquent_billing'})
            
    
    def do_fix(self):
        for member_plan in MemberRentalPlan.objects.filter():
            cc = BillingCard.get(member_plan.user)
            if isinstance(cc.data, str):
                cc.data = None
                cc.save()

    def do_send_empty_list_nofitications(self):
        debug('Sending "empty" rent list notifications...')
        qs = MemberRentalPlan.objects.filter(status=RentalPlanStatus.Active)
        for member_plan in qs:
            if RentList.get(member_plan.user).count() < 10:
                user = member_plan.user
                debug('  Send to %s...', user.email)
                mail(user.email, 'emails/rent_emails/add_more_games.html', {
                    'user': user,
                }, subject='Your Rent List is Low! - Add More Games')
                
    #ernestorx
    def do_change_all_pending_to_active(self):
        ''' management command to switch members from pending to active
        '''
        debug('Switching all Members rental plans from pending to active...')
        qs = MemberRentalPlan.objects.filter(status=RentalPlanStatus.Pending)
        for member_plan in qs:
            #malcala
            # Capturing first payment
            member_plan.capture_1b()          
            # going to active
            member_plan.scheduled_plan = member_plan.plan
            member_plan.save()  
            member_plan.activate_scheduled_plan()
            #member_plan.activate(member_plan.plan)
            member_plan.save()   

#    @transaction.commit_on_success
    def do_process_cancellations(self):
        debug('Processing expired plans...')
        for p in MemberRentalPlan.objects.filter(status=RentalPlanStatus.Expired):
            user = p.user
            orders = RentOrder.list_stolen_games(user)
            if orders.count() == 0:
                p.delete()
                continue

            for order in orders.filter(penalty_payment=None):
                order.take_penalty_payment()

            if p.expiration_date > datetime.now().date() - timedelta(10):
                continue
            
            if p.buy_games_at_home():
                p.delete()
                continue
            
            p.status = RentalPlanStatus.Collection
            p.save()
            
        debug('Processing plans that could be canceled...')
        for p in MemberRentalPlan.objects.filter(status=RentalPlanStatus.CanceledP):
            user = p.user
            orders = RentOrder.list_stolen_games(user)
            if orders.count() == 0:
                debug("There is no games at home. Subscription could be canceled")
                p.finish_cancellation()
                continue
            
            if not p.cancellation_date:
                continue
            if orders.filter(date_rent__lt=datetime(2010, 10, 1)).count():
                # FIXME: temporary stub
                continue
            has_claims = False
            for o in orders:
                has_claims = o.claims().count() > 0
                if has_claims: break
            if has_claims:
                continue
            if p.cancellation_date < datetime(2010, 12, 23).date() - timedelta(10):
                p.cancellation_date = None 

            debug('Processing %s...', p.user)

            for order in orders.filter(penalty_payment=None):
                order.take_penalty_payment()

            if not p.cancellation_date:
                p.cancellation_date = datetime.now().date()
                p.save()

            date_x = datetime.now().date() - timedelta(10)
            
            if p.cancellation_date > date_x:
                debug("User has %s day(s) to return rented games", (p.cancellation_date - date_x).days)
                continue
            
            if p.buy_games_at_home():
                debug("All games are sold. Subscription could be canceled")
                p.finish_cancellation()
                continue
            
            debug('Changing plan status to "Collection"...')
            p.status = RentalPlanStatus.Collection
            p.save()
            
        debug('Processing plans that was suspended...')
        for p in MemberRentalPlan.objects.filter(status=RentalPlanStatus.Suspended):
            user = p.user
            orders = RentOrder.list_stolen_games(user)
            if orders.count() == 0:
                continue

            debug('Processing %s...', p.user)

            for order in orders.filter(penalty_payment=None):
                order.take_penalty_payment(penalty_reason=('SUSP', 'Rent Suspension'))

            date_x = datetime.now() - timedelta(10)
            
            if p.suspend_date is None:
                p.suspend_date = datetime.now()
                p.save()
            if p.suspend_date > date_x:
                debug("User has %s day(s) to return rented games", (p.suspend_date - date_x).days)
                continue
            
            if p.buy_games_at_home(description='Rent Suspension', penalty_reason=('SUSP', 'Rent Suspension')):
                continue
            
            debug('Changing plan status to "Collection"...')
            p.status = RentalPlanStatus.Collection
            p.save()

    @transaction.commit_on_success
    def do_fix_rental_plans(self):
        today = datetime.now().date()
        def calc_next_payment_date(start_date, period):
            d = start_date.date() if isinstance(start_date, datetime) else start_date
            while d < today:
                d = inc_months(d, period, start_date)
            return d
        
        debug('Fixing rental plans...')
        qs = MemberRentalPlan.objects.filter(status=RentalPlanStatus.Active)
        debug('Going to fix %d of plans...', qs.count())
        for p, i in itertools.izip(qs, itertools.count(1)):
            if i % 100 == 0:
                debug(i)
            expire_in = RentalPlan.get_expire_in(p.plan)
            if expire_in:
                p.expiration_date = inc_months(p.start_date, expire_in, p.start_date)
                p.next_payment_amount = None
                p.next_payment_date = None
                if p.status == RentalPlanStatus.Active and p.expiration_date < today:
                    p.set_status(RentalPlanStatus.CanceledP, save=False)
            else:
                p.expiration_date = None
                _pd, amount = RentalPlan.get_next_payment(p.plan, p.start_date, datetime.now())
                reccuring_period = RentalPlan.get_reccuring_period(p.plan)
                p.next_payment_amount = amount
                p.next_payment_date = calc_next_payment_date(p.start_date, reccuring_period)
            p.save()

    @transaction.commit_on_success
    def do_fix_rent_orders(self):
        qs = RentOrder.objects.filter(status=RentOrderStatus.Returned)
        print 'Checking %s of rent orders...' % qs.count()
        for r, i in itertools.izip(qs, itertools.count(1)):
            if i % 100 == 0:
                print i
            for r1 in RentOrder.objects.filter(status=RentOrderStatus.Shipped, item=r.item, user=r.user):
                if r1.date_rent.date() == r.date_rent.date():
                    print '%s\t%s\t%s' % (r.user.id, r.id, r1.id)
                    r1.delete()


    def do_armageddon(self):
        qs = Inventory.objects.filter(status__in=[InventoryStatus.Pending])
        for i in qs:
            if RentOrder.objects.filter(status=RentOrderStatus.Prepared, inventory=i):
                continue
            if BuyOrderItem.objects.filter(inventory=i).count():
                continue
            print '%s\t%s\t%s\t%s\t%s' % (i.barcode, 'NG' if i.is_new else 'UG', i.item.short_name, i.item.category.name, i.item.upc) 


    def do_superfix(self):
        for o in RentOrder.objects.filter(status=RentOrderStatus.Prepared):
            if o.source_dc.code != o.inventory.dropship.code:
                inventory_barcode = o.inventory.barcode
                o.status = RentOrderStatus.Pending
                o.inventory = None
                o.save()
                if RentOrder.objects.filter(status=RentOrderStatus.Prepared, inventory__barcode=inventory_barcode).count() == 0:
                    invenrory = Inventory.objects.get(barcode=inventory_barcode)
                    invenrory.status = InventoryStatus.InStock
                    invenrory.save() 
            

    def do_cleanup_picked_list(self):
        for o in RentOrder.objects.filter(status=RentOrderStatus.Pending):
#            dc = Dropship.find_closest_dc(o.shipping_zip_code, o.item, None)
#            if dc:
#                continue
            o.put_back_to_list()

    def do_fml(self):
        count = 0
        print '\t'.join(('DB VAL', 'EST', 'BARCODE ID', 'TITLE', 'PLATFORM', 'UPC'))
        for i in Inventory.objects.filter(status=InventoryStatus.InStock):
            orders = RentOrder.objects.filter(inventory=i, status=RentOrderStatus.Returned, date_returned__gt=datetime(2010, 11, 1)).order_by('-date_returned')
            if not orders:
                continue
            order = orders[0]
            home_dc = order.user.get_profile().dropship
            if not home_dc or i.dropship == home_dc:
                continue
            print '\t'.join((i.dropship.code, home_dc.code, i.barcode, i.item.short_name, i.item.category.name, i.item.upc))
            i.tmp_saved_dc_code = i.dropship.code
            i.dropship = home_dc
            i.save()
            count += 1
        print count

    def do_fix_refund(self):
        for h in MemberRentalPlanHistory.objects.filter(status=RentalPlanStatus.Canceled, 
                                                        start_date__gt=datetime(2010, 11, 2), 
                                                        finish_date__gte=datetime(2010, 11, 2)).select_related():
            orders = RentOrder.objects.filter(user=h.user, date_rent__gte=h.start_date, date_rent__lte=h.finish_date)
            if orders.count():
                continue
            billing = BillingHistory.objects.filter(user=h.user, timestamp__gte=h.start_date, timestamp__lte=h.finish_date, 
                                                    status=TransactionStatus.Passed, type=TransactionType.RentPayment)
            if not billing or billing.count() > 1:
                continue
            billing = billing[:][0]
            if billing.get_refund():
                continue
             
            print 'http://gamemine.com/Staff/Customer-Billing-History/%s/' % h.user.id
#            print h.start_date, h.finish_date, h.user.id, h.user.email
#            print '\t', billing.timestamp, billing.get_status_display()

    def do_fix_2x_speed(self):
        for o in RentOrder.objects.filter(status=RentOrderStatus.Shipped, scanned_in_route=False, user__profile__strikes=0):
            plan = MemberRentalPlan.get_current_plan(o.user)
            if not plan or plan.status != RentalPlanStatus.Active:
                continue
            if Claim.list(o).count():
                continue
            
            scans = o.incoming_tracking_scans or {}
            if 'I' in scans or 'D' in scans or 'A' in scans:
                d = scans.get('I', scans.get('D', scans.get('A')))
                d = datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
                if not d or d <= datetime.now() - timedelta(7):
                    continue
                o.scanned_in_route = True
                o.save()
                p = o.user.get_profile()
                p.extra_rent_slots += 1
                p.save()
                print o

    def do_reactivate_held(self):
        today = datetime.now().date()
        plans = MemberRentalPlan.objects.filter(status=RentalPlanStatus.OnHold, hold_reactivate_timestamp__lte=today)
        for plan in plans:
            plan.reactivate()

    def do_charge_held(self):
        for p in MemberRentalPlan.objects.filter(status=RentalPlanStatus.OnHold):
            user = p.user
            orders = RentOrder.objects.filter(user=user, status=RentOrderStatus.Shipped)
            if orders.count() == 0:
                continue

            for order in orders.filter(penalty_payment=None):
                order.take_penalty_payment(penalty_reason=('HOLD', 'Hold Account'))

            date_x = datetime.now().date() - timedelta(7)
            
            if p.hold_start_timestamp.date() > date_x:
                continue
            
            if p.buy_games_at_home(description='Hold Account', penalty_reason=('HOLD', 'Hold Account')):
                continue
            
            p.status = RentalPlanStatus.Collection
            p.save()

    def do_fix_2x_speed2(self):
        for p in Profile.objects.filter(extra_rent_slots__gt=0):
            p.extra_rent_slots = RentOrder.objects.filter(status=RentOrderStatus.Shipped, scanned_in_route=True, user=p.user).count()
            p.save()
        for p in Profile.objects.filter(extra_rent_slots__gt=0):
            extra_rent_slots = p.extra_rent_slots
            for o in RentOrder.objects.filter(status=RentOrderStatus.Pending, user=p.user):
                o.speed_2x = True
                o.save()
                extra_rent_slots -= 1
                if extra_rent_slots == 0:
                    break
            p.extra_rent_slots = extra_rent_slots
            p.save()


    plan_with_billing_problem = ['erika.seaton@gmail.com', 'ejack05@gmail.com', 'stauf@verizon.net', 'navarrojose@me.com', 'mlhimes1@aol.com', 'rdavonlady@aol.com', 'charlie_roberts4@yahoo.com', 'ahackney2@yahoo.com', 'crystalknopp@gmail.com', 'spqzx@yahoo.com', 'sitlrcs@yahoo.com', 'johnh1803@gmail.com', 'admin@courtsofpraise.net', 'robinsontaylore@gmail.com', 'ras3562003@yahoo.com', 'bloodyd33@gmail.com', 'cmr44fan@prtcnet.com', 'chanikya.konda@gmail.com', 'Josh@Dallmanconstruction.com', 'parandehgheibi@yahoo.com', 'Taforo86@Live.com', 'Barbaraputman@windstream.net', 'c.cooleyhigh@yahoo.com', 'dkersey1@roadrunner.com', 'kymberlis_kreations@hotmail.com', 'rlongo7088@aol.com', 'sspeakerboy@hotmail.com', 'Jeeper114@msn.com', 'lmbornstein@hotmail.com', 'murphy91371@gmail.com', 'PALUMB@aol.com', 'timothylfoley@hotmail.com', 'EllenReagan001@yahoo.com', 'thebrowns2kids@comcast.net', 'shelly_gulseth@hotmail.com', 'todd82477@verizon.net', 'mhayes088@gmail.com', 'vdayoboy@hotmail.com', 'cwrudy@roadrunner.com', 'alejandra.sainz@lausd.net', 'arshiamghddm@aol.com', 'joecena12@gmail.com', 'jallenbennett@gmail.com', 'autumn.amos@att.net', 'gladysbencosme@yahoo.com', 'karenhunter1@comcast.net', 'dwells113@comcast.net', 'art.farooqi@yahoo.com', 'mrgbilia@gmail.com', 'seanwiseman06@gmail.com', 'ryan_p_emerson@yahoo.com', 'mkstanley88@yahoo.com', 'nerdrocker89@gmail.com', 'austin.lebaron@yahoo.com', 'hollerinmatt1@hotmail.com', 'cook.terry3@gmail.com', 'Gkain11@gmail.com', 'Jennyfirlynn68@msn.com', 't7persico@gmail.com', 'Bridgette.clifton@hotmail.com', 'davidperry5.0@gmail.com', 'alexandriagore@gmail.com', 'nategrundy@yahoo.com', 'jarrinmorris@yahoo.com', 'beaman.mary66@yahoo.com', 'bigbob0524@yahoo.com', 'margretecortez@yahoo.com', 'karins2cool@yahoo.com', 'Marco.verussa@live.com', 'Mike.mac530@gmail.com', 'dmrdfl@aol.com', 'eazy.marq@yahoo.com', 'epahule@sbcglobal.net', 'landism27@windstream.net', 'hometrainingpt@hotmail.com', 'Jasonoveson@comcast.net', 'Shelton_sekac@hotmail.com', 'elpingu2001@aol.com', 'bethas20@hotmail.com', 'saradon79@yahoo.com', 'mayoph9@yahoo.com', 'timotyy1@verizon.net', 'robertalee.smith@gmail.com', 'bwilliams0194@kctcs.edu', 'realbrownsugar2000@yahoo.com', 'rgruiz22@yahoo.com', 'liammaher@carolina.rr.com', 'crankitup99@yahoo.com', 'mindynasers@yahoo.com', 'bugg200@aol.com', 'atjl0701@hotmail.com', 'zoo-keeper@att.net', 'sarahjanehuber@yahoo.com', 'ogim424@yahoo.com', 'tisaunde@uncc.edu', 'raypat210@hotmail.com', 'dortega9@hotmail.com', 'JULIERSMITH42106@AOL.COM', 'lyle_becky@yahoo.com', 'mbaires._@yahool.com', 'thejoshcampbell@yahoo.com', 'whitcherm@msn.com', 'mr_niceguy3241972@yahoo.com', 'paperbackcafe1@yahoo.com', 'bearlake93@aol.com', 'kaoskweed@aol.com', 'michellelovesavon@yahoo.com', 'carcreditpro@gmail.com', 'the_cwb_inc@yahoo.com', 'whaleymichael1030@gmail.com', 'A.longhair@comcast.net', 'Chris71Lee@aol.com', 'denzell.eskridge@gmail.com', 'rolando.nj@gmail.com', 'christopher118102@gmail.com', 'rkornegay123@yahoo.com', 'Livlif63@aol.com', 'fbcjeff@comcast.net', 'lvanburen1@gmail.com', 'hustle97@att.net', 'dacoda90frist@gmail.com', 'peterskellie@yahoo.com', 'hchildress1973@aol.com', 'hajikarimi.mohammad@gmail.com', 'computeremt@live.com', 'garnanathome@aol.com', 'd.forrester8@yahoo.com', 'rickkarch@gmail.com', 'christopher_walsh82@hotmail.com', 'kahkalkay@yahoo.com', 'b.payne24@hotmail.com', 'baileyjim73@yahoo.com', 'kingphilly1988@aol.com', 'basses.96@hotmail.com', 'farrowdeshawn@yahoo.com', 'esther.duran@ymail.com', 'grazhero@live.com', 'seanwhall@ymail.com', 'j1c1con1@yahoo.com', 'jwattsjmd@gmail.com', 'kimberly6867@yahoo.com', 'graysonhatcher@yahoo.com', 'melissasolovely@yahoo.com', 'alisha.brower@students.globeuniversity.edu', 'laithsa@yahoo.com', 'mrsflyingj@yahoo.com', 'jesse_baric@yahoo.com', 'lyoung9643@comcast.net', 'sadiebelle588@yahoo.com', 'deborahsilvers@gmail.com', 'youngatlam@yahoo.com', 'cgparkerpark@bex.net', 'ajvickers81@yahoo.com', 'donwilsonisdead@gmail.com', 'ckeys2u@yahoo.com', 'gspcollins@gmail.com', 'zappakin@q.com', 'melissatanco@gmail.com', 'lakemcallister@gmail.com', 'erneststinson@yahoo.com', 'tancalhoun@hotmail.com', 'daveherbison@gmail.com', 'ualicea@gmail.com', 'mistergqstyle@aim.com', 'bigbadjoerasky@yahoo.com', 'budwiser6921@yahoo.com', 'danizita@live.com', 'shawnspitzer2001@hotmail.com', 'sylvialohry2007@gmail.com', 'brf11@mail.fresnostate.edu', 'minigenius93@yahoo.com', 'justin.stotts@gmail.com', 'rolandjudy@verizon.net', 'dittyditty@gmail.com', 'joaks1983@gmail.com', 'Yvholman53@comcast.net', 's.mobley881@gmail.com', 'paolucci.10@gmail.com', 'phillipsnicole7@aol.com', 'stuntboy4hire@gmail.com', 'JJ0521@clear.net', 'cwrm72@mac.com', 'amykinzleelogan2010@hotmail.com', 'jamespshorter@gmail.com', 'chetlee.cl@gmail.com', 'tjjordan_2186@yahoo.com', 'rosettasanni_thomas@hotmail.com', 'lilshaka9tre@yahoo.com', 'phinsfan87@yahoo.com', 'nickcorradi@yahoo.com', 'loripaup@yahoo.com', 'EWashington82@gmail.com', 'jayrichard1230@gmail.com', 'holydeg@cox.net', 'ryandowd2000@yahoo.com', 'jbapril.9802@yahoo.com', 'mrs.material@gmail.com', 'kchd@sbcglobal.net', 'jgcurtis81@yahoo.com', 'ebaynae@yahoo.com', 'camperman1956@yahoo.com', 'anthony.davis32@twcable.com', 'rodzilla7531@gmail.com', 'oatesjc87@yahoo.com', 'Spyderella2007@comcast.net', 'Nr64147@huskies.bloomu.edu', 'pat_black8@yahoo.com', 'scott.vanderlugt@me.com', 'phpaihw@aol.com', 'smith2088@yahoo.com', 'sparklezprincess@hotmail.com', 'mjperez1227@yahoo.com', 'kalamkins@hotmail.com', 'hjake1996@live.com', 'floydtjb@gmail.com', 'diogratius@yahoo.com', 'victoriajspringer@gmail.com', 'dan.n99@live.com', 'andruska22@hotmail.com', 'gustavoreyes12@yahoo.com', 'dlotowski@hotmail.com', 'bickford08@peoplepc.com', 'bhenry13@uga.edu', 'mccauley.emi@gmail.com', 'karen_ford@bellsouth.net', 'ksandgirls05@att.net', 'leesajones19@hotmail.com', 'tomswift321@yahoo.com', 'lazzar85@gmail.com', 'stacyl@allwest.net']
    def do_fix_next_payment_none(self):
        logger = logging.getLogger()
        hdlr = logging.FileHandler("d://planissue.log" )
        formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s"%(message)s"','%Y-%m-%d %a %H:%M:%S') 
        hdlr.setFormatter(formatter)        
        logger.addHandler(hdlr)
        logger.setLevel(logging.INFO)
        date_x = datetime.now().date()
        qs = MemberRentalPlan.objects.filter(user__email__in=self.plan_with_billing_problem,status=RentalPlanStatus.Active)
        logger.info('total plans %d ' % qs.count())
        for member_plan in qs:
            try:
                if member_plan.start_date is None:
                    member_plan.start_date = date_x
                    member_plan.save()
                if member_plan.next_payment_date is None:
                    np = RentalPlan.get_next_payment(member_plan.plan, member_plan.start_date, member_plan.start_date)               
                    member_plan.next_payment_date, member_plan.next_payment_amount = np
                    member_plan.save()
                if member_plan.next_payment_date <= date_x:
                    if member_plan.scheduled_plan is not None:
                        member_plan.activate_scheduled_plan(fix_next_payment_none=member_plan.next_payment_date)
                    else:
                       if member_plan.take_recurring_billing(force_future_date=False):
                           logger.info('%s charged' % member_plan.user.id )
                       else:
                           logger.info('%s failed' % member_plan.user.email )
                       
            except Exception, _e:
                print _e
                pass
        qs = MemberRentalPlan.objects.filter(user__email__in=self.plan_with_billing_problem,status=RentalPlanStatus.Active,next_payment_date__lte=date_x)
        logger.info('it needs still to be charged %d' % qs.count())


