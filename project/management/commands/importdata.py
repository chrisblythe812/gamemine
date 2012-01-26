from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from project.catalog.models.ratings import Rating

class Command(BaseCommand):
    args = '[fixturename, ]'
    help = 'Import and normilize catalog data'

    def handle(self, *args, **options):
        def loaddata(fixture):
            print 'Importing %s...' % fixture
            if fixture.find('/') == -1:
                fixture = tuple(fixture.split('.'))
                fixture = 'project/%s/fixtures/%s.yaml' % fixture
            if settings.DEBUG:
                from os import path
                ff = fixture.split('.')
                ff.insert(-1, 'debug')
                ff = '.'.join(ff)
                if path.exists(settings.PROJECT_ROOT + '/' + ff):
                    fixture = ff
            call_command('loaddata', fixture)
        
        args = args or [
                        'project/fixtures/sites.yaml',
                        'project/fixtures/users.yaml',
                        'project/fixtures/discount.yaml',
                        'project/fixtures/rental_plans.yaml',
                        'project/fixtures/center.yaml',
                        'project/fixtures/cids.yaml',
                        'project/fixtures/counties.json',
                        'project/fixtures/taxes.yaml',
                        'project/fixtures/taxes-2.yaml',
                        'project/fixtures/dropships.yaml',
                        'project/fixtures/distributors.yaml',
                        'project/fixtures/allocation_factors.yaml',
#                        'project/fixtures/banners.json',
                        'catalog.types',
#                        'catalog.genres',
                        'catalog.ratings',
                        'catalog.categories',
                        #'catalog.games',
                        'catalog.publishers',
                        #'catalog.items',
                        #'catalog.item_genres',
                        #'catalog.item_votes',
                        ]
        for a in args:
            loaddata(a)

        print 'Fixing rating icons'
        icons = {
            'RP': 'ratingsymbol_rp.gif',
            'AO': 'ratingsymbol_ao.gif',
            'M': 'ratingsymbol_m.gif',
            'T': 'ratingsymbol_t.gif',
            'E10+': 'ratingsymbol_e10.gif',
            'E': 'ratingsymbol_e.gif',
            'EC': 'ratingsymbol_ec.gif',
        }
        for k, v in icons.items():
            for r in Rating.objects.filter(esrb_symbol__iexact=k):
                r.image = 'media/rating/' + v
                r.save() 
                
#        print 'Updating items...'
#        self._update_items()

    def _update_items(self):
        from project.catalog.models import Item
        for o in Item.objects.all():
            o.recalc_votes(False)
            o.save()
        