# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'AimTransaction'
        db.create_table('staff_aimtransaction', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, db_index=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, db_index=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('request', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['staff.AimRequest'], unique=True)),
            ('response', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['staff.AimResponse'], unique=True)),
        ))
        db.send_create_signal('staff', ['AimTransaction'])

        # Adding model 'AimRequest'
        db.create_table('staff_aimrequest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('data', self.gf('django_snippets.thirdparty.models.json_field.JSONField')()),
        ))
        db.send_create_signal('staff', ['AimRequest'])

        # Adding model 'AimResponse'
        db.create_table('staff_aimresponse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response_code', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('response_subcode', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('response_reason_code', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('response_reason_text', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('transaction_id', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, db_index=True)),
            ('invoice_number', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('transaction_type', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('data', self.gf('django_snippets.thirdparty.models.json_field.JSONField')()),
        ))
        db.send_create_signal('staff', ['AimResponse'])


    def backwards(self, orm):
        
        # Deleting model 'AimTransaction'
        db.delete_table('staff_aimtransaction')

        # Deleting model 'AimRequest'
        db.delete_table('staff_aimrequest')

        # Deleting model 'AimResponse'
        db.delete_table('staff_aimresponse')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'staff.aimrequest': {
            'Meta': {'object_name': 'AimRequest'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'data': ('django_snippets.thirdparty.models.json_field.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'})
        },
        'staff.aimresponse': {
            'Meta': {'object_name': 'AimResponse'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'data': ('django_snippets.thirdparty.models.json_field.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice_number': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'response_code': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'response_reason_code': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'response_reason_text': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'response_subcode': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'db_index': 'True'}),
            'transaction_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'})
        },
        'staff.aimtransaction': {
            'Meta': {'object_name': 'AimTransaction'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['staff.AimRequest']", 'unique': 'True'}),
            'response': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['staff.AimResponse']", 'unique': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
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
