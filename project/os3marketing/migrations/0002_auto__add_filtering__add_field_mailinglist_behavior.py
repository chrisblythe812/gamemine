# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Filtering'
        db.create_table('os3marketing_filtering', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mailinglist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['os3marketing.MailingList'])),
            ('email_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('buy_x', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('trade_x', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('rent_status', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('os3marketing', ['Filtering'])

        # Adding field 'MailingList.behavior'
        db.add_column('os3marketing_mailinglist', 'behavior', self.gf('django.db.models.fields.IntegerField')(default=1), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'Filtering'
        db.delete_table('os3marketing_filtering')

        # Deleting field 'MailingList.behavior'
        db.delete_column('os3marketing_mailinglist', 'behavior')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'os3marketing.cabecalhorodape': {
            'Meta': {'object_name': 'CabecalhoRodape'},
            'cabecalho': ('django.db.models.fields.TextField', [], {}),
            'descricao': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'padrao': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rodape': ('django.db.models.fields.TextField', [], {})
        },
        'os3marketing.contact': {
            'Meta': {'ordering': "('id', 'creation_date')", 'object_name': 'Contact'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'os3marketing.contactmailingstatus': {
            'Meta': {'ordering': "('creation_date',)", 'object_name': 'ContactMailingStatus'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['os3marketing.Contact']"}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['os3marketing.Link']", 'null': 'True', 'blank': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['os3marketing.Newsletter']"}),
            'status': ('django.db.models.fields.IntegerField', [], {})
        },
        'os3marketing.filtering': {
            'Meta': {'object_name': 'Filtering'},
            'buy_x': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'email_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailinglist': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['os3marketing.MailingList']"}),
            'rent_status': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'trade_x': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'os3marketing.link': {
            'Meta': {'ordering': "('creation_date',)", 'object_name': 'Link'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'os3marketing.mailinglist': {
            'Meta': {'ordering': "('creation_date',)", 'object_name': 'MailingList'},
            'behavior': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'mailinglist_subscriber'", 'symmetrical': 'False', 'to': "orm['os3marketing.Contact']"}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'unsubscribers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'mailinglist_unsubscriber'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['os3marketing.Contact']"})
        },
        'os3marketing.newsletter': {
            'Meta': {'ordering': "('-creation_date',)", 'object_name': 'Newsletter'},
            'cabecalho_rodape': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['os3marketing.CabecalhoRodape']", 'null': 'True', 'blank': 'True'}),
            'content': ('tinymce.models.HTMLField', [], {}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email_status': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_list': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['os3marketing.MailingList']", 'symmetrical': 'False'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sending_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['os3marketing.SMTPServer']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'os3marketing.profile': {
            'Meta': {'object_name': 'Profile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '255'})
        },
        'os3marketing.smtpserver': {
            'Meta': {'object_name': 'SMTPServer'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mails_hour': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {'default': '25'}),
            'reply_to': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'server': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'tls': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'os3marketing.template': {
            'Meta': {'object_name': 'Template'},
            'content': ('tinymce.models.HTMLField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['os3marketing']
