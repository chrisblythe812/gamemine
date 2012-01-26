# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'WrongGameClaim.penalty_payment'
        db.add_column('claims_wronggameclaim', 'penalty_payment', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['members.BillingHistory'], unique=True, null=True), keep_default=False)

        # Adding field 'WrongGameClaim.next_penalty_payment_date'
        db.add_column('claims_wronggameclaim', 'next_penalty_payment_date', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True), keep_default=False)

        # Adding field 'WrongGameClaim.penalty_payment_tries'
        db.add_column('claims_wronggameclaim', 'penalty_payment_tries', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'GameIsDamagedClaim.penalty_payment'
        db.add_column('claims_gameisdamagedclaim', 'penalty_payment', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['members.BillingHistory'], unique=True, null=True), keep_default=False)

        # Adding field 'GameIsDamagedClaim.next_penalty_payment_date'
        db.add_column('claims_gameisdamagedclaim', 'next_penalty_payment_date', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True), keep_default=False)

        # Adding field 'GameIsDamagedClaim.penalty_payment_tries'
        db.add_column('claims_gameisdamagedclaim', 'penalty_payment_tries', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'WrongGameClaim.penalty_payment'
        db.delete_column('claims_wronggameclaim', 'penalty_payment_id')

        # Deleting field 'WrongGameClaim.next_penalty_payment_date'
        db.delete_column('claims_wronggameclaim', 'next_penalty_payment_date')

        # Deleting field 'WrongGameClaim.penalty_payment_tries'
        db.delete_column('claims_wronggameclaim', 'penalty_payment_tries')

        # Deleting field 'GameIsDamagedClaim.penalty_payment'
        db.delete_column('claims_gameisdamagedclaim', 'penalty_payment_id')

        # Deleting field 'GameIsDamagedClaim.next_penalty_payment_date'
        db.delete_column('claims_gameisdamagedclaim', 'next_penalty_payment_date')

        # Deleting field 'GameIsDamagedClaim.penalty_payment_tries'
        db.delete_column('claims_gameisdamagedclaim', 'penalty_payment_tries')


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
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imported': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'old_claim_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sphere_of_claim': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'tmp_processed': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'claims.dontreceiveclaim': {
            'Meta': {'object_name': 'DontReceiveClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'shipping_address1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'shipping_address2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'shipping_city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'shipping_state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True'}),
            'shipping_zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'})
        },
        'claims.gameisdamagedclaim': {
            'Meta': {'object_name': 'GameIsDamagedClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'game_is_cracked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'game_is_scratched': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'game_skips_playing': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'next_penalty_payment_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'penalty_payment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['members.BillingHistory']", 'unique': 'True', 'null': 'True'}),
            'penalty_payment_tries': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'claims.gameminenotreceivegameclaim': {
            'Meta': {'object_name': 'GamemineNotReceiveGameClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'mailed_date': ('django.db.models.fields.DateField', [], {})
        },
        'claims.gameminenotrecievetradegameclaim': {
            'Meta': {'object_name': 'GamemineNotRecieveTradeGameClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'service': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
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
            'game_not_match_white_sleeve': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'next_penalty_payment_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'penalty_payment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['members.BillingHistory']", 'unique': 'True', 'null': 'True'}),
            'penalty_payment_tries': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'claims.wrongtradevaluecreditclaim': {
            'Meta': {'object_name': 'WrongTradeValueCreditClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'expected': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'received': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'members.billinghistory': {
            'Meta': {'object_name': 'BillingHistory'},
            'aim_response': ('django_snippets.models.blowfish_field.BlowfishField', [], {'null': 'True'}),
            'aim_transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'applied_credits': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'card_data': ('django_snippets.models.blowfish_field.BlowfishField', [], {'null': 'True'}),
            'credit': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'debit': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'payment_method': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'refered_transaction': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['members.BillingHistory']", 'null': 'True'}),
            'setted': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        }
    }

    complete_apps = ['claims']
