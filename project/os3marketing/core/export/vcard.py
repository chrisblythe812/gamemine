"""VCard system for importing/exporting Contact models"""
from datetime import datetime
from django.http import HttpResponse
from project.os3marketing.core.helper import email_is_valid
from project.os3marketing.core.libraries import vobject
from project.os3marketing.models import Contact


def vcard_contact_export(contact):
    vcard = vobject.vCard()
    vcard.add('n')
    vcard.n.value = vobject.vcard.Name(family=contact.last_name, given=contact.first_name)    
    vcard.add('fn')
    vcard.fn.value = '%s %s' % (contact.first_name, contact.last_name)
    vcard.add('email')
    vcard.email.value = contact.email
    vcard.email.type_param = 'INTERNET'
    return vcard.serialize()

def vcard_contacts_export(contacts):
    """Export multiples contacts in VCard"""
    export = ''
    for contact in contacts:
        export += '%s\r\n' % vcard_contact_export(contact)
    return export

def vcard_contacts_export_response(contacts, filename=''):
    """Return VCard contacts attached in a HttpResponse"""
    if not filename:
        filename = 'contacts_edn_%s' % datetime.now().strftime('%d-%m-%Y')
    filename = filename.replace(' ', '_')
        
    response = HttpResponse(vcard_contacts_export(contacts),
                            mimetype='text/x-vcard')
    response['Content-Disposition'] = 'attachment; filename=%s.vcf' % filename
    return response

def vcard_contact_import(vcard,list):      
    if not email_is_valid(vcard.email.value):
        return 0    
    created = False
    try:
        contact = Contact.objects.get(email=vcard.email.value)
        created = True
    except:
        contact = Contact()
    contact.email = vcard.email.value 
    contact.first_name = vcard.n.value.given    
    contact.last_name = vcard.n.value.family             
    contact.save()
    
    if list:
        list.subscribers.add(contact)         
    return int(created)

def vcard_contacts_import(stream,list):
    vcards = vobject.readComponents(stream)
    inserted = 0
    for vcard in vcards:
        inserted += vcard_contact_import(vcard,list)
    return inserted

