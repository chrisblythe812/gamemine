# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'OfferTerm'
        db.create_table('offer_term_offerterm', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('text', self.gf('tinymce.models.HTMLField')()),
        ))
        db.send_create_signal('offer_term', ['OfferTerm'])


    def backwards(self, orm):
        
        # Deleting model 'OfferTerm'
        db.delete_table('offer_term_offerterm')


    models = {
        'offer_term.offerterm': {
            'Meta': {'object_name': 'OfferTerm'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('tinymce.models.HTMLField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        }
    }

    complete_apps = ['offer_term']
