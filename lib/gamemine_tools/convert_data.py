import yaml
import csv
import itertools
from datetime import datetime

TYPES = {
    'int': int,
    'string': str,
    'date': lambda s: datetime.strptime(s, '%Y-%m-%d') if s != '0000-00-00' else None,
    'datetime': lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S') if s != '0000-00-00 00:00:00' else None,
    'int_0': lambda s: int(s) if s != '0' else None,
}


def die(message, *args):
    raise Exception(message % args)


def read_rules(filename):
    with open(filename, 'r') as f:
        return yaml.load(f)


def get_model_rule(rules, model_name):
    for r in rules:
        if r['model'] == model_name:
            return r
    

def run(rules, model_name, input):
    rules = read_rules(rules)
    model_rule = get_model_rule(rules, model_name) or die('Unknown model %s', model_name)
    fields_map = model_rule['fields_map'] or {}
    with open(input, 'r') as f:
        results = []
        for fields in csv.reader(f, delimiter=';', quotechar='"', escapechar='\\'):
            break
        for r in csv.reader(f, delimiter=';', quotechar='"', escapechar='\\'):
            data = dict(itertools.izip(fields, r))
            res = {
                   'model': model_name, 
                   'pk': int(data['id']), 
                   'fields': {}
            }
            for fkey, fvalue in fields_map.items():
                v = data[fvalue['name']]
                v = TYPES[fvalue['type']](v)
                res['fields'][fkey] = v
            results.append(res)
        yaml.dump(results, sys.stdout)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        print >>sys.stderr, 'Usage: convert_data <data_rules.yaml> <appname.modelname> <input_data.csv>'
    try:
        run(*sys.argv[1:])
    except Exception, e:
        print >>sys.stderr, 'ERROR: %s' % e
        raise

    