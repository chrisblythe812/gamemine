from project.os3marketing.core.helper import email_is_valid
from datetime import datetime
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.template import loader, Context
from project.os3marketing.models import Contact
import csv
import os


def export_csv_to_response(query_set,name=''):
        response = HttpResponse(mimetype='plain/text')
        if not name:
            name = 'contacts_csv_%s' % datetime.now().strftime('%d-%m-%Y')        
        name = name.replace(' ', '_')
        response['Content-Disposition'] = 'attachment; filename=' + '%s.csv' % name
        t = loader.get_template('os3marketing/contact_export_csv.txt')
        c = Context({
            'data': query_set,
        })
        response.write(t.render(c).encode("ISO-8859-1"))
        return response
    
def import_from_stream(source,list):
    tmp_file = settings.MEDIA_ROOT + '/csv.csv'
    default_storage.save(tmp_file ,source)
    try:
        file=open(tmp_file,'rb') 
        testReader=csv.reader(file,delimiter=';',quotechar='"')
        inserted = 0
        for row in testReader:
            if len(row) < 2:
                continue
            email = row[0].strip() 
            if not email_is_valid(email):
                continue
            created = False
            try:
                contact = Contact.objects.get(email=email)
                created = True
            except:
                contact = Contact() 
            contact.email = email
            contact.first_name = row[1].decode('ISO-8859-1')
            contact.last_name = row[2].decode('ISO-8859-1')    
            contact.save()    
            if  list:
                list.subscribers.add(contact)               
            inserted += int(created)   
        return inserted
    finally:
        file.close()
        os.remove(tmp_file)