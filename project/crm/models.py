from logging import debug #@UnusedImport
from datetime import datetime

from django.db import models, transaction
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django_snippets.thirdparty.models import JSONField
from project.utils.mailer import mail


class CaseStatus:
    New = 0
    OnHold = 1
    Escalated = 2
    Closed = 3
    AutoClosed = 4
    
CASE_STATUSES = (
    (CaseStatus.New, 'New'),
    (CaseStatus.OnHold, 'On Hold'),
    (CaseStatus.Escalated, 'Escalated'),
    (CaseStatus.Closed, 'Closed'),
    (CaseStatus.AutoClosed, 'Closed'),
)
    
CASE_STATUSES_PUBLIC = (
    (CaseStatus.New, 'New'),
    (CaseStatus.OnHold, 'On Hold'),
    (CaseStatus.Escalated, 'Escalated'),
    (CaseStatus.Closed, 'Closed'),
)
    

class FeedbackifyFeedback(models.Model):
    class Meta:
        ordering = ['-timestamp']
    
    user = models.ForeignKey(User, null=True)
    timestamp = models.DateTimeField(null=True, db_index=True)
    form_id = models.IntegerField(null=True)
    item_id = models.IntegerField(null=True)
    score = models.IntegerField(null=True)
    category = models.CharField(max_length=100, db_index=True)
    subcategory = models.CharField(max_length=100, db_index=True)
    feedback = models.TextField()
    email = models.EmailField(null=True)
    context = JSONField(null=True)
    payload = JSONField(null=True)

    status = models.IntegerField(choices=CASE_STATUSES, default=CaseStatus.New, db_index=True)

    def save(self, *args, **kwargs):
        qs = User.objects.filter(email=self.email)
        if qs.count():
            self.user = qs[0]
        super(FeedbackifyFeedback, self).save(*args, **kwargs)
        
    def get_replies(self):
        return Reply.get_replies(self)
    
    def get_email(self):
        return self.user.email if self.user else self.email


class Reply(models.Model):
    class Meta:
        ordering = ['timestamp']
    
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    case = generic.GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(default=datetime.now, db_index=True)
    status = models.IntegerField(choices=CASE_STATUSES, default=CaseStatus.New, db_index=True)
    message = models.TextField()
    mailed_to = models.EmailField(null=True)

    def send_email(self):
        mail(self.mailed_to, 'emails/crm/reply.html', {
            'reply': self,
        }, subject='Gamemine - Reply')

    @staticmethod
    def get_replies(case, **kwargs):
        ct = ContentType.objects.get_for_model(case)
        return Reply.objects.filter(content_type__pk=ct.id, object_id=case.id, **kwargs)
    
    
class Ticket(models.Model):
    created = models.DateTimeField(default=datetime.now, db_index=True)
    user = models.ForeignKey(User, null=True)
    status = models.IntegerField(choices=CASE_STATUSES, default=CaseStatus.New, db_index=True)
    message = models.TextField()
    last_updated = models.DateTimeField(null=True)
    
    @staticmethod
    def create(user, status = CaseStatus.New, message = '', cls=None, **kwargs):
        d = datetime.now()
        cls = cls or Ticket
        t = cls(created = d,
                user = user,
                message = message,
                status = status,
                last_updated = d,
                **kwargs)
        t.save()
        
        h = TicketHistory(ticket = t,
                          user = user,
                          timestamp = d,
                          status = status, 
                          message = message)
        h.save()
        
        return t
    
    def change_status(self, user, status, message=''):
        h = TicketHistory(ticket = self, 
                          user = user,
                          status = status, 
                          message = message)
        h.save()
        self.status = status
        self.last_updated = h.timestamp
        self.save()


class TicketHistory(models.Model):
    class Meta:
        ordering = ['-timestamp']
    
    ticket = models.ForeignKey(Ticket)
    user = models.ForeignKey(User, null=True)
    timestamp = models.DateTimeField(db_index=True, default=datetime.now)
    status = models.IntegerField(choices=CASE_STATUSES)
    message = models.TextField(null=True)


class PersonalGameTicket(Ticket):
    class Meta:
        ordering = ['-created']
    
    order = models.ForeignKey('rent.RentOrder')

    @staticmethod
    @transaction.commit_on_success
    def create(user, order, status = CaseStatus.New, message = ''):
        from project.rent.models import MemberRentalPlan, RentalPlanStatus
      
        try:
            t = PersonalGameTicket.objects.exclude(status__in=[CaseStatus.AutoClosed, CaseStatus.Closed]).get(order=order)
            t.change_status(user, status, message)
            return t
        except PersonalGameTicket.DoesNotExist:
            t = Ticket.create(user, status, message, PersonalGameTicket, order=order)
            plan = MemberRentalPlan.get_current_plan(order.user)
            if plan:
                plan.status = RentalPlanStatus.PersonalGame
                plan.save()
                plan.send_personal_game_received()
            return t
