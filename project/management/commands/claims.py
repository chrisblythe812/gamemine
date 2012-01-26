import sys
from datetime import datetime, timedelta
import itertools

from django.core.management.base import LabelCommand

from project.claims.models import Claim, SphereChoice, DontReceiveClaim,\
    GamemineNotReceiveGameClaim, WrongGameClaim, GameIsDamagedClaim
from project.crm.models import CaseStatus
from project.rent.models import RentOrder, RentOrderStatus, MemberRentalPlan,\
    RentalPlanStatus
from project.members.models import Profile
from project.inventory.models import InventoryStatus


class Command(LabelCommand):
    def _get_args(self):
        for m in dir(self):
            if m.startswith('do_'):
                yield m[3:]

    help = 'Working with endicia'
    label = 'command'

    def handle_label(self, label, **options):
        try:
            method = getattr(self, 'do_' + label)
        except:
            print >>sys.stderr, 'Possible commands are: %s' % ', '.join(self._get_args())
            return
        self._items_cache = {}
        self._missing_items = set()
        method()

    def _get_cursor(self):
        import MySQLdb
        if not hasattr(self, 'mconn'):
            self.mconn = MySQLdb.connect(host='78.31.177.17', db="gamemine", user='gamemine', passwd='1')
        return self.mconn.cursor()


    def do_load_old_claims(self):
        Claim.objects.filter(content_type__id=21).delete()
        Claim.objects.filter(imported=True).delete()

        c = self._get_cursor()
        c.execute("""
            select
                r.id, r.ref_user, i.upc, r.ref_sent_item, h.sent_date, r.sent_code, r.ref_shipping_problem, r.add_date, r.processed
            from shipping_problem_reports r
                inner join items i on i.id = r.ref_item
                inner join history_records h on h.id = r.ref_history_record
            where reported_by = 'member';
        """, [])

        for id, ref_user, _upc, _ref_sent_item, sent_date, sent_code, ref_shipping_problem, add_date, processed in c.fetchall():
            d1 = sent_date - timedelta(1)
            d2 = sent_date + timedelta(1)
            order = RentOrder.objects.filter(user__id=ref_user, inventory__barcode=sent_code, date_rent__gt=d1, date_rent__lt=d2)
            if not order:
                continue
            order = order[0]

            data = {
                'claim_object': order,
                'user_id': ref_user,
                'date': add_date,
                'sphere_of_claim': SphereChoice.Rent,
                'status': CaseStatus.New if processed == 0 else CaseStatus.Closed,
                'imported': True,
                'tmp_processed': processed,
                'old_claim_id': id,
            }

            if ref_shipping_problem == 1:
                p = Profile.objects.get(user__id=ref_user)
                data.update(p.get_name_data())
                data.update(p.get_shipping_address_data('shipping'))
                data.pop('shipping_county', None)
                DontReceiveClaim(**data).save()
            elif ref_shipping_problem == 2:
                data['mailed_date'] = add_date - timedelta(7)
                GamemineNotReceiveGameClaim(**data).save()
            elif ref_shipping_problem in [3, 4, 5, 6]:
                data['game_not_in_list'] = ref_shipping_problem in [3, 5]
                data['game_not_match_white_sleeve'] = ref_shipping_problem in [4, 6]
                WrongGameClaim(**data).save()
            else:
                data['game_is_scratched'] = ref_shipping_problem == 7
                GameIsDamagedClaim(**data).save()

    def do_fix(self):
        for r in RentOrder.objects.exclude(status__in=[RentOrderStatus.Shipped, RentOrderStatus.Prepared, RentOrderStatus.Pending]):
            claims = Claim.list(r).filter(status=CaseStatus.New)
            for c in claims:
                c.status = CaseStatus.AutoClosed
                c.save()
        for c in GamemineNotReceiveGameClaim.objects.filter(status__in=[CaseStatus.New, CaseStatus.Closed], sphere_of_claim=SphereChoice.Rent):
            rent_order = c.claim_object
            scans = rent_order.incoming_tracking_scans or {}
            if 'I' in scans or 'A' in scans or 'D' in scans:
                rent_order.inventory.status = InventoryStatus.USPSLost
            else:
                p = rent_order.user.get_profile()
                p.inc_strikes(1, True)
                rent_order.inventory.status = InventoryStatus.Lost
            rent_order.inventory.save()
            rent_order.status = RentOrderStatus.Claim
            rent_order.save()
            for cc in Claim.list(rent_order):
                cc.status = CaseStatus.AutoClosed
                cc.save()
        for c in DontReceiveClaim.objects.filter(status__in=[CaseStatus.New, CaseStatus.Closed], sphere_of_claim=SphereChoice.Rent):
            rent_order = c.claim_object
            scans = rent_order.outgoing_tracking_scans or {}
            if 'I' in scans or 'A' in scans or 'D' in scans:
                p = rent_order.user.get_profile()
                p.inc_strikes(1, True)
                rent_order.inventory.status = InventoryStatus.Lost
            else:
                rent_order.inventory.status = InventoryStatus.USPSLost
            rent_order.inventory.save()
            rent_order.status = RentOrderStatus.Claim
            rent_order.save()
            for cc in Claim.list(rent_order):
                cc.status = CaseStatus.AutoClosed
                cc.save()

        for c in WrongGameClaim.objects.filter(status__in=[CaseStatus.New], sphere_of_claim=SphereChoice.Rent):
            c.next_penalty_payment_date = c.date + timedelta(10)
            c.status = CaseStatus.AutoClosed
            c.save()
            rent_order = c.claim_object
            p = rent_order.user.get_profile()
            p.inc_strikes(1, True)

        for c in GameIsDamagedClaim.objects.filter(status__in=[CaseStatus.New], sphere_of_claim=SphereChoice.Rent):
            c.next_penalty_payment_date = c.date + timedelta(10)
            c.status = CaseStatus.AutoClosed
            c.save()
            # MVI-005: Commented out lines below since it makes second strike on user for damages game (first strike
            # was done upon filling claim by user)
            # rent_order = c.claim_object
            # p = rent_order.user.get_profile()
            # p.inc_strikes(1, True)

        for p in Profile.objects.filter(strikes=3):
            p.suspend_rent_account()


    def do_take_penalty_payments(self):
        def list_claims(cls):
            qs = cls.objects.exclude(next_penalty_payment_date=None)
            qs = qs.filter(next_penalty_payment_date__lte=datetime.now())
            return qs

        for c in itertools.chain(list_claims(GameIsDamagedClaim), list_claims(WrongGameClaim)):
            # ernestorx
            # refund Customers when no games have been shipped (current process)
            # and has minimum of seven (7) released games (date equal to or less than today)
            # on rent list for 15-day consecutive concurrent days.
            r, _aim_result = c.take_penalty_payment()
            if not r:
                if c.penalty_payment_tries > 5:
                    c.next_penalty_payment_date = None
                    c.save()
                    plan = MemberRentalPlan.get_current_plan(c.user)
                    plan.status = RentalPlanStatus.Collection
                    plan.save()
