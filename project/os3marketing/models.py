# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import signals
from django.db.models.query import EmptyQuerySet
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from itertools import chain
from managers import *
from project.buy_orders.models import *
from project.members.models import Profile, ProfileEntryPoint
from project.rent.models import *
from project.trade.models import *
from smtplib import SMTP
from tinymce import models as tinymce_models
class SMTPServer(models.Model):
    alias = models.CharField(_(u"Nickname"),max_length=255,help_text=_(u"A description for the smtp server"))
    server = models.CharField(_(u"SMTP Server"), max_length=255,unique=True,help_text=_(u"SMTP Server information, eg: smtp.gmail.com"))
    user = models.CharField(_(u"User"), max_length=128, blank=True,
                            help_text=_(u"SMTP server user. Leave blank if it is public."))
    password = models.CharField(_(u"Password"), max_length=128, blank=True,
                                help_text=_(u"SMTP Server password. Leave blank if it is public."))
    port = models.IntegerField(_(u"Port"),_(u"Enter the SMTP server's port."), default=25)
    tls = models.BooleanField('TLS',help_text=_(u'Enter if the server uses tls. For more details <a href=\"http://pt.wikipedia.org/wiki/Transport_Layer_Security\">click here</a>.'))
    mails_hour = models.IntegerField(_(u"Emails per hour"),default=0,help_text=_(u"""Enter the number of emails per hour in case the SMTP server has a limit of emails that can be sent for each day/hour. 
                                                                                    Leave the value 0 in case there is no limit.  """))
    sender = models.CharField(_(u'Source email.'), max_length=255,help_text=_(u'Email shown as source for newsletter')) #default=DEFAULT_HEADER_SENDER
    reply_to = models.CharField(_(u'Reply email'), max_length=255,help_text=_(u'Enter the email used to receive feedback from contacts.'))#default=DEFAULT_HEADER_REPLY
    active = models.BooleanField(_(u"Active"),default=True)
    
    objects = SMTPManager()
    def check_connection(self):
        try:
            smtp = SMTP(self.server, int(self.port))
            if self.tls:
                smtp.starttls()
            if self.user or self.password:
                smtp.login(self.user, self.password)
            smtp.quit()
        except Exception as e:
            return False
        return True
    check_connection.short_description = _(u'Connection test')

    def credits(self):
        if not self.mails_hour:
            return 10000000 
        last_hour = datetime.now() - timedelta(hours=1)
        sent_last_hour = ContactMailingStatus.objects.filter(
            models.Q(status=ContactMailingStatus.SENT) |
            models.Q(status=ContactMailingStatus.SENT_TEST),
            newsletter__server=self,
            creation_date__gte=last_hour).count()
        return self.mails_hour - sent_last_hour

    def __unicode__(self):
        return '%s (%s)' % (self.alias, self.server)

    class Meta:
        verbose_name = _(u"SMTP Server")
        verbose_name_plural = _(u"SMTP Servers")
        
        
class Contact(models.Model): 
    ACTIVE  = 0
    INVALID_EMAIL  = 1
    UNSUBSCRIBER = 2
    STATUS_CHOICES = ((ACTIVE, _(u'Active')),
                      (INVALID_EMAIL, _(u'Invalid Email')),
                      (UNSUBSCRIBER, _(u'Unsubscription')),
                      )
    
    email = models.EmailField(_(u"Email"), unique=True)
    first_name = models.CharField(_(u"Name"), max_length=50, blank=True)
    last_name = models.CharField(_(u"Last name"), max_length=50, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES ,default=ACTIVE)
    tester = models.BooleanField(_(u"Test contact"), default=False,help_text=_(u"All contacts marked as test will receive the newsletter's test email."))
    creation_date = models.DateTimeField(_(u"Creation date"), auto_now_add=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
        
    objects = ContactManager()


    def save(self, force_insert=False, force_update=False):
        q = User.objects.filter(email=self.email)
        if q.count() > 0:
            self.content_object = q[0]
        super(Contact, self).save(force_insert, force_update)
        
        
    def subscriptions(self):
        return MailingList.objects.filter(subscribers=self)

    def unsubscriptions(self):
        return MailingList.objects.filter(unsubscribers=self)

    def mail_format(self):
        if self.first_name and self.last_name:
            return '%s %s <%s>' % (self.last_name, self.first_name, self.email)
        return self.email


    def __unicode__(self):
        if self.first_name and self.last_name:
            return '%s %s' % (self.first_name, self.last_name)
        return unicode(self.email)

    class Meta:
        ordering = ('id','creation_date',)
        verbose_name = _(u'Contact')
        verbose_name_plural = _(u'Contacts')
        
class Link(models.Model):
    title = models.CharField(_(u'Title'), max_length=255)
    url = models.CharField(_(u'Url'), max_length=255)
    creation_date = models.DateTimeField(_(u'Creation date'), auto_now_add=True)

    def get_absolute_url(self):
        return self.url

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('creation_date',)
        verbose_name = _(u'Link')
        verbose_name_plural = _(u'Links')


class MailingList(models.Model):
    class Meta:
        ordering = ('creation_date',)
        verbose_name = _(u'Mailing List')
        verbose_name_plural = _(u'Mailing Lists')

    PUBLIC  = 0
    PRIVATE  = 1
    TYPE_CHOICES = ((PUBLIC, _(u'Publics')),
                      (PRIVATE, _(u'Privates')),    
                      )
    STATIC = 0
    DYNAMIC = 1
    ACTION_TYPE = ((STATIC, _(u'Static')),
                      (DYNAMIC, _(u'Dynamic')),    
                      )

    name = models.CharField(_(u'Name'), max_length=255)
    description = models.TextField(_(u'Description'), blank=True)
    subscribers = models.ManyToManyField(Contact, verbose_name=_(u'Subscriptions'),
                                         related_name='mailinglist_subscriber',
                                         #help_text='Contém todos os contatos que receberão a campanha'
                                         )
    unsubscribers = models.ManyToManyField(Contact, verbose_name=_(u'Unsubscription'),
                                           related_name='mailinglist_unsubscriber',
                                         null=True, blank=True,help_text=_(u'Contains all contacts that no longer want to receive the newsletter'))
    creation_date = models.DateTimeField(_(u'Registration date'), auto_now_add=True)
    modification_date = models.DateTimeField(_(u'Modified date'), auto_now=True)
    type = models.IntegerField(_("List type"),choices=TYPE_CHOICES,default=PRIVATE,
                               help_text=_(u"""The public lists will be published at the portal and the registered users will have the 
                                       option to subscribe and unsubscribe to each one of them. This means that these lists will be self 
                                       manageable without intervention from the administrator. The private lists will be managed by the 
                                       system's administrator and will also have a link for unsubscription. """))
    behavior = models.IntegerField(_("Behavior"),choices=ACTION_TYPE,default=DYNAMIC,
                               help_text=_(u"""On static mode the user need to be added manually into the mailing list. On Dynamic mode system gets the users on fly based
                                             on predefined filters. """))
    def __unicode__(self):
        return self.name

    def subscribers_count(self):
        """count subscribers"""
        if self.behavior == MailingList.STATIC:
            return self.subscribers.all().count()
        else:
            return self.get_dynamic_list().count()
    subscribers_count.short_description = '# of contacts'         
    subscribers_count.short_description = _(u'Total Contacts')
  
    def contacts_set(self):
        """get contacts"""
        unsubscribers_id = self.unsubscribers.values_list('id')
        if self.behavior == MailingList.STATIC:
            return self.subscribers.available().exclude(id__in=unsubscribers_id.query)
        else:       
            return self.get_dynamic_list().exclude(id__in=unsubscribers_id.query)

    def get_dynamic_list(self):
        qs = Contact.objects.available()
        filter = False
        for f in self.filtering_set.all():
            filter = True
            kwargs = {}
            if f.email_type == Filtering.NONMEMBERS:
                kwargs['object_id__in'] = User.objects.filter(memberrentalplan__user=None,buyorder__user=None,tradeorder__user=None).values_list('pk').query
            elif f.email_type == Filtering.RENT:
                kwargs['object_id__in'] = RentOrder.objects.all().values_list('user').query
            elif f.email_type == Filtering.BUY:
                kwargs['object_id__in'] = BuyOrder.objects.all().values_list('user').query
            elif f.email_type == Filtering.TRADE:
                kwargs['object_id__in'] = TradeOrder.objects.all().values_list('user').query
            elif f.email_type == Filtering.DECKTHEHALLS:
                kwargs['object_id__in'] = User.objects.filter(profile__entry_point=ProfileEntryPoint.DeckTheHalls).values_list('pk').query                

            if len(kwargs) > 0:                
                qs = qs.filter(**kwargs)
                
            if f.rent_status is not None:
                qs = qs.filter(object_id__in=MemberRentalPlan.objects.filter(status=f.rent_status).values_list('user').query)
            if f.trade_x:
                qs = qs.filter(object_id__in=TradeOrder.objects.filter(create_date__gte=datetime.today() - timedelta(days=f.trade_x)).values_list('user').query)
            if f.buy_x:
                qs = qs.filter(object_id__in=BuyOrder.objects.filter(create_date__gte=datetime.today() - timedelta(days=f.buy_x)).values_list('user').query)
        if filter:
            qs = qs.filter(content_type=ContentType.objects.get_for_model(User))
            return qs
        return Contact.objects.none()

class Filtering(models.Model):
    class Meta:
        verbose_name = _(u'Filtering')
        verbose_name_plural = _(u'Filtering')        
    ALL = 1
    NONMEMBERS = 2
    BUY = 3
    RENT = 4
    TRADE = 5
    DECKTHEHALLS = 6
    EMAIL_TYPE = ((ALL, _(u'All')),
                      (NONMEMBERS, _(u'Non Members')),
                      (BUY, _(u'Buy')),
                      (RENT, _(u'Rent')),   
                      (TRADE, _(u'Trade')),                                         
                      (DECKTHEHALLS, _(u'DecktheHalls')),                                                
                      )    
    mailinglist = models.ForeignKey(MailingList)  
    email_type = models.IntegerField(choices=EMAIL_TYPE,null=True,blank=True)
    buy_x = models.IntegerField(u'Purchased Game in last “X” days',null=True,blank=True)
    trade_x = models.IntegerField(u'Process Trades in last “X” days',null=True,blank=True)
    rent_status = models.IntegerField(choices=RENTAL_PLAN_STATUS, null=True, blank=True)
    
    def __unicode__(self):
        return ''
    
class CabecalhoRodape(models.Model):
    def __unicode__(self):
        return unicode(self.descricao)    
    descricao = models.CharField(_(u'Description'),max_length=50)
    cabecalho = models.TextField(_(u'Header'))
    rodape = models.TextField(_(u'Footer'))
    padrao = models.BooleanField(_(u'Standard'),default=False)
    
    class Meta:
        verbose_name = _(u'Header and Footer')
        verbose_name_plural = _(u'Header and Footer')     
        
class Newsletter(models.Model):
    DRAFT  = 0
    WAITING  = 1
    SENDING = 2
    SENT = 3
    CANCELED = 4

    STATUS_CHOICES = ((DRAFT, _(u'Draft')),
                      (WAITING, _(u'Waiting to be sent')),
                      (SENDING, _(u'Sending')),
                      (SENT, _(u'Sent')),
                      (CANCELED, _(u'Cancelled')),
                      )

    title = models.CharField(_(u'newsletter title'), max_length=255)
    content = tinymce_models.HTMLField(_(u"newsletter"), help_text=_(u"Create the newsletter using the editor or click on the editor's HTML button to write the HTML manually."))     
    mailing_list = models.ManyToManyField(MailingList, verbose_name=_(u'List Type'),help_text=_(u"Enter to which Mailing Lists you would like to send the newsletter."))
    server = models.ForeignKey(SMTPServer, limit_choices_to = {'active': True} ,verbose_name=_(u'Outgoing configuration'))
    email_status = models.EmailField(_(u"Status email"),blank=True,help_text=_(u'Used for information for outgoing newsletters {Initialized and Finished}'))
    status = models.IntegerField(_(u'Status'), choices=STATUS_CHOICES, default=DRAFT)
    sending_date = models.DateTimeField(_(u'Sent date/time'), default=datetime.now)
    slug = models.SlugField()
    creation_date = models.DateTimeField(_(u'Registration date'), auto_now_add=True)
    modification_date = models.DateTimeField(_(u'Modified date'), auto_now=True)
    cabecalho_rodape = models.ForeignKey(CabecalhoRodape,verbose_name=_(u'Header and Footer'),blank=True,null=True)
    def get_contacts(self):             
        or_query = None  
        for l in self.mailing_list.all():
            if type(l.contacts_set()) <> EmptyQuerySet:
                q = models.Q(**{"id__in": l.contacts_set().values_list('id').query})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q    
        if or_query:
            return Contact.objects.available().filter(or_query)    
        else:
            return  Contact.objects.none()   
             
    def mails_to_send(self):
        already_sent = ContactMailingStatus.objects.filter(status__in=[ContactMailingStatus.SENT, ContactMailingStatus.INVALID],
                                                           newsletter=self).values_list('contact')                                                                   
        return self.get_contacts().exclude(id__in=already_sent.query)                                                             
    
    def total_subscribers(self):
        return self.get_contacts().count()

    def mails_sent(self):
        return self.contactmailingstatus_set.filter(status__in=[ContactMailingStatus.SENT, ContactMailingStatus.INVALID]).count()
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ('-creation_date',)
        verbose_name = _(u'Newsletter')
        verbose_name_plural = _(u'Newsletters')
       
        
class Template(models.Model):
    title = models.CharField(_(u'Template title'), max_length=255)
    content = tinymce_models.HTMLField(_(u"Template"), help_text=_(u"Create a newsletter template using the editor or click the editor's HTML button to write the HTML manually."))     
    def __unicode__(self):
        return self.title
    
    class Meta:
        verbose_name = _(u'Template')
        verbose_name_plural = _(u'Templates')
        
class ContactMailingStatus(models.Model):
    SENT_TEST = -1
    SENT = 0
    ERROR = 1
    INVALID = 2
    OPENED = 4
    OPENED_ON_SITE = 5
    LINK_OPENED = 6
    UNSUBSCRIPTION = 7

    STATUS_CHOICES = ((SENT_TEST, _(u'Sent as a test')),
                      (SENT, _(u'Sent')),
                      (ERROR, _(u'Error')),
                      (INVALID, _(u'Invalid')),
                      (OPENED, _(u'Email read')),
                      (OPENED_ON_SITE, _(u'Read on the site')),
                      (LINK_OPENED, _(u'Link clicked')),
                      (UNSUBSCRIPTION, _(u'Unsubscribe')),
                      )

    newsletter = models.ForeignKey(Newsletter, verbose_name=_(u'Newsletter'))
    contact = models.ForeignKey(Contact, verbose_name=_(u'Contact'))
    status = models.IntegerField(_(u'Status'), choices=STATUS_CHOICES)
    link = models.ForeignKey(Link, verbose_name=_(u'Link'),blank=True, null=True)
    creation_date = models.DateTimeField(_(u'Registration date'), auto_now_add=True)


    @property
    def member_type(self):
        return 1

    
    def __unicode__(self):
        return '%s : %s : %s' % (self.newsletter.__unicode__(),
                                 self.contact.__unicode__(),
                                 self.get_status_display())

    class Meta:
        ordering = ('creation_date',)
        verbose_name = _(u'Outgoing status')
        verbose_name_plural = _(u'Outgoing status')
        
class Profile(models.Model):
    name = models.CharField(_(u"Name of the company"),max_length=255)
    website = models.URLField(_(u"Site of the company"),max_length=255)    
    def __unicode__(self):
        return self.name    
    
    class Meta:
        verbose_name = _(u"Company's profile")
        verbose_name_plural = _(u"Company's profile")           
                       
#PRE SAVES    
def sender_pre_save(signal, instance, sender, **kwargs):
    if not instance.slug:
        slug = slugify(instance)
        novo_slug = slug
        contador = 0
        while sender.objects.filter(slug=novo_slug).exclude(id=instance.id).count() > 0:
            contador += 1
            novo_slug = '%s-%d'%(slug, contador)
        instance.slug = novo_slug.lower()
        
def cabecalho_rodape_pre_save(signal, instance, sender, **kwargs):
    if CabecalhoRodape.objects.exclude(pk=instance.pk).count() == 0:
        instance.padrao = True
                
def cabecalho_rodape_pos_save(signal, instance,created, sender, **kwargs):
    if instance.padrao:
        crs = CabecalhoRodape.objects.exclude(pk=instance.pk)
        for cr in crs:
            cr.padrao = False
            cr.save()
                    
def user_pos_save(signal, instance,created, sender, **kwargs):
    if created and instance.email:
        try: 
            contact = Contact.objects.get(email=instance.email)
        except:        
            contact = Contact()
            contact.email= instance.email
            contact.first_name = instance.first_name
            contact.last_name = instance.last_name
        contact.content_object = instance
        contact.save()    
        
def user_pre_delete(signal, instance, sender, **kwargs):
    if instance.email:
        try: 
            contact = Contact.objects.get(email=instance.email)
            contact.delete()
        except:        
            pass
signals.pre_save.connect(sender_pre_save, sender=Newsletter)                
signals.pre_save.connect(cabecalho_rodape_pre_save, sender=CabecalhoRodape)     
signals.post_save.connect(cabecalho_rodape_pos_save, sender=CabecalhoRodape)     
signals.post_save.connect(user_pos_save, sender=User)
signals.pre_delete.connect(user_pre_delete, sender=User)          