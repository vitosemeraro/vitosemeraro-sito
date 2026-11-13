# Uso: python3 scripts/genera_diario.py public
# Gira da solo nella GitHub Action prima del deploy (prima di genera_llms.py). Si può rilanciare.
# Legge gli articoli in public/diario/<slug>/index.html (salta i noindex e quelli con data futura) e aggiorna:
#  - l'elenco e il JSON-LD di public/diario/index.html, tra i segnaposto <!--diario:lista--> e <!--diario:ld-->
#  - gli ultimi 3 articoli nella home, tra <!--diario:home--> e <!--/diario:home-->
#  - il breadcrumb di ogni articolo, che porta a /diario/
#  - la voce "Diario" nel menu delle pagine italiane
#  - public/sitemap.xml (aggiunge /diario/ e gli articoli che mancano)
# Così per pubblicare un articolo basta aggiungere la sua cartella in public/diario/.
import re, os, sys, glob, json, html, datetime

PUB = sys.argv[1]
DOMAIN = 'https://vitosemeraro.com'
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
        'settembre', 'ottobre', 'novembre', 'dicembre']
today = datetime.date.today().isoformat()


def rd(p):
    return open(p, encoding='utf-8').read()


def wr(p, s):
    open(p, 'w', encoding='utf-8').write(s)


def txt(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def data_it(d):
    y, m, g = d.split('-')
    return f'{int(g)} {MESI[int(m) - 1]} {y}'


arts = []
for p in glob.glob('diario/*/index.html', root_dir=PUB):
    h = rd(os.path.join(PUB, p))
    if re.search(r'<meta name="robots" content="[^"]*noindex', h):
        continue
    slug = p.split('/')[1]
    d = re.search(r'article:published_time" content="(\d{4}-\d\d-\d\d)', h)
    d = d.group(1) if d else today
    if d > today:
        continue
    m = re.search(r'<h1>(?:<span class="h1-r">.*?</span>)?(.*?)</h1>', h, re.S)
    title = txt(m.group(1)) if m else txt(re.search(r'<title>(.*?)</title>', h, re.S).group(1))
    desc = re.search(r'<meta name="description" content="([^"]*)"', h)
    arts.append({'slug': slug, 'url': f'/diario/{slug}/', 'date': d, 'title': title,
                 'desc': html.unescape(desc.group(1)) if desc else ''})
    # breadcrumb dell'articolo: link all'indice
    h2 = h.replace('<a href="/">Vito Semeraro</a> / Diario da PM builder</nav>',
                   '<a href="/">Vito Semeraro</a> / <a href="/diario/">Diario da PM builder</a></nav>')
    if '"item": "https://vitosemeraro.com/diario/"' not in h2:
        h2 = re.sub(r'("@type": "BreadcrumbList", "itemListElement": \[\{"@type": "ListItem", "position": 1, [^}]*\}, )\{"@type": "ListItem", "position": 2, ',
                    r'\1{"@type": "ListItem", "position": 2, "name": "Diario da PM builder", "item": "https://vitosemeraro.com/diario/"}, {"@type": "ListItem", "position": 3, ', h2)
    if h2 != h:
        wr(os.path.join(PUB, p), h2)

arts.sort(key=lambda a: (a['date'], a['slug']), reverse=True)
E = html.escape


def li(a):
    return (f'      <li class="rv"><a href="{a["url"]}"><span class="b-c"><time datetime="{a["date"]}">{data_it(a["date"])}</time></span>'
            f'<span class="b-t">{E(a["title"], quote=False)}</span><span class="b-d">{E(a["desc"], quote=False)}</span></a></li>\n')


def put(s, tag, body):
    a, b = f'<!--{tag}-->', f'<!--/{tag}-->'
    if a not in s:
        raise SystemExit(f'segnaposto {a} mancante')
    return re.sub(re.escape(a) + r'.*?' + re.escape(b), lambda _: a + body + b, s, flags=re.S)


# indice /diario/
ip = os.path.join(PUB, 'diario/index.html')
s = rd(ip)
s = put(s, 'diario:lista', '\n' + ''.join(li(a) for a in arts) + '    ')
ld = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'Blog', '@id': DOMAIN + '/diario/#blog', 'name': 'Diario da PM builder', 'url': DOMAIN + '/diario/',
     'inLanguage': 'it-IT', 'author': {'@id': DOMAIN + '/#vito'}, 'publisher': {'@id': DOMAIN + '/#vito'},
     'description': re.search(r'<meta name="description" content="([^"]*)"', s).group(1),
     'blogPost': [{'@type': 'BlogPosting', 'headline': a['title'], 'url': DOMAIN + a['url'], 'datePublished': a['date']} for a in arts]},
    {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Vito Semeraro', 'item': DOMAIN + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Diario da PM builder', 'item': DOMAIN + '/diario/'}]},
    {'@type': 'Person', '@id': DOMAIN + '/#vito', 'name': 'Vito Semeraro', 'url': DOMAIN + '/', 'jobTitle': 'AI Product Manager'}]}
s = put(s, 'diario:ld', '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>')
n = len(arts)
s = put(s, 'diario:n', f'{n} articol{"o" if n == 1 else "i"}' + (f' · ultimo il {data_it(arts[0]["date"])}' if arts else ''))
wr(ip, s)

# home: ultimi 3
hp = os.path.join(PUB, 'index.html')
s = rd(hp)
if '<!--diario:home-->' in s:
    s = put(s, 'diario:home', '\n' + ''.join(li(a) for a in arts[:3]) + '    ')
    wr(hp, s)

# menu "Diario" nelle pagine italiane (dopo "Progetti")
for p in glob.glob('**/index.html', root_dir=PUB, recursive=True):
    if p.startswith(('en/', 'lab/')):
        continue
    f = os.path.join(PUB, p)
    h = rd(f)
    if 'aria-label="Principale"' not in h or '>Diario</a>' in h:
        continue
    h2 = re.sub(r'(<nav aria-label="Principale">.*?<a href="(?:/)?#progetti"[^>]*>Progetti</a>\n)', r'\1      <a href="/diario/">Diario</a>\n', h, count=1, flags=re.S)
    if h2 != h:
        wr(f, h2)

# sitemap
sp = os.path.join(PUB, 'sitemap.xml')
s = rd(sp)
add = []
last = arts[0]['date'] if arts else today
if f'<loc>{DOMAIN}/diario/</loc>' in s:
    s = re.sub(rf'(<loc>{re.escape(DOMAIN)}/diario/</loc><lastmod>)[^<]*', rf'\g<1>{last}', s)
else:
    add.append(f'  <url><loc>{DOMAIN}/diario/</loc><lastmod>{last}</lastmod></url>\n')
for a in arts:
    if f'<loc>{DOMAIN}{a["url"]}</loc>' not in s:
        add.append(f'  <url><loc>{DOMAIN}{a["url"]}</loc><lastmod>{a["date"]}</lastmod></url>\n')
if add:
    s = s.replace('</urlset>', ''.join(add) + '</urlset>')
wr(sp, s)
print('diario: articoli', n, '| sitemap +', len(add))
