# Uso: python3 aggiungi_widget.py <public/index.html> [endpoint]
# Inserisce (o sostituisce) il campo "Chiedi a Vito" sotto il ritratto nell'hero della home.
# Si può rilanciare: tutto sta tra i marcatori <!--ask-->...<!--/ask-->, <!--ask:css--> e <!--ask:js-->.
import re, sys

path = sys.argv[1]
EP = sys.argv[2] if len(sys.argv) > 2 else 'https://chiedi-a-vito.cfdist2.workers.dev/chat'
h = open(path, encoding='utf-8').read()
for a, b in (('<!--ask-->', '<!--/ask-->'), ('<!--ask:css-->', '<!--/ask:css-->'), ('<!--ask:js-->', '<!--/ask:js-->')):
    h = re.sub(re.escape(a) + r'.*?' + re.escape(b) + r'\n?', '', h, flags=re.S)

HTML = '''<!--ask--><form class="ask" id="ask" autocomplete="off" aria-label="Chiedi a Vito, assistente AI">
        <label class="lbl" for="ask-q">Chiedi a Vito <span class="ask-ai">assistente AI</span></label>
        <div class="ask-row"><input id="ask-q" name="q" type="text" maxlength="400" placeholder="Cosa vuoi sapere?" enterkeyhint="send"><button type="submit" aria-label="Chiedi">Chiedi <span aria-hidden="true">→</span></button></div>
        <div class="ask-sg" id="ask-sg"><button type="button">Cos’è staged.ai?</button><button type="button">Come lavori con gli agenti AI?</button><button type="button">Che workshop fai?</button></div>
        <div class="ask-out" id="ask-out" aria-live="polite" hidden></div>
        <p class="ask-n">Risponde un’AI usando solo i testi di questo sito. Può sbagliare: per conferme scrivimi.</p>
      </form><!--/ask-->
'''

CSS = '''<!--ask:css--><style>
.ask{margin-top:20px;font:400 16px/1.5 var(--serif)}
.ask .lbl{display:flex;justify-content:space-between;gap:12px;color:var(--ink)}
.ask .ask-ai{color:var(--ink-2)}
.ask-row{display:flex;margin-top:8px;border:1px solid var(--ink);background:var(--paper)}
.ask-row input{flex:1;min-width:0;border:0;background:transparent;color:var(--ink);font:400 17px/1.4 var(--serif);padding:12px 12px}
.ask-row input::placeholder{color:var(--ink-2);opacity:.75}
.ask-row input:focus{outline:none}
.ask-row:focus-within{outline:2px solid var(--red);outline-offset:2px}
.ask-row button{flex:none;border:0;border-left:1px solid var(--ink);background:var(--ink);color:var(--paper);font:500 14px/1 var(--mono);padding:0 16px;cursor:pointer}
.ask-row button:disabled{opacity:.6;cursor:wait}
.ask-sg{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.ask-sg[hidden]{display:none}
.ask-sg button{font:400 13px/1.3 var(--mono);color:var(--ink);background:transparent;border:1px solid var(--rule);padding:6px 9px;cursor:pointer;text-align:left}
.ask-sg button:hover{border-color:var(--ink)}
.ask-out{margin-top:14px;max-height:360px;overflow:auto;border-top:1px solid var(--rule)}
.ask-out[hidden]{display:none}
.ask-m{padding:12px 0;border-bottom:1px solid var(--rule)}
.ask-m .q{font:400 13px/1.5 var(--mono);color:var(--ink-2)}
.ask-m .a{margin-top:4px;color:var(--ink);white-space:pre-line;overflow-wrap:anywhere}
.ask-m .a a{text-decoration:underline;text-underline-offset:3px}
.ask-m .a.wait{color:var(--ink-2)}
.ask-m .a.err{color:var(--red)}
.ask-n{margin-top:10px;font:400 12px/1.5 var(--mono);color:var(--ink-2)}
@media (max-width:1000px){.ask{max-width:420px}}
</style><!--/ask:css-->
'''

JS = '''<!--ask:js--><script>(() => {
const EP = '%s';
const f = document.getElementById('ask'); if (!f) return;
const q = document.getElementById('ask-q'), out = document.getElementById('ask-out'), sg = document.getElementById('ask-sg'), btn = f.querySelector('.ask-row button');
const hist = [];
const esc = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = s => esc(s).replace(/\\*\\*(.+?)\\*\\*/g, '$1')
  .replace(/https?:\\/\\/[^\\s<)]+[^\\s<).,;:!?]/g, u => '<a href="' + u + '"' + (u.startsWith('https://vitosemeraro.com') ? '' : ' target="_blank" rel="noopener"') + '>' + u.replace(/^https?:\\/\\/(www\\.)?/, '').replace(/\\/$/, '') + '</a>')
  .replace(/[\\w.+-]+@[\\w-]+\\.[\\w.]+[\\w]/g, m => '<a href="mailto:' + m + '">' + m + '</a>');
async function ask(text) {
  text = text.trim().slice(0, 400); if (!text || btn.disabled) return;
  sg.hidden = true; out.hidden = false; btn.disabled = true; q.value = '';
  const m = document.createElement('div'); m.className = 'ask-m';
  m.innerHTML = '<p class="q"></p><p class="a wait">Sto cercando nei testi del sito…</p>';
  m.querySelector('.q').textContent = text; out.appendChild(m); out.scrollTop = out.scrollHeight;
  const a = m.querySelector('.a');
  hist.push({ role: 'user', content: text });
  try {
    const r = await fetch(EP, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages: hist.slice(-12) }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.answer) throw new Error(d.message || 'Ora non riesco a rispondere. Puoi scrivere a vsemeraro@gmail.com.');
    a.className = 'a'; a.innerHTML = fmt(d.answer); hist.push({ role: 'assistant', content: d.answer });
  } catch (e) {
    hist.pop(); a.className = 'a err'; a.innerHTML = fmt(e.message && !/fetch|network/i.test(e.message) ? e.message : 'Ora non riesco a rispondere. Puoi scrivere a vsemeraro@gmail.com.');
  }
  btn.disabled = false; out.scrollTop = out.scrollHeight;
  if (window.ccLoaded && window.gtag) gtag('event', 'ask_vito', { turn: Math.ceil(hist.length / 2) });
}
f.addEventListener('submit', e => { e.preventDefault(); ask(q.value); });
sg.addEventListener('click', e => { const b = e.target.closest('button'); if (b) ask(b.textContent); });
})();</script><!--/ask:js-->
''' % EP

# 1) campo sotto il ritratto, dentro <figure class="portrait">
m = re.search(r'(<figure class="portrait">.*?</div>\n)(\s*</figure>)', h, re.S)
assert m, 'ritratto non trovato'
h = h[:m.end(1)] + '      ' + HTML + h[m.start(2):]
# 2) CSS prima di </head>, JS prima di </body>
h = h.replace('</head>', CSS + '</head>', 1)
h = h.replace('</body>', JS + '</body>', 1)
open(path, 'w', encoding='utf-8').write(h)
print('ok', path)
