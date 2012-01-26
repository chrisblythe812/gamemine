# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'County'
        db.create_table('taxes_county', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('state', self.gf('django.contrib.localflavor.us.models.USStateField')(max_length=2, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
        ))
        db.send_create_signal('taxes', ['County'])

        # Adding unique constraint on 'County', fields ['state', 'name']
        db.create_unique('taxes_county', ['state', 'name'])

        # Adding model 'ByCityTax'
        db.create_table('taxes_bycitytax', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=4)),
            ('state', self.gf('django.contrib.localflavor.us.models.USStateField')(max_length=2, db_index=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
        ))
        db.send_create_signal('taxes', ['ByCityTax'])

        # Adding unique constraint on 'ByCityTax', fields ['state', 'city']
        db.create_unique('taxes_bycitytax', ['state', 'city'])

        # Adding model 'ByCountyTax'
        db.create_table('taxes_bycountytax', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=4)),
            ('county', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['taxes.County'], unique=True)),
        ))
        db.send_create_signal('taxes', ['ByCountyTax'])

        # Adding model 'ByStateTax'
        db.create_table('taxes_bystatetax', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=4)),
            ('state', self.gf('django.contrib.localflavor.us.models.USStateField')(unique=True, max_length=2, db_index=True)),
        ))
        db.send_create_signal('taxes', ['ByStateTax'])


    def backwards(self, orm):
        
        # Deleting model 'County'
        db.delete_table('taxes_county')

        # Removing unique constraint on 'County', fields ['state', 'name']
        db.delete_unique('taxes_county', ['state', 'name'])

        # Deleting model 'ByCityTax'
        db.delete_table('taxes_bycitytax')

        # Removing unique constraint on 'ByCityTax', fields ['state', 'city']
        db.delete_unique('taxes_bycitytax', ['state', 'city'])

        # Deleting model 'ByCountyTax'
        db.delete_table('taxes_bycountytax')

        # Deleting model 'ByStateTax'
        db.delete_table('taxes_bystatetax')


    models = {
        'taxes.bycitytax': {
            'Meta': {'unique_together': "(('state', 'city'),)", 'object_name': 'ByCityTax'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2', 'db_index': 'True'}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '4'})
        },
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
