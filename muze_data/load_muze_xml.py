import sys
from datetime import datetime
from xml import sax
#import pymongo
import psycopg2

class Handler(sax.handler.ContentHandler):
    def __init__(self, callback):
        self.level = -1
        self.collection = None
        self.document = None
        self.item_name = None
        self.data = []
        self.callback = callback
        
    def __unicode__(self):
        return 'level: %d, collection: %s, document: %s, item_name: %s, data: %s' % (
            self.level,
            self.collection,
            self.document,
            self.item_name,
            self.data
        )
        
    def startElement(self, name, attrs):
        self.level += 1
        if name == 'gamemine_muze':
            return # top level element. skip it.
        if self.level == 1:
            self.collection = name
            self.document = {}
        elif self.level == 2:
            self.item_name = name
            self.data = [] 
        else:
            raise Exception('Unsupported level!')
        
    def characters(self, data):
        self.data.append(data)
        
    def endElement(self, name):
        if self.level == 2:
            self.document[self.item_name] = ''.join(self.data)
        elif self.level == 1:
            self.callback(self.collection, self.document)
        self.level -= 1


def translate_date(sdate):
    try:
        return datetime.strptime(sdate, '%Y-%m-%d')
    except ValueError:
        return None

document_translation_table = {
    'Association': {
        'Weight': float,
    },
    'Attribute': {
        'n_Links': int,          
        'n_Objects': int,
        'n_Values': int,
        'n_Children': int,
        'n_Parents': int,          
    },
    'AttributeAssociation': {
    },
    'AttributeLink': {
        'Weight': float,
        'Rank': float, 
    },
    'Clip': {
        'Width': int,
        'Height': int,
        'FileSize': int,
        'Length': int,
        'SetID': int,
    },
    'ClipLink': {
        'SortOrder': int,
        'PublishDate': translate_date,
        'p_Width': int,
        'p_Height': int,
        'p_FileSize': int,
        'p_Ratio': float,
        'p_Length': int,
        'p_SetID': int,
    },
    'Document': {
    },
    'Image': {
        'Width': int,
        'Height': int,
        'FileSize': int,
    },
    'ImageLink': {
        'SortOrder': int,
        'PublishDate': translate_date,
        'p_Width': int,
        'p_Height': int,
        'p_FileSize': int,
        'p_Ratio': float,
    },
    'Name': {
        'n_Attributes': int,
        'n_Associations': int,
    },
    'Release': {
        'ReleaseDate': translate_date,
        'MSRP': float,
    },
    'Work': {
        'OriginalReleaseDate': translate_date,
        'n_Attributes': int,
        'n_Associations': int,
    },
}


def run(f):
    #db = pymongo.Connection()['muze']
    cache = {'__t0': datetime.now(), }
    
    db = psycopg2.connect(database='gamemine_muze', host='localhost', user='postgres', password='123123')
    cur = db.cursor()
    
    collections_sql_cache = {}
    def get_sql(collection, object):
        if collection not in collections_sql_cache:
            collections_sql_cache[collection] = 'INSERT INTO %s(%s) VALUES(%s);' % (
                collection,
                ', '.join(object.keys()),
                ', '.join(['%s' % x for x in object.keys()]))
        return collections_sql_cache[collection]
    
    def write_objects(collection, objects):
        for o in objects:
            sql = get_sql(collection, o)
            cur.execute(sql, o.values())
#        print 'Do write %d objects into %s collection' % (len(objects), collection)
#        collection = db[collection]
#        collection.insert(objects)
    
    def put_document(collection, document):
        translator = document_translation_table[collection]
        for k, v in document.items():
            f = translator.get(k, lambda s: s.strip())
            document[k] = f(v)
        objects = cache.get(collection, [])
        objects.append(document)
        if len(objects) >= 1000:
            last_collecton = cache.get('__last_collecton')
            if last_collecton != collection:
                print 'Loading %s...' % collection
                cache['__last_collecton'] = collection
            write_objects(collection, objects)
            objects = []
        cache[collection] = objects
        
        counter = cache.get('__counter', 0) + 1
        if counter % 10000 == 0:
            t = datetime.now() - cache['__t0']
            speed = counter / t.seconds 
#            print '%s: %s' % (collection, document)
            print 'Processed %d documents in %s (speed: %d doc/sec)...' % (counter, t, speed)
        cache['__counter'] = counter
        
    
    handler = Handler(put_document)
    xml_parser = sax.make_parser()
    xml_parser.setContentHandler(handler)
    xml_parser.parse(f)
    
    db.commit()
    cur.close()
    db.close()
    
    for k, v in cache.items():
        if k.startswith('__'):
            continue
        if v:
            write_objects(k, v)
    t = datetime.now() - cache['__t0']
    counter = cache['__counter']
    speed = counter / t.seconds 
    print 'Total Processed: %d documents in %s (speed %d)' % (counter, t, speed)
    

if __name__ == '__main__':
    t1 = datetime.now()
    with open(sys.argv[1]) as f:
        run(f)
    print 'Done in %s.' % (datetime.now() - t1)
