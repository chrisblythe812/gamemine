import itertools
from datetime import datetime

from django.core.management.base import BaseCommand

from muze import Muze #@UnresolvedImport

from project.catalog.models import Item
from django.conf import settings


class Command(BaseCommand):
    args = '[--force] [muze-work-id] [recalc-votes]'
    help = 'Updating catalog items'
    
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.muze = Muze(settings.MUZE_DB)
        

    def handle(self, xls_filename=None, *args, **options):
        if '--force' in args:
            force = True
            del args['--force']
        else:
            force = False
        args = args or ['clean-muze-cache', 'recalc-votes']
        jobs = {
            'clean-muze-cache': self._do_clean_muze_cache,
            'recalc-votes': self._do_recalc_votes,
        }
        
        t0 = datetime.now()
        print 'Starting updating %d items...' % Item.objects.count() 
        for item, i in itertools.izip(Item.objects.all(), itertools.count()):
            save = False
            for job in args:
                save = jobs[job](item, force) or save
            if save:
                item.save()
            if i > 0 and i % 100 == 0:
                time = (datetime.now() - t0).seconds or 1 
                speed = i / time
                print 'Processed %d items (speed: %d items/sec)' % (i, speed)

        
    def _do_clean_muze_cache(self, item, force=False):
#        print item.get_screenshots()
        return False

    def _do_recalc_votes(self, item, force=False):
        item.recalc_votes()
        return True
