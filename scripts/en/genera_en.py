"""Build the English site under <public>/en/ from the Italian pages and en.json.
Also adds hreflang alternates, og:locale:alternate and an IT/EN switch to the Italian pages.
Run last, after pagina_progetti.py and consenso_cookie.py:  python3 genera_en.py <public>
Re-runnable. Strings missing from en.json stay Italian and are listed at the end:
run estrai.py again, translate the new keys in en.json, rerun.
Afterwards run  python3 scripts/aggiungi_widget.py public/en/index.html  (English widget)."""
import sys, os, re, json
from bs4 import BeautifulSoup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estrai import units, ATTR, META, LDKEYS

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = sys.argv[1]
SITE = 'https://vitosemeraro.com'
EN = json.load(open(os.path.join(HERE, 'en.json'), encoding='utf-8'))

PATHS = {
    '/': '/en/',
    '/progetti/': '/en/projects/',
    '/intelligenza-artificiale-per-aziende/': '/en/ai-method/',
    '/workshop-formazione-intelligenza-artificiale/': '/en/learning-ai-at-work/',
    '/chi-sono/': '/en/about/',
    '/privacy/': '/en/privacy/',
    '/diario/sito-con-claude-code/': '/en/journal/building-my-site-with-claude-code/',
    '/diario/claude-code-cos-e/': '/en/journal/what-is-claude-code/',
}
SLUGS = {'framework-progetti-ai': 'ai-project-frameworks'}
for d in sorted(os.listdir(os.path.join(PUB, 'progetti'))):
    if os.path.isfile(os.path.join(PUB, 'progetti', d, 'index.html')):
        PATHS['/progetti/%s/' % d] = '/en/projects/%s/' % SLUGS.get(d, d)
# only pages that exist (e.g. the live repo has no /progetti/ index); /lab/ and 404 stay Italian-only
PATHS = {k: v for k, v in PATHS.items()
         if os.path.isfile(os.path.join(PUB, k.strip('/'), 'index.html') if k != '/' else os.path.join(PUB, 'index.html'))}

def map_path(h):
    """Italian internal href -> English one; anything else unchanged."""
    path, sep, frag = h.partition('#')
    if path == '' and sep:
        return h
    return PATHS.get(path, path) + sep + frag if path in PATHS else h

def map_url(u):
    if u.startswith(SITE + '/'):
        return SITE + map_path(u[len(SITE):])
    return map_path(u) if u.startswith('/') else u

def file_of(path):
    return os.path.join(PUB, path.strip('/'), 'index.html') if path != '/' else os.path.join(PUB, 'index.html')

# text nodes that sit outside any unit (e.g. the card link inside a.proj)
TEXT = {
    'Approfondisci': 'Read more',
    # the prompt shown in /diario/sito-con-claude-code/ (a <pre>, not a unit)
    'Leggi CLAUDE.md e le pagine esistenti in questa cartella.\nVoglio aggiungere: [cosa, per chi, perché].\nVincoli: stesso stile e stessa struttura delle altre pagine, nessuna libreria esterna nuova, testi in italiano.\nPrima proponimi il piano in 5 righe e aspetta il mio ok.\nPoi modifica i file e dimmi quali hai toccato e come verificarli nel browser.':
    'Read CLAUDE.md and the existing pages in this folder.\nI want to add: [what, for whom, why].\nConstraints: same style and structure as the other pages, no new external libraries, copy in Italian.\nFirst propose the plan in 5 lines and wait for my OK.\nThen edit the files and tell me which ones you touched and how to check them in the browser.',
}
# strings inside inline JS (the Chiedi a Vito widget) until scripts/aggiungi_widget.py writes English ones
JS = {
    'Sto cercando nei testi del sito…': 'Searching the text on this site…',
    'Ora non riesco a rispondere. Puoi scrivere a vsemeraro@gmail.com.': 'I can’t answer right now. You can write to vsemeraro@gmail.com.',
}

missing = {}
def tr(s):
    k = s.strip()
    if k in EN and EN[k]:
        return EN[k]
    missing[k] = 1
    return s

def ld(o, keep_url=False):
    if isinstance(o, dict):
        keep = o.get('@type') in ('Person', 'WebSite')
        for k, v in list(o.items()):
            if isinstance(v, str):
                if k in LDKEYS and re.search('[A-Za-zà-ù]{2}', v):
                    o[k] = tr(v)
                elif k == 'inLanguage' and v == 'it-IT':
                    o[k] = 'en'
                elif k in ('url', '@id') and not keep and not re.search(r'/#(vito|website)$', v):
                    o[k] = map_url(v)
            else:
                ld(v)
    elif isinstance(o, list):
        for v in o:
            ld(v)

def alternates(it_path):
    en_path = PATHS[it_path]
    return ('<link rel="alternate" hreflang="it" href="%s%s">\n<link rel="alternate" hreflang="en" href="%s%s">\n'
            '<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, it_path, SITE, en_path, SITE, it_path))

LNG_CSS = '<style id="lng-css">.bar nav a{white-space:nowrap}.bar nav a.lng{display:inline!important;padding-left:20px;border-left:1px solid var(--rule,#9FB3AD)}@media (max-width:1320px){.bar nav{gap:20px}}@media (max-width:1180px){.bar-r{display:none}}</style>'

def switch(href, code, name):
    return '<a class="lng" href="%s" hreflang="%s" lang="%s" title="%s">%s</a>' % (href, code, code, name, code.upper())

def clean_it(s):
    """Remove what patch_it adds, so the page matches the keys in en.json again."""
    s = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?', '', s)
    s = re.sub(r'<meta property="og:locale:alternate" content="[^"]*">\n?', '', s)
    s = re.sub(r'<style id="lng-css">.*?</style>\n?', '', s)
    s = re.sub(r'\s*<a class="lng"[^>]*>[A-Z]{2}</a>', '', s)
    return s

def patch_it(s, it_path):
    """Italian page: hreflang, og:locale:alternate, switch to English. Text-level edits only."""
    s = re.sub(r'(<link rel="canonical" href="[^"]*">)', lambda m: m.group(1) + '\n' + alternates(it_path), s, count=1)
    s = s.replace('<meta property="og:locale" content="it_IT">', '<meta property="og:locale" content="it_IT">\n<meta property="og:locale:alternate" content="en_GB">', 1)
    s = s.replace('</head>', LNG_CSS + '\n</head>', 1)
    s = re.sub(r'(<nav aria-label="Principale">.*?)(\s*</nav>)', lambda m: m.group(1) + '\n      ' + switch(PATHS[it_path], 'en', 'English') + m.group(2), s, count=1, flags=re.S)
    return s

def build_en(src, it_path):
    soup = BeautifulSoup(src, 'html.parser')
    for t in list(units(soup)):
        inner = t.decode_contents().strip()
        if not re.search('[A-Za-zà-ù]{2}', re.sub('<[^>]+>', '', inner)):
            continue
        new = tr(inner)
        if new != inner:
            t.clear()
            for n in list(BeautifulSoup(new, 'html.parser').contents):
                t.append(n)
    for t in list(soup.find_all(string=True)):
        if t.strip() in TEXT and t.parent.name not in ('script', 'style'):
            t.replace_with(t.replace(t.strip(), TEXT[t.strip()]))
    for t in soup.find_all(True):
        if t.find_parent(['script', 'style']):
            continue
        for a in ATTR:
            if t.get(a) and re.search('[A-Za-zà-ù]{2}', t[a]):
                t[a] = tr(t[a])
        if t.name == 'meta' and t.get('content') and any(t.get(k) == v for k, v in META):
            t['content'] = tr(t['content'])
        if t.name in ('a', 'link') and t.get('href') and not (t.name == 'link' and t.get('rel') == ['alternate']):
            t['href'] = map_url(t['href'])
        if t.name == 'meta' and t.get('property') == 'og:url':
            t['content'] = map_url(t['content'])
    for sc in soup.find_all('script', type='application/ld+json'):
        o = json.loads(sc.string)
        ld(o)
        sc.string = json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    out = str(soup)
    out = out.replace('<html lang="it">', '<html lang="en">', 1)
    out = out.replace('<meta content="it_IT" property="og:locale"/>', '<meta content="en_GB" property="og:locale"/>\n<meta content="it_IT" property="og:locale:alternate"/>', 1)
    out = re.sub(r'(<link href="[^"]*" rel="canonical"/>)', lambda m: m.group(1) + '\n' + alternates(it_path), out, count=1)
    out = re.sub(r'(<nav aria-label="Main">.*?)(\s*</nav>)', lambda m: m.group(1) + '\n' + switch(it_path, 'it', 'Italiano') + m.group(2), out, count=1, flags=re.S)
    out = out.replace('</head>', LNG_CSS + '\n</head>', 1)
    for a, b in JS.items():
        out = out.replace(a, b)
    # analytics: project clicks also on /en/projects/<slug>/
    out = out.replace(r"/\/progetti\/[^/]+\/?$/.test(a.pathname)", r"/\/(progetti|projects)\/[^/]+\/?$/.test(a.pathname)")
    out = out.replace("project: a.pathname.split('/')[2]", "project: a.pathname.split('/').filter(Boolean).pop()")
    return out

if __name__ == '__main__':
    for it_path, en_path in PATHS.items():
        f = file_of(it_path)
        it = clean_it(open(f, encoding='utf-8').read())
        en = build_en(it, it_path)
        open(f, 'w', encoding='utf-8').write(patch_it(it, it_path))
        g = file_of(en_path)
        os.makedirs(os.path.dirname(g), exist_ok=True)
        open(g, 'w', encoding='utf-8').write(en)
        print(it_path, '->', en_path)
    # sitemap
    sp = os.path.join(PUB, 'sitemap.xml')
    sm = open(sp, encoding='utf-8').read()
    sm = re.sub(r'\s*<url><loc>%s/en/[^<]*</loc>.*?</url>' % re.escape(SITE), '', sm)
    add = ''.join('\n  <url><loc>%s%s</loc><lastmod>2026-11-12</lastmod></url>' % (SITE, p)
                  for p in PATHS.values() if p != '/en/privacy/')
    sm = sm.replace('\n</urlset>', add + '\n</urlset>', 1)
    open(sp, 'w', encoding='utf-8').write(sm)
    if missing:
        print('UNTRANSLATED (%d):' % len(missing))
        for k in missing:
            print('  ', k[:100])
