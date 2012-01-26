# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Ticket'
        db.create_table('crm_ticket', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('crm', ['Ticket'])

        # Adding model 'PersonalGameTicket'
        db.create_table('crm_personalgameticket', (
            ('ticket_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['crm.Ticket'], unique=True, primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['rent.RentOrder'])),
        ))
        db.send_create_signal('crm', ['PersonalGameTicket'])

        # Adding model 'TicketHistory'
        db.create_table('crm_tickethistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ticket', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['crm.Ticket'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('message', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('crm', ['TicketHistory'])


    def backwards(self, orm):
        
        # Deleting model 'Ticket'
        db.delete_table('crm_ticket')

        # Deleting model 'PersonalGameTicket'
        db.delete_table('crm_personalgameticket')

        # Deleting model 'TicketHistory'
        db.delete_table('crm_tickethistory')


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
        'catalog.category': {
            'Meta': {'object_name': 'Category'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'bid': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'game_weight': ('django.db.models.fields.DecimalField', [], {'default': "'6.0'", 'max_digits': '5', 'decimal_places': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'meta_keywords': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'meta_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'ordering': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'null': 'True', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Type']"})
        },
        'catalog.game': {
            'Meta': {'object_name': 'Game'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'catalog.genre': {
            'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Genre'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'ordering': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Type']", 'null': 'True', 'blank': 'True'})
        },
        'catalog.item': {
            'Meta': {'object_name': 'Item'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'base_retail_price_new': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'base_retail_price_used': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'base_trade_price': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'bre_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'bsid': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'db_index': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['catalog.Category']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'details_page_views': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Game']", 'null': 'True'}),
            'genre_list': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'db_index': 'True'}),
            'genres': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalog.Genre']", 'null': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'muze_cache': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'number_of_online_players': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'number_of_players': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'publisher': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Publisher']", 'null': 'True'}),
            'rating': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Rating']", 'null': 'True'}),
            'ratio': ('django.db.models.fields.FloatField', [], {'default': '0', 'db_index': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_index': 'True'}),
            'rent_amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'rent_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'rent_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'retail_price_new': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'db_index': 'True'}),
            'retail_price_used': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'sold_amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'db_index': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalog.Tag']", 'null': 'True', 'symmetrical': 'False'}),
            'trade_amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'trade_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'trade_price': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'db_index': 'True'}),
            'trade_price_incomplete': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Type']", 'null': 'True'}),
            'upc': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'votes': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'})
        },
        'catalog.publisher': {
            'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Publisher'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Type']", 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'catalog.rating': {
            'Meta': {'unique_together': "(('type', 'title'),)", 'object_name': 'Rating'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'esrb_symbol': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Type']"})
        },
        'catalog.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'catalog.type': {
            'Meta': {'object_name': 'Type'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'plural_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'crm.feedbackifyfeedback': {
            'Meta': {'object_name': 'FeedbackifyFeedback'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'context': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'feedback': ('django.db.models.fields.TextField', [], {}),
            'form_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'payload': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'subcategory': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'crm.personalgameticket': {
            'Meta': {'object_name': 'PersonalGameTicket', '_ormbases': ['crm.Ticket']},
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rent.RentOrder']"}),
            'ticket_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['crm.Ticket']", 'unique': 'True', 'primary_key': 'True'})
        },
        'crm.reply': {
            'Meta': {'object_name': 'Reply'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailed_to': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'})
        },
        'crm.ticket': {
            'Meta': {'object_name': 'Ticket'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'crm.tickethistory': {
            'Meta': {'object_name': 'TicketHistory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'ticket': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['crm.Ticket']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'inventory.distributor': {
            'Meta': {'object_name': 'Distributor'},
            'address': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'new_games_vendor': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'})
        },
        'inventory.dropship': {
            'Meta': {'object_name': 'Dropship'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'bid': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label_sizes': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'lon': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'printers': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'inventory.inventory': {
            'Meta': {'object_name': 'Inventory'},
            'added_at_manual_check': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'barcode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'buy_only': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'dropship': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inventory.Dropship']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_new': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']", 'null': 'True'}),
            'manual_check_discarded': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'manual_checked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'manual_checked_dc': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'manual_checked'", 'null': 'True', 'to': "orm['inventory.Dropship']"}),
            'not_expected_to_return': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'purchase_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inventory.PurchaseItem']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'tmp_new_dc_code_aproved': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'tmp_saved_dc_code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True'})
        },
        'inventory.purchase': {
            'Meta': {'object_name': 'Purchase'},
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'distributor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inventory.Distributor']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_new': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        'inventory.purchaseitem': {
            'Meta': {'object_name': 'PurchaseItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'purchase': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['inventory.Purchase']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {})
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
        },
        'rent.rentorder': {
            'Meta': {'object_name': 'RentOrder'},
            'date_delivered': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date_prepared': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date_rent': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'date_returned': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date_shipped': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date_shipped_back': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incoming_endicia_data': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'incoming_mail_label': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'incoming_tracking_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'incoming_tracking_scans': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inventory.Inventory']", 'null': 'True', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'map': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'next_penalty_check': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'outgoing_endicia_data': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'outgoing_mail_label': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'outgoing_tracking_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'outgoing_tracking_scans': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'penalty_payment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['members.BillingHistory']", 'unique': 'True', 'null': 'True'}),
            'prepared_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'prepared_games'", 'null': 'True', 'to': "orm['auth.User']"}),
            'return_accepted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'return_accepted_games'", 'null': 'True', 'to': "orm['auth.User']"}),
            'shipped_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'shipped_rent_orders'", 'null': 'True', 'to': "orm['auth.User']"}),
            'shipping_address1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'shipping_address2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'shipping_city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'shipping_county': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'shipping_state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True'}),
            'shipping_zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'source_dc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inventory.Dropship']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'status_message': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['crm']
