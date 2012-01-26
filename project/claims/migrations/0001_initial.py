# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Claim'
        db.create_table('claims_claim', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('sphere_of_claim', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('claims', ['Claim'])

        # Adding model 'GameIsDamagedClaim'
        db.create_table('claims_gameisdamagedclaim', (
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
            ('game_is_scratched', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('game_skips_playing', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('game_is_cracked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('claims', ['GameIsDamagedClaim'])

        # Adding model 'WrongGameClaim'
        db.create_table('claims_wronggameclaim', (
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
            ('game_not_in_list', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('game_not_match_white_sleeve', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('claims', ['WrongGameClaim'])

        # Adding model 'DontRecieveClaim'
        db.create_table('claims_dontrecieveclaim', (
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('claims', ['DontRecieveClaim'])

        # Adding model 'MailerIsEmptyClaim'
        db.create_table('claims_mailerisemptyclaim', (
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
        ))
        db.send_create_signal('claims', ['MailerIsEmptyClaim'])

        # Adding model 'GamemineNotRecieveGameClaim'
        db.create_table('claims_gameminenotrecievegameclaim', (
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
            ('mailed_date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('claims', ['GamemineNotRecieveGameClaim'])

        # Adding model 'GamemineNotRecieveTradeGameClaim'
        db.create_table('claims_gameminenotrecievetradegameclaim', (
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
            ('service', self.gf('django.db.models.fields.IntegerField')()),
            ('tracking_number', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('claims', ['GamemineNotRecieveTradeGameClaim'])

        # Adding model 'WrongTradeValueCredit'
        db.create_table('claims_wrongtradevaluecredit', (
            ('claim_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['claims.Claim'], unique=True, primary_key=True)),
            ('received', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('expected', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
        ))
        db.send_create_signal('claims', ['WrongTradeValueCredit'])


    def backwards(self, orm):
        
        # Deleting model 'Claim'
        db.delete_table('claims_claim')

        # Deleting model 'GameIsDamagedClaim'
        db.delete_table('claims_gameisdamagedclaim')

        # Deleting model 'WrongGameClaim'
        db.delete_table('claims_wronggameclaim')

        # Deleting model 'DontRecieveClaim'
        db.delete_table('claims_dontrecieveclaim')

        # Deleting model 'MailerIsEmptyClaim'
        db.delete_table('claims_mailerisemptyclaim')

        # Deleting model 'GamemineNotRecieveGameClaim'
        db.delete_table('claims_gameminenotrecievegameclaim')

        # Deleting model 'GamemineNotRecieveTradeGameClaim'
        db.delete_table('claims_gameminenotrecievetradegameclaim')

        # Deleting model 'WrongTradeValueCredit'
        db.delete_table('claims_wrongtradevaluecredit')


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
            'comment': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'})
        },
        'claims.wronggameclaim': {
            'Meta': {'object_name': 'WrongGameClaim', '_ormbases': ['claims.Claim']},
            'claim_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['claims.Claim']", 'unique': 'True', 'primary_key': 'True'}),
            'game_not_in_list': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'game_not_match_white_sleeve': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'claims.wrongtradevaluecredit': {
            'Meta': {'object_name': 'WrongTradeValueCredit', '_ormbases': ['claims.Claim']},
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
