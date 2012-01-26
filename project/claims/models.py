from logging import debug #@UnusedImport
import decimal
from datetime import datetime, timedelta

from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from project.crm.models import CASE_STATUSES, CaseStatus
from project.utils import create_aim
from project.members.models import BillingHistory, TransactionType,\
    TransactionStatus
from project.utils.mailer import mail
    

class SphereChoice:
    Buy = 0
    Trade = 1
    Rent = 2

SPHERE_CHOICES = (
    (SphereChoice.Buy, 'Buy'),
    (SphereChoice.Trade, 'Trade'),
    (SphereChoice.Rent, 'Rent'),
)

SPHERE_REVERSED_DICT = dict(map(lambda x: [x[1], x[0]], SPHERE_CHOICES))

class ClaimType:
    GameIsDamaged = 0
    WrongGame = 1
    DontRecieve = 2
    MailerIsEmpty = 3
    GamemineNotReceiveGame = 4
    GamemineNotReceiveTradeGame = 5
    WrongTradeValueCredit = 6
    

CLAIM_TYPES = (
    (0, 'Game is damaged, scratched or unplayable'),
    (1, 'I received the wrong Game'),
    (2, 'I haven\'t received the Game'),
    (3, 'The mailer was empty'),
    (4, 'I mailed the game back but Gamemine has not received it'),
    (5, 'I mailed the game but Gamemine has not received it'),
    (6, 'I received the wrong trade value credit for my game'),
)

CLAIM_TITLES = (
    (0, 'Damaged Game'),
    (1, 'Wrong Game'),
    (2, 'Lost Game'),
    (3, 'Empty mailer'),
    (4, 'I mailed the game back but Gamemine has not received it'),
    (5, 'I mailed the game but Gamemine has not received it'),
    (6, 'I received the wrong trade value credit for my game'),
)
CLAIM_TITLES_DICT = dict(CLAIM_TITLES)

CLAIM_NORMALIZED_TITLES = (
    (0, 'Damaged Game'),
    (1, 'Wrong Game Received'),
    (2, 'Lost'),
    (3, 'Empty mailer'),
    (4, 'Lost (returned)'),
    (5, 'Lost (trade)'),
    (6, 'Wrong trade value credit'),
)
CLAIM_NORMALIZED_TITLES_DICT = dict(CLAIM_NORMALIZED_TITLES)

class Claim(models.Model):
    class Meta:
        ordering = ['date']
    
    content_type = models.ForeignKey(ContentType, editable=False)
    object_id = models.PositiveIntegerField(editable=False)
    claim_object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey('auth.User', null=True, editable=False)
    date = models.DateTimeField(default=datetime.now, db_index=True)
    sphere_of_claim = models.IntegerField(choices=SPHERE_CHOICES, db_index=True, editable=False)
    type = models.IntegerField(choices=CLAIM_TYPES, db_index=True, editable=False)
#    open = models.NullBooleanField()
    status = models.IntegerField(choices=CASE_STATUSES, default=CaseStatus.New, db_index=True)
    
    imported = models.BooleanField(default=False, editable=False)
    tmp_processed = models.IntegerField(null=True, editable=False)
    old_claim_id = models.IntegerField(null=True, editable=False)
    
    @classmethod
    def get(cls, user, object):
        for o in cls.list(object, user=user):
            return o
        return None
    
    @classmethod
    def list(cls, object, **kwargs):
        ct = ContentType.objects.get_for_model(object)
        qs = cls.objects.filter(content_type__pk=ct.id, object_id=object.id, **kwargs)
        return qs

    def get_title(self):
        return CLAIM_TITLES_DICT.get(self.type)
    
    def get_normalized_display(self):
        return CLAIM_NORMALIZED_TITLES_DICT.get(self.type)
    
    def __unicode__(self):
        return self.get_normalized_display()
    
    def send_email(self):
        pass
    
    def save(self, *args, **kwargs):
        is_new = self.id == None
        res = super(Claim, self).save(*args, **kwargs)
        if is_new:
            self.send_email()
        return res


def default_next_penalty_payment_date():
    return datetime.now() + timedelta(10)


class PenaltyPaymentClaim(models.Model):
    class Meta:
        abstract = True
    
    penalty_payment = models.OneToOneField('members.BillingHistory', null=True)
    next_penalty_payment_date = models.DateTimeField(null=True, db_index=True, default=default_next_penalty_payment_date)
    penalty_payment_tries = models.IntegerField(default=0)
    
    def take_penalty_payment(self):
        if self.penalty_payment != None:
            return True, None
        
        aim = create_aim()
        profile = self.user.get_profile()
        card = profile.get_billing_card_data()
        data = {
            'amount': decimal.Decimal('50.0'),
            'number': card['number'], 
            'exp': '/'.join(('%s' % card['exp_month'], ('%s' % card['exp_year'])[-2:])),
            'code': card['code'],
            'billing': profile.get_billing_data(), 
            'shipping': profile.get_shipping_data(), 
            'invoice_num': 'RENT_CLAIM_%s_%s' % (self.user.id, self.id), 
            'description': '%s - Unreturned Game Fees' % self.get_title(),
            'x_email': self.user.email,
            'x_cust_id': self.user.id,
        }
        res = aim.capture(**data)

        billing_history = BillingHistory(user=self.user, 
                                         payment_method=profile.get_payment_card().display_number, 
                                         description=data['description'], 
                                         debit=data['amount'], 
                                         reason='rent', 
                                         type=TransactionType.RentPayment,
                                         status=TransactionStatus.Passed,
                                         card_data=card,
                                         aim_transaction_id=res.transaction_id,
                                         aim_response=res._as_dict,
                                         message=res.response_reason_text)

        if res.response_code != 1:
            self.penalty_payment_tries += 1
            self.next_penalty_payment_date = datetime.now() + timedelta(2)
            self.save()
            billing_history.status = TransactionStatus.Declined
            billing_history.save()
            return False, res
        billing_history.save()
        self.next_penalty_payment_date = None
        self.penalty_payment = billing_history
        self.save()
        return True, res
    
    def cancel_penalty_payment(self):
        if self.penalty_payment == None or self.penalty_payment.get_refund() or self.penalty_payment.status == TransactionStatus.Canceled:
            return
        if self.penalty_payment.is_setted():
            self.penalty_payment.refund_transaction(comment='Game Returned')
        else:
            self.penalty_payment.void_transaction()
    
    
class GameIsDamagedClaim(Claim, PenaltyPaymentClaim):
    game_is_scratched = models.BooleanField(default=False, blank=True, 
                                            verbose_name='Game is scratched')
    game_skips_playing = models.BooleanField(default=False, blank=True,
                                             verbose_name='Game skips or stops playing')
    game_is_cracked = models.BooleanField(default=False, blank=True,
                                          verbose_name='Game is cracked or broken')

    def save(self, *args, **kwargs):
        self.type = ClaimType.GameIsDamaged
        return super(GameIsDamagedClaim, self).save(*args, **kwargs)
    
    def get_damages_display(self):
        r = []
        if self.game_is_scratched:
            r.append('Scratched')
        if self.game_skips_playing:
            r.append('Skips Playing')
        if self.game_is_cracked:
            r.append('Cracked')
        return '; '.join(r)

    def send_email(self):
        mail(self.user.email, 'emails/claims/rent_damaged_game.html', {
            'claim': self,
            'user': self.user,
        }, subject='Your "Damaged Game" problem has been received')


class WrongGameClaim(Claim, PenaltyPaymentClaim):
    game_not_in_list = models.BooleanField(default=False, blank=True,
                                           verbose_name='Game was not on your Rent List')
    game_not_match_white_sleeve = models.BooleanField(default=False, blank=True,
                                                      verbose_name='Game does not match the white sleeve')

    def save(self, *args, **kwargs):
        self.type = ClaimType.WrongGame
        return super(WrongGameClaim, self).save(*args, **kwargs)

    def send_email(self):
        mail(self.user.email, 'emails/claims/rent_wrong_game.html', {
            'claim': self,
            'user': self.user,
        }, subject='Your "Wrong Game" problem has been received')

    
class DontReceiveClaim(Claim):
    first_name = models.CharField('First Name', max_length=30, null=True, blank=True)
    last_name = models.CharField('Last Name', max_length=30, null=True, blank=True)
    shipping_address1 = models.CharField(max_length=255, verbose_name='Address 1', null=True)
    shipping_address2 = models.CharField(max_length=255, verbose_name='Address 2', null=True, blank=True)
    shipping_city = models.CharField(max_length=100, verbose_name='City', null=True)
    shipping_state = models.CharField(max_length=2, verbose_name='State', null=True)
    shipping_zip_code = models.CharField(max_length=10, verbose_name='Zip', null=True)

    def save(self, *args, **kwargs):
        self.type = ClaimType.DontRecieve
        return super(DontReceiveClaim, self).save(*args, **kwargs)

    def send_email(self):
        mail(self.user.email, 'emails/claims/rent_lost_game.html', {
            'claim': self,
            'user': self.user,
        }, subject='Your "Lost Game" problem has been received')


class MailerIsEmptyClaim(Claim):
    comment = models.CharField(max_length=255, default='', blank=True)

    def save(self, *args, **kwargs):
        self.type = ClaimType.MailerIsEmpty
        return super(MailerIsEmptyClaim, self).save(*args, **kwargs)


class GamemineNotReceiveGameClaim(Claim):
    mailed_date = models.DateField()

    def save(self, *args, **kwargs):
        self.type = ClaimType.GamemineNotReceiveGame
        return super(GamemineNotReceiveGameClaim, self).save(*args, **kwargs)


SERVICE_CHOICES = (
    (0, 'USPS'),
    (1, 'FedEx'),
    (2, 'UPS'),
)


class GamemineNotRecieveTradeGameClaim(Claim):
    service = models.IntegerField(choices=SERVICE_CHOICES, default=0)
    tracking_number = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        self.type = ClaimType.GamemineNotReceiveTradeGame
        return super(GamemineNotRecieveTradeGameClaim, self).save(*args, **kwargs)


class WrongTradeValueCreditClaim(Claim):
    received = models.DecimalField(max_digits=12, decimal_places=2, blank=True, default=decimal.Decimal('0.0'))
    expected = models.DecimalField(max_digits=12, decimal_places=2, blank=True, default=decimal.Decimal('0.0'))

    def save(self, *args, **kwargs):
        self.type = ClaimType.WrongTradeValueCredit
        return super(WrongTradeValueCreditClaim, self).save(*args, **kwargs)
