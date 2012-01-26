# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'RentList.added'
        db.alter_column('rent_rentlist', 'added', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'MemberRentalPlan.created'
        db.alter_column('rent_memberrentalplan', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'MemberRentalPlan.start_date'
        db.alter_column('rent_memberrentalplan', 'start_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'RentPlanCancellationReason.timestamp'
        db.alter_column('rent_rentplancancellationreason', 'timestamp', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'CancellationReason.creation_date'
        db.alter_column('rent_cancellationreason', 'creation_date', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'RentOrder.date_rent'
        db.alter_column('rent_rentorder', 'date_rent', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'MemberRentalPlanHistory.finish_date'
        db.alter_column('rent_memberrentalplanhistory', 'finish_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'RentOrderEvent.timestamp'
        db.alter_column('rent_rentorderevent', 'timestamp', self.gf('django.db.models.fields.DateTimeField')())


    def backwards(self, orm):
        
        # Changing field 'RentList.added'
        db.alter_column('rent_rentlist', 'added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True))

        # Changing field 'MemberRentalPlan.created'
        db.alter_column('rent_memberrentalplan', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True))

        # Changing field 'MemberRentalPlan.start_date'
        db.alter_column('rent_memberrentalplan', 'start_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True))

        # Changing field 'RentPlanCancellationReason.timestamp'
        db.alter_column('rent_rentplancancellationreason', 'timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True))

        # Changing field 'CancellationReason.creation_date'
        db.alter_column('rent_cancellationreason', 'creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True))

        # Changing field 'RentOrder.date_rent'
        db.alter_column('rent_rentorder', 'date_rent', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True))

        # Changing field 'MemberRentalPlanHistory.finish_date'
        db.alter_column('rent_memberrentalplanhistory', 'finish_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True))

        # Changing field 'RentOrderEvent.timestamp'
        db.alter_column('rent_rentorderevent', 'timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True))


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
            'bre_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'bsid': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'db_index': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['catalog.Category']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
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
            'retail_price_new': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'db_index': 'True'}),
            'retail_price_used': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'sold_amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'db_index': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalog.Tag']", 'null': 'True', 'symmetrical': 'False'}),
            'trade_amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'trade_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'trade_price': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'db_index': 'True'}),
            'trade_price_incomplete': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
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
            'barcode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'dropship': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inventory.Dropship']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_new': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'purchase_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['inventory.PurchaseItem']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
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
            'aim_transaction_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'applied_credits': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'card_data': ('django_snippets.models.blowfish_field.BlowfishField', [], {'null': 'True'}),
            'credit': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'debit': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment_method': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'tax': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'rent.allocationfactor': {
            'Meta': {'object_name': 'AllocationFactor'},
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'rent.cancellationreason': {
            'Meta': {'object_name': 'CancellationReason'},
            'confirmation_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'confirmation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'moving_traveling': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'not_enough_variety_of_games': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'only_signed_up_for_promotion': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'plan': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'poor_customer_service': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'poor_inventory_availability': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'service_costs_too_much': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'shipping_to_slow': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'switching_to_another_service': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'too_many_shipping_problems': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'website_is_not_user_friendly': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'rent.memberrentalplan': {
            'Meta': {'object_name': 'MemberRentalPlan'},
            'cancel_confirmation_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'cancel_confirmation_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'cancellation_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'delinquent_amout': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'delinquent_next_check': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_index': 'True'}),
            'delinquent_tax': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'first_payment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['members.BillingHistory']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next_payment_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'next_payment_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_index': 'True'}),
            'payment_fails_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'plan': ('django.db.models.fields.IntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'status_message': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'rent.memberrentalplanhistory': {
            'Meta': {'object_name': 'MemberRentalPlanHistory'},
            'finish_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plan': ('django.db.models.fields.IntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'rent.rentalplan': {
            'Meta': {'object_name': 'RentalPlan'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'expire_in': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'first_month': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'games_allowed': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'months': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'plan': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'store_credits': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'thereafter_months': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'})
        },
        'rent.rentlist': {
            'Meta': {'object_name': 'RentList'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
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
            'outgoing_endicia_data': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'outgoing_mail_label': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'outgoing_tracking_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'outgoing_tracking_scans': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
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
        },
        'rent.rentorderevent': {
            'Meta': {'object_name': 'RentOrderEvent'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'claim': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['claims.Claim']", 'null': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['rent.RentOrder']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'})
        },
        'rent.rentplancancellationreason': {
            'Meta': {'object_name': 'RentPlanCancellationReason'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moving_traveling': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'not_enough_variety_of_games': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'only_signed_up_for_promotion': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'plan': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'poor_customer_service': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'poor_inventory_availability': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'service_costs_too_much': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'shipping_to_slow': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'switching_to_another_service': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'too_many_shipping_problems': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'website_is_not_user_friendly': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['rent']
