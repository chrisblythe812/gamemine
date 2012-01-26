from ftplib import FTP
import tempfile
import os
import sys
from optparse import make_option
from datetime import datetime

from django.core.management.base import LabelCommand, BaseCommand
from django.conf import settings
from zipfile import ZipFile
from project.catalog.models.items import Item
from project.catalog.models.ratings import Rating

def parse_line(r, *args):
    r = r.rstrip().split('|')
    return r if len(r) > 1 else None


class Command(LabelCommand):
    def _get_args(self):
        for m in dir(self):
            if m.startswith('do_'):
                yield m[3:]

    help = 'Working with Ingram Database'
    label = 'command'

    option_list = list(BaseCommand.option_list) + [
        make_option('--init', action="store_true", dest="init", default=False),
    ]

    def handle_label(self, label, **options):
        self.options = options
        try:
            method = getattr(self, 'do_' + label)
        except:
            print >>sys.stderr, 'Possible commands: %s' % ', '.join(self._get_args())
            return
        self._items_cache = {}
        self._missing_items = set()
        method()

    def do_update(self):
        is_init = self.options['init']

        files = []

        ftp = settings.INGRAM['ftp']
        ftp_host = ftp['host']
        ftp_username = ftp['username']
        ftp_password = ftp['password']
        print 'Connecting to ftp://%s@%s' % (ftp_username, ftp_host)
        ftp = FTP(ftp_host)
        ftp.login(ftp_username, ftp_password)

        def get_file(filename):
            print 'Downloading %s...' % filename
            fd, fname = tempfile.mkstemp()
            files.append(fd)
            ftp.retrbinary('RETR %s' % filename, lambda b: os.write(fd, b))
            return fname

        today = datetime.now().date()
        counter = 0

        content_file_name = 'game_%s' % ('content' if is_init else 'update')
        content_file = '/pub/games/database/%s.zip' % content_file_name
        f = ZipFile(get_file(content_file), 'r')
        for rr in f.open('%s.txt' % content_file_name, 'r').readlines():
            r = parse_line(rr)
            upc = r[1]
            esrb = r[8]
            product_type_code = int(r[3])
            no_of_discs = int(r[7] or '0')
            try:
                item = Item.objects.get(upc=upc)
                if item.release_date > today:
                    try:
                        item.rating = Rating.objects.get(esrb_symbol=esrb)
                    except Rating.DoesNotExist:
                        pass
                if r[4].lower().find('bundle') != -1:
                    item.trade_flag = False
                    item.rent_flag = False
                elif product_type_code == 1:
                    item.active = True
                    item.trade_flag = True
                    item.rent_flag = True
                elif product_type_code in [6, 7]:
                    item.trade_flag = False
                    item.rent_flag = False
                elif no_of_discs == 1:
                    item.trade_flag = True
                    item.rent_flag = True
                elif no_of_discs > 1:
                    item.trade_flag = False
                    item.rent_flag = False
                item.ingram_code = r[0]
                item.save()

                print 'Processed: %s %d %d %s %s %s (%s)' % (item.upc,
                                                             product_type_code,
                                                             no_of_discs,
                                                             'x' if item.rent_flag else ' ',
                                                             'x' if item.trade_flag else ' ',
                                                             unicode(item),
                                                             item.category.name)
                counter += 1
            except Item.DoesNotExist:
                pass
            except:
                print 'AAAAAAAAAAAAAAAAAAAAAAAAAAAA: ', r[0]
                raise

        print counter

        from project.management.commands.ingram import Command as IngramCommand
        IngramCommand().handle()

        counter = 0

        ids = []

        images_file_name = 'images%sL' % ('' if is_init else '-update')
        images_file = '/pub/games/database/%s.zip' % images_file_name
        f = ZipFile(get_file(images_file), 'r')
        for fname in f.namelist():
            ingram_code, suffix = fname.split('.')
            ingram_code = ' '.join(ingram_code.split('_'))
            try:
                item = Item.objects.get(ingram_code=ingram_code)
                if item.active:
                    continue
                item.active = True
                item.save()
                pk = str(item.id)

                fout_name = os.path.join(settings.MEDIA_ROOT, 'media/covers', pk[:2], pk[2:4], pk + '.' + suffix)
                d = '/'.join(fout_name.split('/')[:-1])
                if not os.path.exists(d):
                    os.makedirs(d)

                fin = f.open(fname, 'r')
                with open(fout_name, 'w') as fout:
                    fout.write(fin.read())

                print 'Image Processed: %s %s (%s)' % (item.upc, unicode(item), item.category.name)
                counter += 1
                ids.append(pk)
            except Item.DoesNotExist:
                pass

        print counter

        if counter:
            fd, fname = tempfile.mkstemp()
            os.write(fd, '\n'.join(ids))
            os.lseek(fd, 0, os.SEEK_SET)

            from project.management.commands.muze import Command as MuzeCommand
            MuzeCommand().do_make_covers(filter_stream=os.fdopen(fd, 'r'))

        map(os.close, files)


    def do_test(self):
        import Image, ImageChops, ImageEnhance

        def autocrop(im, bgcolor):
            if im.mode != "RGB":
                im = im.convert("RGB")
            enh = ImageEnhance.Brightness(im)
            im2 = enh.enhance(1.5)
            bg = Image.new("RGB", im.size, bgcolor)
            diff = ImageChops.difference(im2, bg)
            bbox = diff.getbbox()
            if bbox:
                return im.crop(bbox)

        im = Image.open('/home/pashka/Documents/Projects/gamemine/static/media/covers/10/00/10000022.jpg')
        im2 = autocrop(im, (255, 255, 255))
        im2.save('/home/pashka/Documents/Projects/gamemine/static/media/covers/10/00/10000022-2.jpg')



    def do_new_imports(self):
        is_init = 'init'

        games_to_be_imported = ['752919553053','752919992852','711719812524','014633195378','014633195361','014633196481','014633196467','014633196702','014633196474','014633196870',
'767649403462','767649403424','752919552155','752919991954','730865900053','730865001385','014633098594','014633098587','752919553176','752919992982',
'711719810629','008888526834','008888346838','013388330577','013388340576','010086680522','010086690507','010086650464','010086670394','752919552391',
'752919992203','785138303789','767649403509','767649403400','083717202196','010086680539','010086690514','010086650488','047875841345','047875841369',
'047875841383','047875841406','047875841420','047875841444','893610001488','893610001471','040198002141','013388305018','008888526391','014633098938',
'014633098945','814290011017','008888346784','752919553060','752919992869','785138304755','785138364667','014633196016','014633196009','014633195989',
'014633195972','883929166787','893610001457','893610001440','650008500936','785138330525','785138304762','812872011394','812872014104','722674700290',
'045496902353','812872011387','047875765542','712725021245','712725021252','712725021238','712725021399','879278360006','008888166863','008888166764',
'785138364766','083717241850','712725021177','010086611007','023272342654','013388305025','045496741396','045496741402','045496741419','722674700306',
'662248910444','008888166078','008888166757','045496741389','008888166733','008888166702','008888166696','045496741556','040198002158','045496741426',
'014633194661','008888166740','083717241867']

        files = []

        ftp = settings.INGRAM['ftp']
        ftp_host = ftp['host']
        ftp_username = ftp['username']
        ftp_password = ftp['password']
        print 'Connecting to ftp://%s@%s' % (ftp_username, ftp_host)
        ftp = FTP(ftp_host)
        ftp.login(ftp_username, ftp_password)

        def get_file(filename):
            print 'Downloading %s...' % filename
            fd, fname = tempfile.mkstemp()
            files.append(fd)
            ftp.retrbinary('RETR %s' % filename, lambda b: os.write(fd, b))
            return fname

        today = datetime.now().date()
        counter = 0

        content_file_name = 'game_%s' % ('content' if is_init else 'update')
        content_file = '/pub/games/database/%s.zip' % content_file_name
        f = ZipFile(get_file(content_file), 'r')
        for rr in f.open('%s.txt' % content_file_name, 'r').readlines():
            r = parse_line(rr)
            upc = r[1]
            esrb = r[8]
            product_type_code = int(r[3])
            no_of_discs = int(r[7] or '0')
            if upc not in games_to_be_imported:
                continue
            try:
                item = Item.objects.get(upc=upc)
                if item.release_date > today:
                    try:
                        item.rating = Rating.objects.get(esrb_symbol=esrb)
                    except Rating.DoesNotExist:
                        pass
                if r[4].lower().find('bundle') != -1:
                    item.trade_flag = False
                    item.rent_flag = False
                elif product_type_code == 1:
                    item.active = True
                    item.trade_flag = True
                    item.rent_flag = True
                elif product_type_code in [6, 7]:
                    item.trade_flag = False
                    item.rent_flag = False
                elif no_of_discs == 1:
                    item.trade_flag = True
                    item.rent_flag = True
                elif no_of_discs > 1:
                    item.trade_flag = False
                    item.rent_flag = False
                item.ingram_code = r[0]
                item.save()
                print 'Processed: %s %d %d %s %s %s (%s)' % (item.upc,
                                                             product_type_code,
                                                             no_of_discs,
                                                             'x' if item.rent_flag else ' ',
                                                             'x' if item.trade_flag else ' ',
                                                             unicode(item),
                                                             item.category.name)
                counter += 1
            except Item.DoesNotExist:
                print "Nao existe upc: %s igram %s" % (upc,r[0])
                pass
            except:
                print 'AAAAAAAAAAAAAAAAAAAAAAAAAAAA: ', r[0]
                raise

        print counter

        from project.management.commands.ingram import Command as IngramCommand
        IngramCommand().handle()

        counter = 0

        ids = []

        images_file_name = 'images%sL' % ('' if is_init else '-update')
        images_file = '/pub/games/database/%s.zip' % images_file_name
        f = ZipFile(get_file(images_file), 'r')
        for fname in f.namelist():
            ingram_code, suffix = fname.split('.')
            ingram_code = ' '.join(ingram_code.split('_'))
            try:
                item = Item.objects.get(ingram_code=ingram_code)
                if item.upc not in games_to_be_imported:
                    continue
#                if item.active:
#                    continue
#                item.active = True
                item.save()
                pk = str(item.id)

                fout_name = os.path.join(settings.MEDIA_ROOT, 'media/covers', pk[:2], pk[2:4], pk + '.' + suffix)
                d = '/'.join(fout_name.split('/')[:-1])
                if not os.path.exists(d):
                    os.makedirs(d)

                fin = f.open(fname, 'r')
                with open(fout_name, 'w') as fout:
                    fout.write(fin.read())

                print 'Image Processed: %s %s (%s)' % (item.upc, unicode(item), item.category.name)
                counter += 1
                ids.append(pk)
            except Item.DoesNotExist:
                pass

        print counter

        if counter:
            fd, fname = tempfile.mkstemp()
            os.write(fd, '\n'.join(ids))
            os.lseek(fd, 0, os.SEEK_SET)

            from project.management.commands.muze import Command as MuzeCommand
            MuzeCommand().do_make_covers(filter_stream=os.fdopen(fd, 'r'))

        map(os.close, files)



    def do_manually_import_image(self):
        counter = 0
        ids = []
        images_file = '/home/webmaster/gamemine/project/management/commands/images05-09-11.zip'
        f = ZipFile(images_file, 'r')
        for fname in f.namelist():
            id, suffix = fname.split('.')
#            ingram_code = ' '.join(ingram_code.split('_'))
            try:
                item = Item.objects.get(id=id)
                pk = str(item.id)
                print settings.MEDIA_ROOT
                fout_name = os.path.join(settings.MEDIA_ROOT, 'media/covers', pk[:2], pk[2:4], pk + '.' + suffix)
                d = '/'.join(fout_name.split('/')[:-1])
                if not os.path.exists(d):
                    os.makedirs(d)

                fin = f.open(fname, 'r')
                with open(fout_name, 'w') as fout:
                    fout.write(fin.read())

                print 'Image Processed: %s %s (%s)' % (item.upc, unicode(item), item.category.name)
                counter += 1
                ids.append(pk)
            except Item.DoesNotExist:
                pass

        print counter

        if counter:
            fd, fname = tempfile.mkstemp()
            os.write(fd, '\n'.join(ids))
            os.lseek(fd, 0, os.SEEK_SET)

            from project.management.commands.muze import Command as MuzeCommand
            MuzeCommand().do_make_covers(filter_stream=os.fdopen(fd, 'r'))
#
#        #map(os.close, files
