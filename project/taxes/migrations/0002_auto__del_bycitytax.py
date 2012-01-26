# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'ByCityTax'
        db.delete_table('taxes_bycitytax')


    def backwards(self, orm):
        
        # Adding model 'ByCityTax'
        db.create_table('taxes_bycitytax', (
            ('city', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('state', self.gf('django.contrib.localflavor.us.models.USStateField')(max_length=2, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=4)),
        ))
        db.send_create_signal('taxes', ['ByCityTax'])


    models = {
        'taxes.bycountytax': {
            'Meta': {'object_name': 'ByCountyTax'},
            'county': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['taxes.County']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '4'})
        },
        'taxes.bystatetax': {
            'Meta': {'object_name': 'ByStateTax'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'unique': 'True', 'max_length': '2', 'db_index': 'True'}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '4'})
        },
        'taxes.county': {
            'Meta': {'unique_together': "(('state', 'name'),)", 'object_name': 'County'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2', 'db_index': 'True'})
        }
    }

    complete_apps = ['taxes']
