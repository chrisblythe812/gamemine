# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SMTPServer'
        db.create_table('os3marketing_smtpserver', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('alias', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('server', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('port', self.gf('django.db.models.fields.IntegerField')(default=25)),
            ('tls', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('mails_hour', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sender', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('reply_to', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('os3marketing', ['SMTPServer'])

        # Adding model 'Contact'
        db.create_table('os3marketing_contact', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('tester', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('os3marketing', ['Contact'])

        # Adding model 'Link'
        db.create_table('os3marketing_link', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('os3marketing', ['Link'])

        # Adding model 'MailingList'
        db.create_table('os3marketing_mailinglist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modification_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('os3marketing', ['MailingList'])

        # Adding M2M table for field subscribers on 'MailingList'
        db.create_table('os3marketing_mailinglist_subscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['os3marketing.mailinglist'], null=False)),
            ('contact', models.ForeignKey(orm['os3marketing.contact'], null=False))
        ))
        db.create_unique('os3marketing_mailinglist_subscribers', ['mailinglist_id', 'contact_id'])

        # Adding M2M table for field unsubscribers on 'MailingList'
        db.create_table('os3marketing_mailinglist_unsubscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['os3marketing.mailinglist'], null=False)),
            ('contact', models.ForeignKey(orm['os3marketing.contact'], null=False))
        ))
        db.create_unique('os3marketing_mailinglist_unsubscribers', ['mailinglist_id', 'contact_id'])

        # Adding model 'CabecalhoRodape'
        db.create_table('os3marketing_cabecalhorodape', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('descricao', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('cabecalho', self.gf('django.db.models.fields.TextField')()),
            ('rodape', self.gf('django.db.models.fields.TextField')()),
            ('padrao', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('os3marketing', ['CabecalhoRodape'])

        # Adding model 'Newsletter'
        db.create_table('os3marketing_newsletter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content', self.gf('tinymce.models.HTMLField')()),
            ('server', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['os3marketing.SMTPServer'])),
            ('email_status', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sending_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modification_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('cabecalho_rodape', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['os3marketing.CabecalhoRodape'], null=True, blank=True)),
        ))
        db.send_create_signal('os3marketing', ['Newsletter'])

        # Adding M2M table for field mailing_list on 'Newsletter'
        db.create_table('os3marketing_newsletter_mailing_list', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('newsletter', models.ForeignKey(orm['os3marketing.newsletter'], null=False)),
            ('mailinglist', models.ForeignKey(orm['os3marketing.mailinglist'], null=False))
        ))
        db.create_unique('os3marketing_newsletter_mailing_list', ['newsletter_id', 'mailinglist_id'])

        # Adding model 'Template'
        db.create_table('os3marketing_template', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content', self.gf('tinymce.models.HTMLField')()),
        ))
        db.send_create_signal('os3marketing', ['Template'])

        # Adding model 'ContactMailingStatus'
        db.create_table('os3marketing_contactmailingstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('newsletter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['os3marketing.Newsletter'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['os3marketing.Contact'])),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('link', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['os3marketing.Link'], null=True, blank=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('os3marketing', ['ContactMailingStatus'])

        # Adding model 'Profile'
        db.create_table('os3marketing_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=255)),
        ))
        db.send_create_signal('os3marketing', ['Profile'])


    def backwards(self, orm):
        
        # Deleting model 'SMTPServer'
        db.delete_table('os3marketing_smtpserver')

        # Deleting model 'Contact'
        db.delete_table('os3marketing_contact')

        # Deleting model 'Link'
        db.delete_table('os3marketing_link')

        # Deleting model 'MailingList'
        db.delete_table('os3marketing_mailinglist')

        # Removing M2M table for field subscribers on 'MailingList'
        db.delete_table('os3marketing_mailinglist_subscribers')

        # Removing M2M table for field unsubscribers on 'MailingList'
        db.delete_table('os3marketing_mailinglist_unsubscribers')

        # Deleting model 'CabecalhoRodape'
        db.delete_table('os3marketing_cabecalhorodape')

        # Deleting model 'Newsletter'
        db.delete_table('os3marketing_newsletter')

        # Removing M2M table for field mailing_list on 'Newsletter'
        db.delete_table('os3marketing_newsletter_mailing_list')

        # Deleting model 'Template'
        db.delete_table('os3marketing_template')

        # Deleting model 'ContactMailingStatus'
        db.delete_table('os3marketing_contactmailingstatus')

        # Deleting model 'Profile'
        db.delete_table('os3marketing_profile')


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
        'os3marketing.link': {
            'Meta': {'ordering': "('creation_date',)", 'object_name': 'Link'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'os3marketing.mailinglist': {
            'Meta': {'ordering': "('creation_date',)", 'object_name': 'MailingList'},
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
