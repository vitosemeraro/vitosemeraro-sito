"""Collect the Italian strings of the built site to translate: innermost text blocks (inner HTML),
attributes, meta tags and JSON-LD text. Output: JSON {italian: ""}."""
import sys, os, json, glob, re
from bs4 import BeautifulSoup
TB = {'p','li','h1','h2','h3','h4','h5','dt','dd','figcaption','summary','label','title','td','th'}
IN = {'a','span','b','nav','strong','em','button'}
ATTR = ('alt','aria-label','placeholder')
META = {('name','description'),('name','twitter:title'),('name','twitter:description'),('property','og:title'),('property','og:description'),('property','og:site_name')}
LDKEYS = {'name','description','text','headline','jobTitle','alternateName','about'}

def has_text(h):
    return re.search('[A-Za-zà-ù]{2}', re.sub('<[^>]+>', '', h))

def units(s):
    """Yield the tags whose inner HTML is one translation unit."""
    for t in s.find_all(True):
        if t.find_parent(['script','style']) or t.name in ('script','style'): continue
        if t.name in TB:
            if not t.find(list(TB)): yield t
        elif t.name in IN:
            if t.find_parent(list(IN)) or t.find(list(TB)): continue
            up = t.find_parent(list(TB))
            if up is not None and not up.find(list(TB)): continue
            yield t

def ld_strings(o, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in LDKEYS and isinstance(v, str) and has_text(v): out.append(v)
            else: ld_strings(v, out)
    elif isinstance(o, list):
        for v in o: ld_strings(v, out)

if __name__ == '__main__':
    PUB, OUT = sys.argv[1], sys.argv[2]
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    seen = {}
    for f in sorted(glob.glob(os.path.join(PUB, '**', '*.html'), recursive=True)):
        if os.sep + 'en' + os.sep in f: continue
        s = BeautifulSoup(open(f, encoding='utf-8').read(), 'html.parser')
        for t in s.find_all(True):
            if t.find_parent(['script','style']): continue
            for a in ATTR:
                if t.get(a) and has_text(t[a]): seen[t[a]] = 1
            if t.name == 'meta' and t.get('content') and any(t.get(k) == v for k, v in META): seen[t['content']] = 1
        for t in units(s):
            inner = t.decode_contents().strip()
            if has_text(inner): seen[inner] = 1
        for sc in s.find_all('script', type='application/ld+json'):
            out = []; ld_strings(json.loads(sc.string), out)
            for v in out: seen[v] = 1
    json.dump({k: old.get(k, '') for k in seen}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(seen), 'strings,', sum(1 for k in seen if not old.get(k)), 'untranslated')
