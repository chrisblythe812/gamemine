# -*- coding: utf-8 -*-
"""Mailer"""
from HTMLParser import HTMLParseError
from datetime import datetime
from django.contrib.sites.models import Site
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.encoding import smart_unicode, smart_str
from django.utils.translation import ugettext_lazy as _
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from project.os3marketing.core.helper import *
from project.os3marketing.core.libraries.html2text import html2text
from project.os3marketing.models import ContactMailingStatus, Newsletter, Contact, \
    Profile
from project.os3marketing.tokens import tokenize
from smtplib import SMTP, SMTPRecipientsRefused
import re
import time

class Mailer(object):
    """Mailer for generating and sending newsletters
    In test mode the mailer always send mails but do not log it"""
    smtp = None

    def __init__(self, newsletter, test=False):
        self.test = test
        self.newsletter = newsletter
        try:
            self.profile = get_profile()
        except:
            raise ProfileDoesNotExist(u"Profile is not configured.")
        
        content = '<table width="100%%"><tr><td align="center">%s</td></tr></table>' % self.newsletter.content
        self.newsletter_template = Template(content)
    
    def admin_notification(self,status,text,start_connection=False):
        """
        notify start and end of the campaign
        """
        if self.test or not self.newsletter.email_status:
            return
        
        if start_connection:
            self.smtp_connect()  
        message = MIMEMultipart('alternative')
        message['Subject'] = "%s - %s" % (status,self.newsletter.title)
        message['From'] = self.newsletter.server.sender
        message['Reply-to'] = self.newsletter.server.reply_to
        message['To'] = self.newsletter.email_status
        message.attach(MIMEText(text, 'plain', 'UTF-8'))         
        self.smtp.sendmail("%s<%s>" % (self.profile.name,self.newsletter.server.sender),
                                     self.newsletter.email_status,
                                     message.as_string())  
        if start_connection:               
            self.smtp.quit()
                    
    def run(self):
        """Send the mails"""
        if self.can_send:
            if not self.smtp:
                self.smtp_connect()
            if self.newsletter.status == Newsletter.WAITING:
                self.admin_notification(_(u'Start'),_(u'Email sending started.'))
            for contact in self.get_contacts():
                message = self.build_message(contact)
                try:
                    self.smtp.sendmail("%s<%s>" % (self.profile.name,self.newsletter.server.sender),
                                                 contact.email,
                                                 message.as_string())
                    status = self.test and ContactMailingStatus.SENT_TEST or ContactMailingStatus.SENT
                except SMTPRecipientsRefused, e:                    
                    status = ContactMailingStatus.INVALID
                except HTMLParseError, e:
                    raise e
                except Exception as e:
                    print e
                    status = ContactMailingStatus.ERROR
                    self.smtp.quit()
                    time.sleep(1)
                    self.smtp_connect()

                ContactMailingStatus.objects.create(newsletter=self.newsletter,
                                                    contact=contact, status=status)
                time.sleep(1)
            self.smtp.quit()
            self.update_newsletter_status()

    def build_message(self, contact):
        """Build the email"""
        content_html = self.build_email_content(contact)
        content_text = html2text(content_html)

        message = MIMEMultipart('alternative')
        message['Subject'] = self.newsletter.title
        message['From'] = self.newsletter.server.sender
        message['Reply-to'] = self.newsletter.server.reply_to
        message['To'] = contact.mail_format()
        message.attach(MIMEText(smart_str(content_text), 'plain', 'UTF-8'))
        message.attach(MIMEText(smart_str(content_html), 'html', 'UTF-8'))
        return message

    def smtp_connect(self):
        """Make a connection to the SMTP"""
        server = self.newsletter.server
        self.smtp = SMTP(server.server, int(server.port))
        if server.tls:
            self.smtp.starttls()
        if server.user or server.password:
            self.smtp.login(server.user, server.password)


    def get_contacts(self):
        """
            create a contact list to be sent
        """
        credits = self.newsletter.server.credits()
        if self.test:
            return Contact.objects.testers()[:credits]
        return self.newsletter.mails_to_send()[:credits]
    def build_email_content(self, contact):
        uidb36, token = tokenize(contact)
        unsubscription_url = get_unsubscription_url(self.newsletter,contact)
        context = Context({'contact': contact,
                           'domain': Site.objects.get_current().domain,
                           'newsletter': self.newsletter,
                           'uidb36': uidb36, 
                           'token': token,
                           'header_sender':self.newsletter.server.sender,
                           'website':self.profile.website,
                           'unsubscription_url':unsubscription_url})

        content = self.newsletter_template.render(context)
        content = track_links(content, context)
        try:
            link_site = Template(self.newsletter.cabecalho_rodape.cabecalho).render(context)
        except:
            link_site = render_to_string('os3marketing/newsletter_link_site.html', context)
            
        content = body_insertion(content, link_site)
        try:
            unsubscription = Template(self.newsletter.cabecalho_rodape.rodape).render(context)
        except:
            unsubscription = render_to_string('os3marketing/newsletter_link_unsubscribe.html', context)
            
        content = body_insertion(content, unsubscription, end=True)
        image_tracking = render_to_string('os3marketing/newsletter_image_tracking.html', context)
        content = body_insertion(content, image_tracking, end=True)
        return smart_unicode(content)

    def update_newsletter_status(self):
        if self.test:
            return
        if self.newsletter.status == Newsletter.WAITING:
            self.newsletter.status = Newsletter.SENDING
        if self.newsletter.status == Newsletter.SENDING and \
           self.newsletter.mails_to_send().count() == 0:
            self.newsletter.status = Newsletter.SENT
            self.admin_notification(_(u'Finalized'),_(u'Email sending finalized.'),True)
        self.newsletter.save()

    @property
    def can_send(self):
       
        if self.newsletter.server.credits() <= 0:
            return False
        if self.test:
            return True

        if self.newsletter.sending_date <= datetime.now() and \
               (self.newsletter.status == Newsletter.WAITING or \
                self.newsletter.status == Newsletter.SENDING):
            return True

        return False

