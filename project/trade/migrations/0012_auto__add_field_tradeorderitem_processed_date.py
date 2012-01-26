# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'TradeOrderItem.processed_date'
        db.add_column('trade_tradeorderitem', 'processed_date', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'TradeOrderItem.processed_date'
        db.delete_column('trade_tradeorderitem', 'processed_date')


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
            'game_weight': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'genre_list': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'db_index': 'True'}),
            'genres': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalog.Genre']", 'null': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'muze_cache': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'number_of_online_players': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'number_of_players': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'prebook_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
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
        'trade.tradecart': {
            'Meta': {'object_name': 'TradeCart'},
            'anonymous_cart_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_session_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True'})
        },
        'trade.tradecartitem': {
            'Meta': {'object_name': 'TradeCartItem'},
            'cart': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['trade.TradeCart']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_complete': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user_session_id': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user_session_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'})
        },
        'trade.tradelistitem': {
            'Meta': {'object_name': 'TradeListItem'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_complete': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['catalog.Item']"}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tradelist'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'trade.tradeorder': {
            'Meta': {'object_name': 'TradeOrder'},
            'barcode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'received_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'shipping_address1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'shipping_address2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'shipping_city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'shipping_county': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'shipping_state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True'}),
            'shipping_zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'trade.tradeorderitem': {
            'Meta': {'object_name': 'TradeOrderItem'},
            'declined': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inventory.Inventory']", 'null': 'True'}),
            'is_broken': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_damaged': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_exellent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_factory_sealed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_heavily_scratched': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_lightly_scratched': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_like_new': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_mailback': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_match': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_refurblished': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_unplayable': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'is_very_good': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['trade.TradeOrder']"}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'processed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'returning_endicia_data': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'returning_mail_label': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'})
        }
    }

    complete_apps = ['trade']
