from django.contrib import admin
from project.os3marketing.models import *

from project.os3marketing.admin.contact import ContactAdmin  
from project.os3marketing.admin.smtpserver import SMTPServerAdmin  
from project.os3marketing.admin.mailinglist import MailingListAdmin  
from project.os3marketing.admin.newsletter import NewsletterAdmin  
from project.os3marketing.admin.template import TemplateAdmin  
from project.os3marketing.admin.cabecalho_rodape import CabecalhoAdmin  

admin.site.register(Contact, ContactAdmin) 
admin.site.register(SMTPServer, SMTPServerAdmin)
admin.site.register(MailingList, MailingListAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(CabecalhoRodape, CabecalhoAdmin)
admin.site.register(Profile)

