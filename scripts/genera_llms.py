# Uso: python3 genera_llms.py <cartella public>
# Nel repo vitosemeraro-sito gira da solo nella GitHub Action prima del deploy.
# Salta le pagine noindex.
# Scrive <public>/llms.txt (indice per i motori AI) e <public>/llms-full.txt (testo delle pagine IT),
# che è anche la base di conoscenza dell'assistente "Chiedi a Vito" (il Worker la legge dal sito).
# Si può rilanciare. Va lanciato dopo le altre modifiche al sito (dopo genera_en.py e favicon.py).
import re, os, sys, glob
from html.parser import HTMLParser

PUB = sys.argv[1]
DOMAIN = 'https://vitosemeraro.com/'

# Regole contratto: niente datore di lavoro attuale né suoi marchi, niente lista "Ho lavorato per e con".
BANNED = re.compile(r'RCS|Corriere|Gazzetta', re.I)
FIXES = [
    (re.compile(r'Oggi lavoro sui prodotti editoriali di [^,]+, e costruisco'), 'Costruisco'),
    (re.compile(r'Today I work on [^,]+, and I build'), 'I build'),
]
SKIP_LINE = re.compile(r'^(Vito Semeraro|AI Product Manager e PM builder, Milano|Come lavoro|Progetti|Playbook|Talk|Contatti|Diario|EN|IT|Aziende|Workshop|LinkedIn|GitHub|Privacy|PrivacyCookie|Cookie|AccettaRifiuta|Vito Semeraro© 2026|C|\d\d|AI in azienda|Tutti i progetti →)$')


class P(HTMLParser):
    BLOCK = ('p', 'h1', 'h2', 'h3', 'h4', 'li', 'div', 'section', 'br', 'tr', 'dt', 'dd', 'figcaption', 'a', 'article')
    def __init__(s):
        super().__init__(); s.t = []; s.skip = 0
    def handle_starttag(s, tag, a):
        if tag in ('script', 'style', 'svg', 'noscript', 'template', 'form', 'header', 'footer'): s.skip += 1
        if tag in s.BLOCK: s.t.append('\n')
    def handle_endtag(s, tag):
        if tag in ('script', 'style', 'svg', 'noscript', 'template', 'form', 'header', 'footer'): s.skip -= 1
    def handle_data(s, d):
        if not s.skip: s.t.append(d)


def page_text(path):
    h = open(path, encoding='utf-8').read()
    h = re.sub(r'<!--ask-->.*?<!--/ask-->', '', h, flags=re.S)
    h = re.sub(r'<div class="clients.*?</div>', '', h, flags=re.S)  # lista "Ho lavorato per e con"
    h = re.sub(r'<div class="cc".*?</div>\s*</div>', '', h, flags=re.S)  # banner cookie
    title = re.search(r'<title>(.*?)</title>', h, re.S).group(1).strip()
    desc = re.search(r'<meta name="description" content="([^"]*)"', h)
    p = P(); p.feed(h)
    txt = re.sub(r'[ \t\xa0]+', ' ', ''.join(p.t))
    for rx, rep in FIXES: txt = rx.sub(rep, txt)
    lines = []
    for l in txt.split('\n'):
        l = l.strip()
        if not l or SKIP_LINE.match(l) or BANNED.search(l): continue
        if l.startswith('Uso Cloudflare per contare'): break
        lines.append(l)
    return title, (desc.group(1) if desc else ''), '\n'.join(lines)


pages = ['index.html', 'chi-sono/index.html', 'intelligenza-artificiale-per-aziende/index.html',
         'workshop-formazione-intelligenza-artificiale/index.html', 'progetti/index.html']
pages += sorted(p for p in glob.glob('progetti/*/index.html', root_dir=PUB) if p != 'progetti/index.html')
pages += ['diario/index.html'] + sorted(glob.glob('diario/*/index.html', root_dir=PUB))
pages += sorted(glob.glob('lab/*/index.html', root_dir=PUB))

full, idx = [], []
for p in pages:
    if not os.path.exists(os.path.join(PUB, p)): continue
    if re.search(r'<meta name="robots" content="[^"]*noindex', open(os.path.join(PUB, p), encoding='utf-8').read()): continue
    url = DOMAIN + (os.path.dirname(p) + '/' if os.path.dirname(p) else '')
    title, desc, body = page_text(os.path.join(PUB, p))
    title = title.replace(' · Vito Semeraro', '')
    full.append(f'# {title}\nURL: {url}\n\n{body}')
    idx.append((p, title, url, desc))

assert not BANNED.search('\n'.join(full)), 'testo vietato rimasto in llms-full.txt'

def sec(prefix):
    return ''.join(f'- [{t}]({u}): {d}\n' for p, t, u, d in idx if p.startswith(prefix) and p != prefix + 'index.html')

EN = f'''## English
- [Home (English)]({DOMAIN}en/)
- [About]({DOMAIN}en/about/)
- [The method]({DOMAIN}en/ai-method/)
- [Learning AI at work]({DOMAIN}en/learning-ai-at-work/)
- [staged.ai]({DOMAIN}en/projects/staged-ai/)

''' if os.path.exists(os.path.join(PUB, 'en/index.html')) else ''
llms = f'''# Vito Semeraro

> AI Product Manager e PM builder a Milano. Porta l'intelligenza artificiale nei team e nei prodotti: progetta con Claude Design, costruisce con gli agenti AI, misura l'adozione. Certificato PMI-CPMAI.

Sul sito c'è anche "Chiedi a Vito", un assistente AI che risponde solo dai testi di queste pagine. Il testo completo delle pagine è in {DOMAIN}llms-full.txt.

## Pagine
- [Chi sono, progetti e contatti]({DOMAIN}): profilo, metodo, progetti, talk, certificazioni
- [Chi sono, in fatti]({DOMAIN}chi-sono/): ruolo, percorso anno per anno, progetti con ruolo e stato, certificazioni, talk e scritti
- [Intelligenza artificiale per aziende]({DOMAIN}intelligenza-artificiale-per-aziende/): casi d'uso, prototipi con agenti AI, AI Act, adozione misurata
- [Workshop e formazione sull'AI]({DOMAIN}workshop-formazione-intelligenza-artificiale/): formati per PM, team e manager, alfabetizzazione AI Act art. 4
- [Tutti i progetti]({DOMAIN}progetti/)
- [Diario da PM builder]({DOMAIN}diario/): tutti gli articoli su AI, Claude Code e agenti nel lavoro da product manager

## Progetti
{sec('progetti/')}
{EN}## Contatti
- Email: vsemeraro@gmail.com
- LinkedIn: https://www.linkedin.com/in/vsemeraro/
- GitHub: https://github.com/vitosemeraro
'''
if any(p.startswith('diario/') and p != 'diario/index.html' for p, *_ in idx):
    llms += '\n## Diario\n' + sec('diario/')
if any(p.startswith('lab/') for p, *_ in idx):
    llms += '\n## Lab\n' + sec('lab/')
llms = llms.replace('\n\n\n', '\n\n')
open(os.path.join(PUB, 'llms.txt'), 'w', encoding='utf-8').write(llms)
open(os.path.join(PUB, 'llms-full.txt'), 'w', encoding='utf-8').write(
    '# Vito Semeraro, testo completo del sito\n\nFonte: ' + DOMAIN + '. Testo delle pagine in italiano, generato automaticamente.\n\n' + '\n\n'.join(full) + '\n')
print('llms.txt', len(llms), '| llms-full.txt', sum(map(len, full)), '| pagine', len(idx))
