# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Subscriber.campaign_cid'
        db.add_column('subscription_subscriber', 'campaign_cid', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, db_index=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Subscriber.campaign_cid'
        db.delete_column('subscription_subscriber', 'campaign_cid')


    models = {
        'subscription.subscriber': {
            'Meta': {'object_name': 'Subscriber'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'campaign_cid': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'db_index': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['subscription']
