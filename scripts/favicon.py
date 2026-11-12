"""Favicon "VS": white Inter Bold letters on the site's dark green ink (#123F37).
Writes favicon.svg, favicon.ico, apple-touch-icon.png, icon-192.png, icon-512.png into <public>
and replaces the old inline data: icon in every page.  python3 favicon.py <public>"""
import sys, os, re, glob
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageDraw, ImageFont

PUB = sys.argv[1]
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
INK, WHITE = '#123F37', '#FFFFFF'

f = TTFont(FONT); gs = f.getGlyphSet(); cmap = f.getBestCmap()
upm = f['head'].unitsPerEm
paths, x, track = [], 0, -40
for ch in 'VS':
    g = gs[cmap[ord(ch)]]
    pen = SVGPathPen(gs); g.draw(pen)
    paths.append((x, pen.getCommands())); x += g.width + track
bp = BoundsPen(gs)
for ch in 'VS': pass
# bounds of the whole word
xmin, ymin, xmax, ymax = 1e9, 1e9, -1e9, -1e9
xx = 0
for ch in 'VS':
    b = BoundsPen(gs); gs[cmap[ord(ch)]].draw(b)
    x0, y0, x1, y1 = b.bounds
    xmin, ymin, xmax, ymax = min(xmin, xx + x0), min(ymin, y0), max(xmax, xx + x1), max(ymax, y1)
    xx += gs[cmap[ord(ch)]].width + track
w, h = xmax - xmin, ymax - ymin
S = 32; box = 24.0                     # letters fill 24 of 32 units wide
k = box / w
tx = (S - w * k) / 2 - xmin * k
ty = (S + h * k) / 2 + ymin * k         # flip y: font y-up
body = ''.join('<path transform="translate(%.3f %.3f) scale(%.5f %.5f)" d="%s"/>' % (tx + px * k, ty, k, -k, d) for px, d in paths)
svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
       '<rect width="32" height="32" rx="6" fill="%s"/><g fill="%s">%s</g></svg>' % (INK, WHITE, body))
open(os.path.join(PUB, 'favicon.svg'), 'w').write(svg)

def png(size, radius=True):
    big = size * 8
    im = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if radius: d.rounded_rectangle((0, 0, big - 1, big - 1), radius=big * 6 // 32, fill=INK)
    else: d.rectangle((0, 0, big, big), fill=INK)
    fnt = ImageFont.truetype(FONT, 10)
    # size the text to the same 22/32 width
    lo, hi = 10, big
    while hi - lo > 1:
        m = (lo + hi) // 2
        bb = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), 'VS', font=ImageFont.truetype(FONT, m))
        (lo, hi) = (m, hi) if bb[2] - bb[0] <= big * 24 / 32 else (lo, m)
    fnt = ImageFont.truetype(FONT, lo)
    bb = d.textbbox((0, 0), 'VS', font=fnt)
    d.text(((big - (bb[2] - bb[0])) / 2 - bb[0], (big - (bb[3] - bb[1])) / 2 - bb[1]), 'VS', font=fnt, fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)

png(180, radius=False).convert('RGB').save(os.path.join(PUB, 'apple-touch-icon.png'))
png(192).save(os.path.join(PUB, 'icon-192.png'))
png(512).save(os.path.join(PUB, 'icon-512.png'))
png(48).save(os.path.join(PUB, 'favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)])

TAGS = ('<link rel="icon" href="/favicon.ico" sizes="32x32">\n'
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
n = 0
for p in glob.glob(os.path.join(PUB, '**', '*.html'), recursive=True):
    s = open(p, encoding='utf-8').read()
    t = re.sub(r'<link rel="icon"[^>]*>\n?|<link [^>]*rel="icon"[^>]*/?>\n?|<link rel="apple-touch-icon"[^>]*>\n?|<link [^>]*rel="apple-touch-icon"[^>]*/?>\n?', '', s)
    t = t.replace('</head>', TAGS + '\n</head>', 1)
    if t != s:
        open(p, 'w', encoding='utf-8').write(t); n += 1
print('pages', n)
