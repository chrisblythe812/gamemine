# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BuyCart'
        db.create_table('buy_orders_buycart', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, null=True)),
            ('anonymous_cart_id', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, db_index=True)),
            ('size', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now=True, auto_now_add=True, blank=True)),
            ('last_session_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('buy_orders', ['BuyCart'])

        # Adding model 'BuyCartItem'
        db.create_table('buy_orders_buycartitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cart', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['buy_orders.BuyCart'])),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Item'])),
            ('quantity', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('is_new', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True)),
            ('user_session_id', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('user_session_price', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('buy_orders', ['BuyCartItem'])

        # Adding model 'BuyOrder'
        db.create_table('buy_orders_buyorder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('message', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, null=True)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True)),
            ('shipping_address1', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('shipping_address2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('shipping_city', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('shipping_state', self.gf('django.db.models.fields.CharField')(max_length=2, null=True)),
            ('shipping_zip_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('billing_first_name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True)),
            ('billing_last_name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True)),
            ('billing_address1', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('billing_address2', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('billing_city', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('billing_state', self.gf('django.db.models.fields.CharField')(max_length=2, null=True)),
            ('billing_zip_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('card_type', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('card_display_number', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
            ('card_data', self.gf('django_snippets.models.blowfish_field.BlowfishField')(null=True)),
            ('total', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2)),
            ('size', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('endicia_data', self.gf('django_snippets.thirdparty.models.json_field.JSONField')(null=True)),
            ('mail_label', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True)),
            ('tracking_number', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
        ))
        db.send_create_signal('buy_orders', ['BuyOrder'])

        # Adding model 'BuyOrderItem'
        db.create_table('buy_orders_buyorderitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['buy_orders.BuyOrder'])),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Item'])),
            ('quantity', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('is_new', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True)),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('reserve', self.gf('django_snippets.thirdparty.models.json_field.JSONField')(default='{}')),
        ))
        db.send_create_signal('buy_orders', ['BuyOrderItem'])

        # Adding model 'BuyOrderHistory'
        db.create_table('buy_orders_buyorderhistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name='history', to=orm['buy_orders.BuyOrder'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('message', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, null=True)),
        ))
        db.send_create_signal('buy_orders', ['BuyOrderHistory'])

        # Adding model 'BuyList'
        db.create_table('buy_orders_buylist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, db_index=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Item'])),
            ('is_new', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('buy_alert', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('buy_orders', ['BuyList'])


    def backwards(self, orm):
        
        # Deleting model 'BuyCart'
        db.delete_table('buy_orders_buycart')

        # Deleting model 'BuyCartItem'
        db.delete_table('buy_orders_buycartitem')

        # Deleting model 'BuyOrder'
        db.delete_table('buy_orders_buyorder')

        # Deleting model 'BuyOrderItem'
        db.delete_table('buy_orders_buyorderitem')

        # Deleting model 'BuyOrderHistory'
        db.delete_table('buy_orders_buyorderhistory')

        # Deleting model 'BuyList'
        db.delete_table('buy_orders_buylist')


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
        'buy_orders.buycart': {
            'Meta': {'object_name': 'BuyCart'},
            'anonymous_cart_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_session_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True'})
        },
        'buy_orders.buycartitem': {
            'Meta': {'object_name': 'BuyCartItem'},
            'cart': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['buy_orders.BuyCart']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_new': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user_session_id': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user_session_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'})
        },
        'buy_orders.buylist': {
            'Meta': {'object_name': 'BuyList'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'buy_alert': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_new': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'buy_orders.buyorder': {
            'Meta': {'object_name': 'BuyOrder'},
            'billing_address1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'billing_address2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'billing_city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'billing_first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'billing_last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'billing_state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True'}),
            'billing_zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'card_data': ('django_snippets.models.blowfish_field.BlowfishField', [], {'null': 'True'}),
            'card_display_number': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'card_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'endicia_data': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'mail_label': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True'}),
            'shipping_address1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'shipping_address2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'shipping_city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'shipping_state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True'}),
            'shipping_zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'tracking_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'buy_orders.buyorderhistory': {
            'Meta': {'object_name': 'BuyOrderHistory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'history'", 'to': "orm['buy_orders.BuyOrder']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'buy_orders.buyorderitem': {
            'Meta': {'object_name': 'BuyOrderItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_new': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['buy_orders.BuyOrder']"}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'reserve': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'default': "'{}'"})
        },
        'catalog.category': {
            'Meta': {'object_name': 'Category'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
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
            'buy_new_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'buy_used_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['catalog.Category']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'dropship_key_alpha': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'dropship_key_jack': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'dropship_key_visco': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Game']", 'null': 'True'}),
            'genres': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalog.Genre']", 'null': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'muze_cache': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'number_of_players': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'profit': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '12', 'decimal_places': '2'}),
            'publisher': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Publisher']", 'null': 'True'}),
            'quantity_alpha': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'quantity_jack': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'quantity_used': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'quantity_visco': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rating': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Rating']", 'null': 'True'}),
            'ratio': ('django.db.models.fields.FloatField', [], {'default': '0', 'db_index': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_index': 'True'}),
            'rent_amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'rent_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'retail_price_alpha': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'retail_price_jack': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'retail_price_new': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'db_index': 'True'}),
            'retail_price_used': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'retail_price_used_vendor': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'retail_price_visco': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'sold_amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['catalog.Tag']", 'null': 'True', 'symmetrical': 'False'}),
            'trade_amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'trade_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'trade_price': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'db_index': 'True'}),
            'trade_price_incomplete': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Type']", 'null': 'True'}),
            'upc': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'votes': ('django_snippets.thirdparty.models.json_field.JSONField', [], {'null': 'True'}),
            'wholesale_price_alpha': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'wholesale_price_jack': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'wholesale_price_used': ('django.db.models.fields.DecimalField', [], {'default': "'0.0'", 'max_digits': '12', 'decimal_places': '2'}),
            'wholesale_price_visco': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'})
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
        }
    }

    complete_apps = ['buy_orders']
