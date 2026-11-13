# Uso: python3 scripts/genera_diario.py public
# Gira da solo nella GitHub Action prima del deploy (prima di genera_llms.py). Si può rilanciare.
# Per l'italiano (public/diario/) e l'inglese (public/en/journal/) legge gli articoli <cartella>/<slug>/index.html
# (salta i noindex e quelli con data futura) e aggiorna:
#  - l'elenco e il JSON-LD della pagina indice, tra i segnaposto <!--diario:lista-->, <!--diario:ld-->, <!--diario:n-->
#  - gli ultimi 3 articoli nella home della lingua, tra <!--diario:home--> e <!--/diario:home--> (se c'è)
#  - il breadcrumb di ogni articolo (link all'indice e BreadcrumbList Home > Indice > Articolo)
#  - la voce "Diario" / "Journal" nel menu delle pagine della lingua
#  - public/sitemap.xml (aggiunge gli indici e gli articoli che mancano)
# Così per pubblicare un articolo basta aggiungere la sua cartella.
import re, os, sys, glob, json, html, datetime

PUB = sys.argv[1]
DOMAIN = 'https://vitosemeraro.com'
today = datetime.date.today().isoformat()

LANGS = [
    {'dir': 'diario', 'home': '/', 'name': 'Diario da PM builder', 'nav': 'Diario',
     'months': ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
                'settembre', 'ottobre', 'novembre', 'dicembre'],
     'one': 'articolo', 'many': 'articoli', 'last': 'ultimo il', 'lang': 'it-IT',
     'pages': lambda p: not p.startswith(('en/', 'lab/'))},
    {'dir': 'en/journal', 'home': '/en/', 'name': 'A PM builder’s journal', 'nav': 'Journal',
     'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                'September', 'October', 'November', 'December'],
     'one': 'article', 'many': 'articles', 'last': 'latest on', 'lang': 'en-GB',
     'pages': lambda p: p.startswith('en/')},
]


def rd(p):
    return open(p, encoding='utf-8').read()


def wr(p, s):
    open(p, 'w', encoding='utf-8').write(s)


def txt(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def meta(h, key):
    # attributes in either order (the English pages are written by BeautifulSoup: content first)
    m = re.search(r'<meta (?:name|property)="%s" content="([^"]*)"' % key, h) or \
        re.search(r'<meta content="([^"]*)" (?:name|property)="%s"' % key, h)
    return html.unescape(m.group(1)) if m else None


def put(s, tag, body):
    a, b = f'<!--{tag}-->', f'<!--/{tag}-->'
    if a not in s:
        raise SystemExit(f'segnaposto {a} mancante')
    return re.sub(re.escape(a) + r'.*?' + re.escape(b), lambda _: a + body + b, s, flags=re.S)


def fix_breadcrumb_ld(h, L, url, title):
    def rep(m):
        raw = m.group(1)
        try:
            ld = json.loads(raw)
        except ValueError:
            return m.group(0)
        changed = False
        for node in ld.get('@graph', [ld]):
            if node.get('@type') == 'BreadcrumbList':
                want = [{'@type': 'ListItem', 'position': 1, 'name': 'Vito Semeraro', 'item': DOMAIN + L['home']},
                        {'@type': 'ListItem', 'position': 2, 'name': L['name'], 'item': f'{DOMAIN}/{L["dir"]}/'},
                        {'@type': 'ListItem', 'position': 3, 'name': title, 'item': DOMAIN + url}]
                old = node.get('itemListElement', [])
                if len(old) >= 2 and old[-1].get('name'):
                    want[2]['name'] = old[-1]['name']
                if old != want:
                    node['itemListElement'] = want
                    changed = True
        if not changed:
            return m.group(0)
        compact = '":"' in raw
        out = json.dumps(ld, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': '))
        return '<script type="application/ld+json">' + out + '</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', rep, h, count=1, flags=re.S)


sitemap_add = []
sp = os.path.join(PUB, 'sitemap.xml')
sm = rd(sp)

for L in LANGS:
    ip = os.path.join(PUB, L['dir'], 'index.html')
    if not os.path.exists(ip):
        continue
    D = L['dir']

    def fmt(d):
        y, m, g = d.split('-')
        return f'{int(g)} {L["months"][int(m) - 1]} {y}'

    arts = []
    for p in glob.glob(f'{D}/*/index.html', root_dir=PUB):
        f = os.path.join(PUB, p)
        h = rd(f)
        if re.search(r'name="robots"[^>]*noindex|noindex[^>]*name="robots"', h):
            continue
        slug = p.split('/')[-2]
        url = f'/{D}/{slug}/'
        d = meta(h, 'article:published_time') or today
        d = d[:10]
        if d > today:
            continue
        m = re.search(r'<h1>(?:<span class="h1-r">.*?</span>)?(.*?)</h1>', h, re.S)
        title = txt(m.group(1)) if m else txt(re.search(r'<title>(.*?)</title>', h, re.S).group(1))
        arts.append({'url': url, 'date': d, 'title': title, 'desc': meta(h, 'description') or ''})
        # breadcrumb visibile e JSON-LD
        home_a = f'<a href="{L["home"]}">Vito Semeraro</a> / '
        h2 = h.replace(home_a + L['name'] + '</nav>', home_a + f'<a href="/{D}/">{L["name"]}</a></nav>')
        h2 = fix_breadcrumb_ld(h2, L, url, title)
        if h2 != h:
            wr(f, h2)

    arts.sort(key=lambda a: (a['date'], a['url']), reverse=True)
    E = html.escape

    def li(a):
        return (f'      <li class="rv"><a href="{a["url"]}"><span class="b-c"><time datetime="{a["date"]}">{fmt(a["date"])}</time></span>'
                f'<span class="b-t">{E(a["title"], quote=False)}</span><span class="b-d">{E(a["desc"], quote=False)}</span></a></li>\n')

    s = rd(ip)
    s = put(s, 'diario:lista', '\n' + ''.join(li(a) for a in arts) + '    ')
    idx_url = f'{DOMAIN}/{D}/'
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Blog', '@id': idx_url + '#blog', 'name': L['name'], 'url': idx_url, 'inLanguage': L['lang'],
         'author': {'@id': DOMAIN + '/#vito'}, 'publisher': {'@id': DOMAIN + '/#vito'},
         'description': meta(s, 'description'),
         'blogPost': [{'@type': 'BlogPosting', 'headline': a['title'], 'url': DOMAIN + a['url'], 'datePublished': a['date']} for a in arts]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Vito Semeraro', 'item': DOMAIN + L['home']},
            {'@type': 'ListItem', 'position': 2, 'name': L['name'], 'item': idx_url}]},
        {'@type': 'Person', '@id': DOMAIN + '/#vito', 'name': 'Vito Semeraro', 'url': DOMAIN + '/', 'jobTitle': 'AI Product Manager'}]}
    s = put(s, 'diario:ld', '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>')
    n = len(arts)
    s = put(s, 'diario:n', f'{n} {L["one"] if n == 1 else L["many"]}' + (f' · {L["last"]} {fmt(arts[0]["date"])}' if arts else ''))
    wr(ip, s)

    # home della lingua: ultimi 3
    hp = os.path.join(PUB, L['home'].strip('/'), 'index.html')
    s = rd(hp)
    if '<!--diario:home-->' in s:
        wr(hp, put(s, 'diario:home', '\n' + ''.join(li(a) for a in arts[:3]) + '    '))

    # voce nel menu, dopo "Progetti" / "Projects"
    for p in glob.glob('**/index.html', root_dir=PUB, recursive=True):
        if not L['pages'](p):
            continue
        f = os.path.join(PUB, p)
        h = rd(f)
        if f'>{L["nav"]}</a>' in h:
            continue
        h2 = re.sub(r'(<nav aria-label="(?:Principale|Main)">.*?<a [^>]*href="(?:/en/|/)?#progetti"[^>]*>(?:Progetti|Projects)</a>\n)',
                    lambda m: m.group(1) + f'<a href="/{D}/">{L["nav"]}</a>\n', h, count=1, flags=re.S)
        if h2 != h:
            wr(f, h2)

    # sitemap
    last = arts[0]['date'] if arts else today
    if f'<loc>{idx_url}</loc>' in sm:
        sm = re.sub(rf'(<loc>{re.escape(idx_url)}</loc><lastmod>)[^<]*', rf'\g<1>{last}', sm)
    else:
        sitemap_add.append(f'  <url><loc>{idx_url}</loc><lastmod>{last}</lastmod></url>\n')
    for a in arts:
        if f'<loc>{DOMAIN}{a["url"]}</loc>' not in sm:
            sitemap_add.append(f'  <url><loc>{DOMAIN}{a["url"]}</loc><lastmod>{a["date"]}</lastmod></url>\n')
    print(f'{D}: articoli {n}')

if sitemap_add:
    sm = sm.replace('</urlset>', ''.join(sitemap_add) + '</urlset>')
wr(sp, sm)
print('sitemap +', len(sitemap_add))
