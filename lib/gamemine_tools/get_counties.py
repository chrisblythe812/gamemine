import urllib2
import re

from simplejson import dumps

#http://www.his.com/~wfeidt/Misc/usc_ind.html

URL_BASE = 'http://www.his.com/~wfeidt/Misc/'
URL_START = 'usc_ind.html'

def run():
    results = {}
    states = {}
    
    urls = []

    res = urllib2.urlopen(URL_BASE + URL_START).read()
    ss = re.findall(r'<li>\s+<a href="(usc_.*?\.html)#.*?>(.*?)</a> [{(](.*?)[})]', res)
    for s in ss:
        urls.append(s[0])
        states[s[1]] = s[2]
    
    for url in set(urls):
        res = urllib2.urlopen(URL_BASE + url).read()
        mm = re.findall(r'<li>.*?>([ a-z]+)<.*?<ul>(.*?)</ul>', res, re.I | re.S)
        for m in mm:
            counties = re.findall('<li>\s*(.*?)\s*</li>\s*', m[1])
            counties = map(lambda x: re.sub(r'\sCounty', '', x), counties)
            counties = map(lambda x: re.sub(r'<.*?>', '', x), counties)
            results[states[m[0]]] = {
                'name': m[0],
                'counties': counties,
            }
    results['NV']['counties'].append('Carson City')
    res = []
    i = 1
    for k, v in results.items():
        for name in v['counties']:
            res.append({
                'fields': {
                    'state': k,
                    'name': name, 
                },
                'model': 'taxes.county',
                'pk': i,
            })
            i += 1
    res = dumps(res, indent=2)
    print res
    

if __name__ == '__main__':
    run()
