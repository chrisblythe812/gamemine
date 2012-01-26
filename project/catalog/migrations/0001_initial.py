# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Type'
        db.create_table('catalog_type', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('plural_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('catalog', ['Type'])

        # Adding model 'Genre'
        db.create_table('catalog_genre', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Type'], null=True, blank=True)),
            ('ordering', self.gf('django.db.models.fields.SmallIntegerField')(null=True, db_index=True)),
        ))
        db.send_create_signal('catalog', ['Genre'])

        # Adding unique constraint on 'Genre', fields ['name', 'type']
        db.create_unique('catalog_genre', ['name', 'type_id'])

        # Adding model 'Category'
        db.create_table('catalog_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('ordering', self.gf('django.db.models.fields.SmallIntegerField')(default=0, null=True, db_index=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Type'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True)),
            ('meta_title', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('meta_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('meta_keywords', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('catalog', ['Category'])

        # Adding model 'Game'
        db.create_table('catalog_game', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100, db_index=True)),
        ))
        db.send_create_signal('catalog', ['Game'])

        # Adding model 'Rating'
        db.create_table('catalog_rating', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Type'])),
            ('esrb_symbol', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=20, null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('catalog', ['Rating'])

        # Adding unique constraint on 'Rating', fields ['type', 'title']
        db.create_unique('catalog_rating', ['type_id', 'title'])

        # Adding model 'Publisher'
        db.create_table('catalog_publisher', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Type'], null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('catalog', ['Publisher'])

        # Adding unique constraint on 'Publisher', fields ['name', 'type']
        db.create_unique('catalog_publisher', ['name', 'type_id'])

        # Adding model 'Tag'
        db.create_table('catalog_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
        ))
        db.send_create_signal('catalog', ['Tag'])

        # Adding model 'Item'
        db.create_table('catalog_item', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upc', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50, db_index=True)),
            ('bre_id', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, db_index=True)),
            ('bsid', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, db_index=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('number_of_players', self.gf('django.db.models.fields.SmallIntegerField')(db_index=True, null=True, blank=True)),
            ('release_date', self.gf('django.db.models.fields.DateField')(null=True, db_index=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['catalog.Category'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Type'], null=True)),
            ('rating', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Rating'], null=True)),
            ('publisher', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Publisher'], null=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Game'], null=True)),
            ('votes', self.gf('django_snippets.thirdparty.models.json_field.JSONField')(null=True)),
            ('ratio', self.gf('django.db.models.fields.FloatField')(default=0, db_index=True)),
            ('buy_new_flag', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True)),
            ('buy_used_flag', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True)),
            ('trade_flag', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True)),
            ('rent_flag', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True)),
            ('muze_cache', self.gf('django_snippets.thirdparty.models.json_field.JSONField')(null=True)),
            ('retail_price_new', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=10, decimal_places=2, db_index=True)),
            ('retail_price_used', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=10, decimal_places=2)),
            ('retail_price_visco', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('wholesale_price_visco', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('quantity_visco', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('dropship_key_visco', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('retail_price_jack', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('wholesale_price_jack', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('quantity_jack', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('dropship_key_jack', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('retail_price_alpha', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('wholesale_price_alpha', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('quantity_alpha', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('dropship_key_alpha', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('profit', self.gf('django.db.models.fields.DecimalField')(default='0.0', max_digits=12, decimal_places=2)),
            ('retail_price_used_vendor', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=10, decimal_places=2)),
            ('wholesale_price_used', self.gf('django.db.models.fields.DecimalField')(default='0.0', max_digits=12, decimal_places=2)),
            ('quantity_used', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('trade_price', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=10, decimal_places=2, db_index=True)),
            ('trade_price_incomplete', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=10, decimal_places=2)),
            ('sold_amount', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('rent_amount', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('trade_amount', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('catalog', ['Item'])

        # Adding M2M table for field genres on 'Item'
        db.create_table('catalog_item_genres', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('item', models.ForeignKey(orm['catalog.item'], null=False)),
            ('genre', models.ForeignKey(orm['catalog.genre'], null=False))
        ))
        db.create_unique('catalog_item_genres', ['item_id', 'genre_id'])

        # Adding M2M table for field tags on 'Item'
        db.create_table('catalog_item_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('item', models.ForeignKey(orm['catalog.item'], null=False)),
            ('tag', models.ForeignKey(orm['catalog.tag'], null=False))
        ))
        db.create_unique('catalog_item_tags', ['item_id', 'tag_id'])

        # Adding model 'Review'
        db.create_table('catalog_review', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='content_type_set_for_review', to=orm['contenttypes.ContentType'])),
            ('object_pk', self.gf('django.db.models.fields.TextField')()),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=300, null=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(max_length=3000)),
            ('rating', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True, blank=True)),
            ('helpful_index', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('catalog', ['Review'])

        # Adding model 'ReviewHelpfulVote'
        db.create_table('catalog_reviewhelpfulvote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Review'])),
            ('vote', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('catalog', ['ReviewHelpfulVote'])

        # Adding model 'ItemVote'
        db.create_table('catalog_itemvote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Item'])),
            ('ratio', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True)),
            ('review', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['catalog.Review'], unique=True, null=True)),
        ))
        db.send_create_signal('catalog', ['ItemVote'])

        # Adding model 'ReportUpload'
        db.create_table('catalog_reportupload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('report', self.gf('django.db.models.fields.TextField')()),
            ('source', self.gf('django.db.models.fields.TextField')()),
            ('unknown_upc', self.gf('django.db.models.fields.TextField')()),
            ('unknown_upc_count', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('catalog', ['ReportUpload'])


    def backwards(self, orm):
        
        # Deleting model 'Type'
        db.delete_table('catalog_type')

        # Deleting model 'Genre'
        db.delete_table('catalog_genre')

        # Removing unique constraint on 'Genre', fields ['name', 'type']
        db.delete_unique('catalog_genre', ['name', 'type_id'])

        # Deleting model 'Category'
        db.delete_table('catalog_category')

        # Deleting model 'Game'
        db.delete_table('catalog_game')

        # Deleting model 'Rating'
        db.delete_table('catalog_rating')

        # Removing unique constraint on 'Rating', fields ['type', 'title']
        db.delete_unique('catalog_rating', ['type_id', 'title'])

        # Deleting model 'Publisher'
        db.delete_table('catalog_publisher')

        # Removing unique constraint on 'Publisher', fields ['name', 'type']
        db.delete_unique('catalog_publisher', ['name', 'type_id'])

        # Deleting model 'Tag'
        db.delete_table('catalog_tag')

        # Deleting model 'Item'
        db.delete_table('catalog_item')

        # Removing M2M table for field genres on 'Item'
        db.delete_table('catalog_item_genres')

        # Removing M2M table for field tags on 'Item'
        db.delete_table('catalog_item_tags')

        # Deleting model 'Review'
        db.delete_table('catalog_review')

        # Deleting model 'ReviewHelpfulVote'
        db.delete_table('catalog_reviewhelpfulvote')

        # Deleting model 'ItemVote'
        db.delete_table('catalog_itemvote')

        # Deleting model 'ReportUpload'
        db.delete_table('catalog_reportupload')


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
        'catalog.itemvote': {
            'Meta': {'object_name': 'ItemVote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Item']"}),
            'ratio': ('django.db.models.fields.SmallIntegerField', [], {}),
            'review': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['catalog.Review']", 'unique': 'True', 'null': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
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
        'catalog.reportupload': {
            'Meta': {'object_name': 'ReportUpload'},
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.TextField', [], {}),
            'source': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'unknown_upc': ('django.db.models.fields.TextField', [], {}),
            'unknown_upc_count': ('django.db.models.fields.IntegerField', [], {})
        },
        'catalog.review': {
            'Meta': {'object_name': 'Review'},
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '3000'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'content_type_set_for_review'", 'to': "orm['contenttypes.ContentType']"}),
            'helpful_index': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'object_pk': ('django.db.models.fields.TextField', [], {}),
            'rating': ('django.db.models.fields.SmallIntegerField', [], {}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'catalog.reviewhelpfulvote': {
            'Meta': {'object_name': 'ReviewHelpfulVote'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'review': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Review']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'vote': ('django.db.models.fields.IntegerField', [], {'default': '0'})
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
        'sites.site': {
            'Meta': {'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['catalog']
