# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User
from project.os3marketing.models import Contact
class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        for c in User.objects.all():
            try: 
                contact = Contact.objects.get(email=c.email)
            except:        
                contact = Contact()
                contact.email= c.email
                contact.first_name = c.first_name
                contact.last_name = c.last_name
            contact.content_object = c
            contact.save()    

                        

    