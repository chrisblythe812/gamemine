# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MuzeUpdateLog'
        db.create_table('staff_muzeupdatelog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('checksum', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=512)),
        ))
        db.send_create_signal('staff', ['MuzeUpdateLog'])


    def backwards(self, orm):
        
        # Deleting model 'MuzeUpdateLog'
        db.delete_table('staff_muzeupdatelog')


    models = {
        'staff.muzeupdatelog': {
            'Meta': {'object_name': 'MuzeUpdateLog'},
            'checksum': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'})
        }
    }

    complete_apps = ['staff']
