# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
class ContactManager(models.Manager):
    def get(self, *args, **kwargs):        
        from models import Contact
        if 'content_object' in kwargs:
            content_object = kwargs['content_object']
            del kwargs['content_object']
            kwargs['content_type'] = ContentType.objects.get_for_model(type(content_object))
            kwargs['object_id'] = content_object.pk                      
            if content_object.__class__.__name__ == 'User':
                try:
                    return super(ContactManager, self).get(*args, **kwargs)
                except Exception:       
                    c = Contact.objects.filter(email=content_object.email)[:1]
                    if c.count() > 0:
                        c[0].content_object = content_object
                        c[0].save()
                        return c[0]
                    c = Contact()
                    c.content_object =content_object
                    c.email = content_object.email
                    c.first_name = content_object.first_name
                    c.last_name = content_object.last_name
                    c.save()
                    return c
        return super(ContactManager, self).get(*args, **kwargs) 
    
    def available(self):
        from models import Contact
        return self.get_query_set().filter(status=Contact.ACTIVE)

    def testers(self):
        from models import Contact
        return self.get_query_set().filter(tester=True)

class SMTPManager(models.Manager):
    def active(self):
        return self.get_query_set().filter(active=True)
    

   