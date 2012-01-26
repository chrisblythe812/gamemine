# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'FeedbackifyFeedback'
        db.create_table('crm_feedbackifyfeedback', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.DateField')(null=True, db_index=True)),
            ('form_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('item_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('score', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('subcategory', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('feedback', self.gf('django.db.models.fields.TextField')()),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True)),
            ('context', self.gf('django_snippets.thirdparty.models.json_field.JSONField')(null=True)),
        ))
        db.send_create_signal('crm', ['FeedbackifyFeedback'])


    def backwards(self, orm):
        
        # Deleting model 'FeedbackifyFeedback'
        db.delete_table('crm_feedbackifyfeedback')


    models = {
        'crm.feedbackifyfeedback': {
            'Meta': {'object_name': 'FeedbackifyFeedback'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'context': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'feedback': ('django.db.models.fields.TextField', [], {}),
            'form_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'subcategory': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['crm']
