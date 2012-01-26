from logging import debug

from ftplib import FTP
import itertools
import os
import subprocess
import Image
from shutil import copyfile
from optparse import make_option
from zipfile import ZipFile
import tempfile
from hashlib import md5

from django.core.management.base import LabelCommand, BaseCommand
from django.conf import settings
from django.db import transaction

from project.catalog.models import Item
from project.staff.models import MuzeUpdateLog, MuzeUpdate
import sys

def mkdir_p(path):
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


muze_blanks = {
    'association': {
        'associationid': '',
        'id_1': '',
        'id_2': '',
        'associationtype': '',
        'weight': 0,
        'action': '',
    },
    'attribute': {
        'attributeid': '',
        'type': '',
        'propertytypeid': '',
        'attribute': '',
        'keyattribute': '',
        'description': '',
        'format': '',
        'range': '',
        'enumeratedvalues': '',
        'n_links': 0,
        'n_objects': 0,
        'n_values': 0,
        'n_children': 0,
        'n_parents': 0,
        'action': '',
    },
    'attributeassociation': {
        'attributeassociationid': '',
        'attributeid_1': '',
        'attributeid_2': '',
        'associationtype': '',
        'groupid': '',
        'action': '',
    },
    'attributelink': {
        'attributelinkid': '',
        'objectid': '',
        'propertyattributeid': '',
        'valueattributeid': '',
        'value': '',
        'weight': 0,
        'rank': 0,
        'p_baseobjectid': '',
        'action': '',
    },
    'clip': {
        'clipid': '',
        'filename': '',
        'width': 0,
        'height': 0,
        'mimetype': '',
        'filesize': 0,
        'length': 0,
        'setid': 0,
        'action': '',
    },
    'cliplink': {
        'cliplinkid': '',
        'mainobjectid': '',
        'clipid': '',
        'classificationattributeid': '',
        'positionattributeid': '',
        'caption': '',
        'sortorder': 0,
        'publishdate': '1970-01-01',
        'p_filename': '',
        'p_width': 0,
        'p_height': 0,
        'p_mimetype': '',
        'p_filesize': 0,
        'p_ratio': 0,
        'p_length': 0,
        'p_setid': 0,
        'action': '',
    },
    'document': {
        'documentid': '',
        'typeattributeid': '',
        'title': '',
        'fulltext': '',
        'url': '',
        'format': '',
        'action': '',
    },
    'image': {
        'imageid': '',
        'filename': '',
        'width': 0,
        'height': 0,
        'mimetype': '',
        'filesize': 0,
        'action': '',
    },
    'imagelink': {
        'imagelinkid': '',
        'mainobjectid': '',
        'imageid': '',
        'classificationattributeid': '',
        'positionattributeid': '',
        'caption': '',
        'sortorder': 0,
        'publishdate': '1970-01-01',
        'p_filename': '',
        'p_width': 0,
        'p_height': 0,
        'p_mimetype': '',
        'p_filesize': 0,
        'p_ratio': 0,
        'action': '',
    },
    'name': {
        'nameid': '',
        'type': '',
        'name': '',
        'keyname': '',
        'n_attributes': 0,
        'n_associations': 0,
        'action': '',
    },
    'release': {
        'releaseid': '',
        'workid': '',
        'releasedate': '1970-01-01',
        'upc': '',
        'msrp': '',
        'territory': '',
        'action': '',
    },
    'work': {
        'workid': '',
        'type': '',
        'title': '',
        'keytitle': '',
        'originalreleasedate': '1970-01-01',
        'n_attributes': '',
        'n_associations': '',
        'action': '',
    }
}


class Command(LabelCommand):
    args = '[download-images download-videos make-thumbs cleanup clean-cache update-cache update update-retail-prices update-db daily-db-update update-media]'
    help = 'Working with muze data'
    label = 'command'
    option_list = list(BaseCommand.option_list) + [
        make_option('--file'),
    ]

    def handle_label(self, label, **options):
        if label == 'download-images':
            self.do_download_images()
        elif label == 'download-videos':
            self.do_download_videos()
        elif label == 'update-videos':
            self.do_update_videos()
        elif label == 'update-images':
            self.do_update_images()
        elif label == 'make-thumbs':
            self.do_make_thumbs()
        elif label == 'make-covers':
            self.do_make_covers()
        elif label == 'make-video-thumbs':
            self.do_make_video_thumbs()
        elif label == 'cleanup':
            self.do_cleanup()
        elif label == 'clean-cache':
            self.do_clean_cache()
        elif label == 'update-cache':
            self.do_update_cache()
        elif label == 'update':
            self.do_update()
        elif label == 'update-db':
            self.do_update_db(**options)
        elif label == 'daily-db-update':
            self.daily_db_update(**options)
        elif label == 'update-media':
            self.do_update_media()
        else:
            print 'error: possible parameters: %s' % self.args

    def _get_files(self):
        print 'Collecting filenames...'
        screenshots = []
        item_count = Item.objects.count()
        for item, i in itertools.izip(Item.objects.all(), itertools.count()):
            if i > 0 and i % 100 == 0:
                print '%d%% (%d files)' % (int(float(i) / item_count * 100), len(screenshots))

            screenshots += [x['file_name'] for x in item.get_screenshots() or []]

        print 'Collected %d files' % len(screenshots)
        return screenshots


    def do_download_images(self):
        screenshots = self._get_files()
        files = screenshots
        files.sort()

        ftp_host = settings.MUZE_FTP['host']
        ftp_username = settings.MUZE_FTP['username']
        ftp_password = settings.MUZE_FTP['password']
        print 'Connecting to ftp://%s@%s' % (ftp_username, ftp_host)
        ftp = FTP(ftp_host)
        ftp.login(ftp_username, ftp_password)

        file_count = len(files)
        file_prefix = settings.MEDIA_ROOT + '/muze/ImageFull'
        for fname, i in itertools.izip(files, itertools.count()):
            print '%s... [%d of %d]' % (fname, i, file_count)
            file_name = file_prefix + '/' + fname
            if os.path.exists(file_name):
                continue

            d = '/'.join(file_name.split('/')[:-1])
            if not os.path.exists(d):
                os.makedirs(d)

            try:
                f = open(file_name, 'w')

                def callback(b):
                    f.write(b)

                ftp.retrbinary('RETR /media/ImageFull/%s' % fname, callback)
                f.close()
            except:
                os.unlink(file_name)
#                raise


    def _get_video_files(self):
        print 'Collecting filenames...'
        videos = set()
        item_count = Item.objects.count()
        for item, i in itertools.izip(Item.objects.all(), itertools.count()):
            if i > 0 and i % 100 == 0:
                print '%d%% (%d files)' % (int(float(i) / item_count * 100), len(videos))

            #videos += [x['file_name'] for x in item.get_videos() or []]
            for v in item.get_videos2():
                videos.add(v['f1'])
                videos.add(v['f2'])

        print 'Collected %d files' % len(videos)
        return list(videos)

    def do_download_videos(self):
        files = self._get_video_files()
        files.sort()

        file_prefix = settings.MEDIA_ROOT + '/muze/Clip'
        fff = []
        for fname in files:
            if not os.path.exists(file_prefix + '/' + fname):
                fff.append(fname)
        files = fff

        ftp_host = settings.MUZE_FTP['host']
        ftp_username = settings.MUZE_FTP['username']
        ftp_password = settings.MUZE_FTP['password']
        print 'Connecting to ftp://%s@%s' % (ftp_username, ftp_host)
        ftp = FTP(ftp_host)
        ftp.login(ftp_username, ftp_password)

        file_count = len(files)
        for fname, i in itertools.izip(files, itertools.count()):
            print '%s... [%d of %d]' % (fname, i, file_count)
            file_name = file_prefix + '/' + fname
            if os.path.exists(file_name):
                continue

            print '  Downloading...'

            d = '/'.join(file_name.split('/')[:-1])
            if not os.path.exists(d):
                os.makedirs(d)

            try:
                f = open(file_name, 'w')

                def callback(b):
                    f.write(b)

                ftp.retrbinary('RETR /media/Clip/%s' % fname, callback)
                f.close()
            except KeyboardInterrupt, _e:
                os.unlink(file_name)
                return
            except:
                os.unlink(file_name)

    def _make_thumb(self, file_prefix, source_prefix, fname, size, alt=False, suffix='jpg', force=False):
        file_name = '%s/%dx%d/%s' % (file_prefix, size[0], size[1], fname)
        file_name = '.'.join(file_name.split('.')[:-1]) + '.' + suffix
        if not force and os.path.exists(file_name):
            return

        d = '/'.join(file_name.split('/')[:-1])
        if not os.path.exists(d):
            os.makedirs(d)

        try:
            source = os.path.join(source_prefix, fname)
            image = Image.open(source)
            bbox = image.getbbox()

            w1 = float(bbox[2])
            h1 = float(bbox[3])
            w2 = float(size[0])
            h2 = float(size[1])

            if alt:
                image = image.convert("RGBA")
                image.thumbnail(size, Image.ANTIALIAS)
                sw, sh = image.size
                x = int((w2 - sw) / 2)
                y = int((h2 - sh) / 2)
                image = image.crop((-x, -y, size[0] - x, size[1] - y))
                image.save(file_name)
            else:
                d2 = w2 / h2

                if w1 < d2 * h1:
                    l = (1 - w1 / d2 / h1) / 2
                    lx, ty, rx, by = 0.0, l, 1.0, 1 - l
                else:
                    l = (1 - d2 * h1 / w1) / 2
                    lx, ty, rx, by = l, 0.0, 1 - l, 1.0

                crop_box = [int(x) for x in (lx * w1, ty * h1, rx * w1, by * h1)]

                image = image.crop(tuple(crop_box))
                image.load()
                image = image.resize(size, Image.ANTIALIAS)
                image.save(file_name)
        except KeyboardInterrupt:
            raise
        except Exception, e:
            debug(e)
            return


    def do_make_covers(self, filter_stream=sys.stdin):
        print 'Processing covers...'
        covers_root = settings.MEDIA_ROOT + '/covers'
        covers = []
        for root, _dirs, files in os.walk(covers_root):
            covers += [os.path.relpath(os.path.join(root, f), covers_root) for f in files]

        file_filter = set()
        # for f in filter_stream.readlines():
        #     f = f.strip()
        #     if f:
        #         file_filter.add(f)

        file_count = len(file_filter) or len(covers)
        file_prefix = settings.MEDIA_ROOT + '/thumbs/covers'

        i = 0
        for fname in covers:
            f = '.'.join(fname.split('/')[-1].split('.')[:-1])
            if fname == 'ITEMS' or (file_filter and f not in file_filter):
                continue

            i += 1
            print '%s... [%d of %d]' % (fname, i, file_count)

            self._make_thumb(file_prefix, covers_root, fname, (230, 320), True, suffix='png', force=True)
            self._make_thumb(file_prefix, covers_root, fname, (170, 220), True, suffix='png', force=True)
            self._make_thumb(file_prefix, covers_root, fname, (140, 190), True, suffix='png', force=True)
            self._make_thumb(file_prefix, covers_root, fname, (120, 160), True, suffix='png', force=True)
            self._make_thumb(file_prefix, covers_root, fname, (55, 70), True, suffix='png', force=True)
            self._make_thumb(file_prefix, covers_root, fname, (80, 100), True, suffix='png', force=True)
            self._make_thumb(file_prefix, covers_root, fname, (37, 47), True, suffix='png', force=True)


    def do_make_thumbs(self):
        print 'Processing screenshots...'
        screenshots = self._get_files()
        file_count = len(screenshots)
        source_prefix = settings.MEDIA_ROOT + '/muze/ImageFull'
        file_prefix = settings.MEDIA_ROOT + '/thumbs/muze'
        for fname, i in itertools.izip(screenshots, itertools.count()):
            print '%s... [%d of %d]' % (fname, i, file_count)

            self._make_thumb(file_prefix, source_prefix, fname, (330, 200))
            self._make_thumb(file_prefix, source_prefix, fname, (40, 25))
            self._make_thumb(file_prefix, source_prefix, fname, (719, 403), True)

    def do_make_video_thumbs(self):
        video_files = self._get_video_files()
        src_root = settings.MEDIA_ROOT + '/muze/Clip'
        dst_root = settings.MEDIA_ROOT + '/thumbs/muze/Clip'

        blank_40x24 = settings.STATIC_ROOT + '/b40x24.jpg'
        bad_videos = []

        dev_null = os.open('/dev/null', os.O_WRONLY)

        for v in video_files:
            src = os.path.join(src_root, v)
            if not os.path.exists(src):
                continue

            n, e = os.path.splitext(v) #@UnusedVariable
            print n
            thumb = os.path.join(dst_root, n + '.jpg')
            if os.path.exists(thumb):
                continue
            mkdir_p(os.path.dirname(thumb))
            try:
                subprocess.check_call(['ffmpeg',
                                       '-v', '-10', # verbosity
                                       '-ss', '15', # 15th second
                                       '-i', src, # source
                                       '-vframes', '1',
                                       '-an', # disable audio
                                       '-f', 'image2', # image
                                       '-s', '40x24', # output dimensions
                                       thumb], # output file
                                      stdout=dev_null, stderr=dev_null)
            except:
                bad_videos.append(src)
                copyfile(blank_40x24, thumb)

        os.close(dev_null)
        print 'BAD VIDEOS:'
        for b in bad_videos:
            print b
        print 'TOTAL: %s' % len(bad_videos)

    def do_cleanup(self):
        items = Item.objects.all()
        count = items.count()
        counter = 0
        for i, c in itertools.izip(items, itertools.count(1)):
            if c % 100 == 0:
                print 'Processed %d items of %d. Cleaned %d file(s)...' % (c, count, counter)
            screenshots = []
            ss = i.muze_cache.get('screenshots', [])
            for s in ss:
                def check(f):
                    p = ['muze/ImageFull', 'thumbs/muze/330x200', 'thumbs/muze/40x25']
                    for pp in p:
                        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, pp, s['file_name'])):
                            return False
                    return True
                if check(s['file_name']):
                    screenshots.append(s)
                else:
                    print 'Missed: %s' % s['file_name']
                    counter += 1
            if len(ss) != len(screenshots):
                i.muze_cache['screenshots'] = screenshots
                i.save()
        print 'Done. Cleaned %d file(s)...' % counter

    @transaction.commit_on_success
    def do_clean_cache(self):
        items = Item.objects.all()
        count = items.count()
        for i, c in itertools.izip(items, itertools.count(1)):
            if c % 100 == 0:
                print 'Processed %d items of %d...' % (c, count)
            i.muze_cache = None
            i.save()

    @transaction.commit_on_success
    def do_update_cache(self):
        items = Item.objects.all()
        count = items.count()
        for i, c in itertools.izip(items, itertools.count(1)):
            if c % 100 == 0:
                print 'Processed %d items of %d...' % (c, count)
            i.muze_cache = None
            i.get_front_image()
            i.get_screenshots()
            i.get_videos()
            i.get_muze_description()
            i.get_muze_msrp()
            i.save()

    def do_update(self):
        debug('Updating muze database...')
        self.daily_db_update()
        debug('Updating muze cache...')
        self.do_update_cache()

    def do_update_videos(self):
        debug('Downloading videos...')
        self.do_download_videos()
        debug('Making thumbnails for videos...')
        self.do_make_video_thumbs()

    def do_update_images(self):
        debug('Downloading images...')
        self.do_download_images()
        debug('Making thumbnails for pictures...')
        self.do_make_thumbs()

    def do_update_media(self):
        self.do_update_videos()
        self.do_update_images()

    def do_update_db(self, file, dry_run=False, **options):
        from xml.sax import parse, ContentHandler

        class XmlReader(ContentHandler):
            def __init__(self, file, callback):
                self.file = file
                self.callback = callback
                self.table_name = file.name.split('.')[0]
                self._tag_name = 'Games' + self.table_name
                self._data = None
                self._text = None

            def run(self):
                parse(self.file, self)

            def startElement(self, name, attrs):
                if name == self._tag_name:
                    self._data = {}
                elif self._data is not None:
                    self._text = ''
                    self._data[name] = None

            def endElement(self, name):
                if name == self._tag_name:
                    self.callback(self.table_name, self._data)
                elif self._data is not None:
                    self._data[name] = (self._text or '').strip()

            def characters(self, content):
                if self._text is not None:
                    self._text += content


        connection = settings.MUZE_DB
#        connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_UNCOMMITTED)
        cursor = connection.cursor()

        file = os.path.expanduser(file)
        print 'Opening %s...' % file
        zipfile = ZipFile(file, 'r')
        try:
            for fname in zipfile.namelist():
                print '\n  Reading %s...' % fname
                file = zipfile.open(fname, 'r')
                try:
                    class Counter(object):
                        cnt = 0

                    counter = Counter()

                    def callback(table_name, data):
                        table_name = table_name.lower()
                        row = muze_blanks[table_name]
                        for k, v in data.items():
                            key = k.lower()
                            row[key] = v or row[key]
                        try:
                            action = row['action']
                            if action == 'A':
                                fields, values = [], []
                                for k, v in row.items():
                                    fields.append(k)
                                    values.append(v)
                                sql = 'insert into "%s"(%s) values (%s)' % (table_name,
                                                                            ', '.join(map(lambda x: '"%s"' % x, fields)),
                                                                            ', '.join(['%s'] * len(values)))
                                params = values
                            elif action == 'C':
                                fields, values = [], []
                                for k, v in row.items():
                                    fields.append(k)
                                    values.append(v)
                                k = table_name + 'id'
                                sql = 'update "%s" set %s where "%s" = %%s' % (table_name,
                                                              ', '.join(map(lambda x: '"%s" = %%s' % x, fields)),
                                                              k)
                                params = values + [row[k]]
                            elif action == 'D':
                                k = table_name + 'id'
                                sql = 'delete from "%s" where "%s" = %%s;' % (table_name, k)
                                params = [row[k]]
                            else:
                                print 'Unknown action %s' % action
                                return
                            sql = sql.encode('ascii')
                            cursor.execute(sql, params)
                            counter.cnt += 1
                            if counter.cnt % 1000 == 0:
                                print 'Processed %d records...' % counter.cnt
                        except Exception, e:
                            print e
                            print 'FAILED ON: %s' % row
                            raise

#                    table_name = file.name.split('.')[0].lower()
#                    cursor.execute('select count(1) from "%s"' % table_name)
#                    if (cursor.fetchone() or [0])[0] == 0:
#                        XmlReader(file, callback).run()
#                        connection.commit()
                    XmlReader(file, callback).run()
                    connection.commit()
                finally:
                    file.close()
        finally:
            zipfile.close()
        print '\nDONE'

    def daily_db_update(self, **options):
        try:
            ftp_host = settings.MUZE_FTP['host']
            ftp_username = settings.MUZE_FTP['username']
            ftp_password = settings.MUZE_FTP['password']
            print 'Connecting to ftp://%s@%s' % (ftp_username, ftp_host)
            ftp = FTP(ftp_host)
            ftp.login(ftp_username, ftp_password)

            fd, fname = tempfile.mkstemp()

            m = md5()

            def callback(b):
                m.update(b)
                os.write(fd, b)

            ftp.retrbinary('RETR /muzegames2/illustrated/xml/inc/inc_illustrated_latest_xml.zip', callback)

            # calc fname's checksum
            checksum = m.hexdigest()

            if MuzeUpdateLog.objects.filter(checksum=checksum).count() > 0:
                debug('Already up to date')
                os.close(fd)
                return

            self.do_update_db(fname, True)

            MuzeUpdateLog(status=MuzeUpdate.Successful,
                          checksum=checksum,
                          filename='/muzegames2/illustrated/xml/inc/inc_illustrated_latest_xml.zip').save()

            os.close(fd)
        except Exception, e:
            MuzeUpdateLog(status=MuzeUpdate.Fail,
                          checksum=checksum,
                          filename='/muzegames2/illustrated/xml/inc/inc_illustrated_latest_xml.zip',
                          message=str(e)).save()
