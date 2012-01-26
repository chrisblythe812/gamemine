# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'WrongTradeValueCredit'
        db.delete_table('claims_wrongtradevaluecredit')

        # Adding model 'WrongTradeValueCreditClaim'
        db.create_table('claims_wrongtradevaluecreditclaim', (
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
            ('received', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('expected', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
        ))
        db.send_create_signal('claims', ['WrongTradeValueCreditClaim'])

        # Changing field 'MailerIsEmptyClaim.comment'
        db.alter_column('claims_mailerisemptyclaim', 'comment', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True))

        # Adding field 'Claim.type'
        db.add_column('claims_claim', 'type', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'WrongTradeValueCredit'
        db.create_table('claims_wrongtradevaluecredit', (
            ('expected', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('received', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('claims', ['WrongTradeValueCredit'])

        # Deleting model 'WrongTradeValueCreditClaim'
        db.delete_table('claims_wrongtradevaluecreditclaim')

        # Changing field 'MailerIsEmptyClaim.comment'
        db.alter_column('claims_mailerisemptyclaim', 'comment', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Deleting field 'Claim.type'
        db.delete_column('claims_claim', 'type')


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
        'claims.claim': {
            'Meta': {'object_name': 'Claim'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sphere_of_claim': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'claims.dontrecieveclaim': {
            'Meta': {'object_name': 'DontRecieveClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'})
        },
        'claims.gameisdamagedclaim': {
            'Meta': {'object_name': 'GameIsDamagedClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'game_is_cracked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'game_is_scratched': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'game_skips_playing': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'claims.gameminenotrecievegameclaim': {
            'Meta': {'object_name': 'GamemineNotRecieveGameClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'mailed_date': ('django.db.models.fields.DateField', [], {})
        },
        'claims.gameminenotrecievetradegameclaim': {
            'Meta': {'object_name': 'GamemineNotRecieveTradeGameClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'service': ('django.db.models.fields.IntegerField', [], {}),
            'tracking_number': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'claims.mailerisemptyclaim': {
            'Meta': {'object_name': 'MailerIsEmptyClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        'claims.wronggameclaim': {
            'Meta': {'object_name': 'WrongGameClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'game_not_in_list': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'game_not_match_white_sleeve': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'claims.wrongtradevaluecreditclaim': {
            'Meta': {'object_name': 'WrongTradeValueCreditClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'expected': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'received': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['claims']
