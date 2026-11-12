# Uso: python3 scripts/aggiungi_widget.py <pagina index.html> [endpoint]
# Inserisce (o sostituisce) il campo "Chiedi a Vito" sotto il ritratto nell'hero.
# Bilingue: se la pagina ha <html lang="en"> usa i testi inglesi, altrimenti quelli italiani.
# Si può rilanciare: tutto sta tra i marcatori <!--ask-->...<!--/ask-->, <!--ask:css--> e <!--ask:js-->.
import re, sys, json

path = sys.argv[1]
EP = sys.argv[2] if len(sys.argv) > 2 else 'https://chiedi-a-vito.cfdist2.workers.dev/chat'
h = open(path, encoding='utf-8').read()
for a, b in (('<!--ask-->', '<!--/ask-->'), ('<!--ask:css-->', '<!--/ask:css-->'), ('<!--ask:js-->', '<!--/ask:js-->')):
    h = re.sub(r'[ \t]*' + re.escape(a) + r'.*?' + re.escape(b) + r'\n?', '', h, flags=re.S)

EN = bool(re.search(r'<html[^>]*\blang="en', h))
T = {
    'label': 'Ask Vito' if EN else 'Chiedi a Vito',
    'aria': 'Ask Vito, his second brain answers' if EN else 'Chiedi a Vito, risponde il suo second brain',
    'ph': 'What would you like to know?' if EN else 'Cosa vuoi sapere?',
    'btn': 'Ask' if EN else 'Chiedi',
    'sg': (['What is staged.ai?', 'How do you work with AI agents?', 'Which certifications do you hold?'] if EN
           else ['Cos’è staged.ai?', 'Come lavori con gli agenti AI?', 'Che certificazioni hai?']),
    'note': ('Answers come from Vito’s second brain, which can make mistakes. To double-check, write to me.' if EN
             else 'Risponde il second brain di Vito, che può sbagliare. Per conferme, scrivimi.'),
    'wait': 'Looking through my notes…' if EN else 'Sto cercando nei miei appunti…',
    'err': 'I can’t answer right now. You can write to vsemeraro@gmail.com.' if EN
           else 'Ora non riesco a rispondere. Puoi scrivere a vsemeraro@gmail.com.',
}

HTML = '''      <!--ask--><form class="ask" id="ask" autocomplete="off" aria-label="%(aria)s">
        <label class="lbl" for="ask-q">%(label)s</label>
        <div class="ask-row"><input id="ask-q" name="q" type="text" maxlength="400" placeholder="%(ph)s" enterkeyhint="send"><button type="submit">%(btn)s <span aria-hidden="true">→</span></button></div>
        <div class="ask-sg" id="ask-sg">%(sg)s</div>
        <div class="ask-out" id="ask-out" aria-live="polite" hidden><div class="ask-new" id="ask-new"></div><div class="ask-old" id="ask-old" aria-hidden="true"></div></div>
        <p class="ask-n">%(note)s</p>
      </form><!--/ask-->
''' % {**T, 'sg': ''.join(f'<button type="button">{s}</button>' for s in T['sg'])}

CSS = '''<!--ask:css--><style>
.ask{margin-top:20px;font:400 16px/1.5 var(--serif)}
.ask .lbl{display:block;color:var(--ink)}
.ask-row{display:flex;margin-top:8px;border:1px solid var(--ink);background:var(--paper)}
.ask-row input{flex:1;min-width:0;border:0;background:transparent;color:var(--ink);font:400 17px/1.4 var(--serif);padding:12px}
.ask-row input::placeholder{color:var(--ink-2);opacity:.75}
.ask-row input:focus{outline:none}
.ask-row:focus-within{outline:2px solid var(--red);outline-offset:2px}
.ask-row button{flex:none;border:0;border-left:1px solid var(--ink);background:var(--ink);color:var(--paper);font:500 14px/1 var(--mono);padding:0 16px;cursor:pointer}
.ask-row button:disabled{opacity:.6;cursor:wait}
.ask-sg{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.ask-sg[hidden],.ask-out[hidden]{display:none}
.ask-sg button{font:400 13px/1.3 var(--mono);color:var(--ink);background:transparent;border:1px solid var(--rule);padding:6px 9px;cursor:pointer;text-align:left}
.ask-sg button:hover{border-color:var(--ink)}
.ask-out{margin-top:14px}
.ask-m{padding:12px 0;border-top:1px solid var(--rule)}
.ask-m .q{font:400 13px/1.5 var(--mono);color:var(--ink-2)}
.ask-m .a{margin-top:4px;color:var(--ink);white-space:pre-line;overflow-wrap:anywhere}
.ask-m .a a{text-decoration:underline;text-underline-offset:3px}
.ask-m .a.wait{color:var(--ink-2)}
.ask-m .a.err{color:var(--red)}
/* older answers slide under a fade from the page background to transparent */
.ask-old{position:relative;max-height:150px;overflow:hidden;pointer-events:none}
.ask-old:empty{display:none}
.ask-old::after{content:"";position:absolute;inset:0;background:linear-gradient(to top,var(--paper) 15%,rgba(238,242,240,0))}
.ask-new .ask-m,.ask-old .ask-m{animation:ask-in .35s ease-out}
@keyframes ask-in{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.ask-new .ask-m,.ask-old .ask-m{animation:none}}
.ask-n{margin-top:10px;font:400 12px/1.5 var(--mono);color:var(--ink-2)}
@media (max-width:1000px){.ask{max-width:420px}}
</style><!--/ask:css-->
'''

JS = '''<!--ask:js--><script>(() => {
const EP = %s, T = %s;
const f = document.getElementById('ask'); if (!f) return;
const q = document.getElementById('ask-q'), out = document.getElementById('ask-out'), nw = document.getElementById('ask-new'), old = document.getElementById('ask-old'), sg = document.getElementById('ask-sg'), btn = f.querySelector('.ask-row button');
const hist = [];
const esc = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = s => esc(s).replace(/\\*\\*(.+?)\\*\\*/g, '$1')
  .replace(/https?:\\/\\/[^\\s<)]+[^\\s<).,;:!?]/g, u => '<a href="' + u + '"' + (u.startsWith('https://vitosemeraro.com') ? '' : ' target="_blank" rel="noopener"') + '>' + u.replace(/^https?:\\/\\/(www\\.)?/, '').replace(/\\/$/, '') + '</a>')
  .replace(/[\\w.+-]+@[\\w-]+\\.[\\w.]+[\\w]/g, m => '<a href="mailto:' + m + '">' + m + '</a>');
async function ask(text) {
  text = text.trim().slice(0, 400); if (!text || btn.disabled) return;
  sg.hidden = true; out.hidden = false; btn.disabled = true; q.value = '';
  // the previous answer moves below, under the fade; the new one sits right under the input
  for (const m of [...nw.children].reverse()) old.prepend(m);
  while (old.children.length > 3) old.lastChild.remove();
  const m = document.createElement('div'); m.className = 'ask-m';
  m.innerHTML = '<p class="q"></p><p class="a wait"></p>';
  m.querySelector('.q').textContent = text; m.querySelector('.a').textContent = T.wait; nw.appendChild(m);
  const a = m.querySelector('.a');
  hist.push({ role: 'user', content: text });
  try {
    const r = await fetch(EP, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages: hist.slice(-12) }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.answer) throw new Error(d.message || T.err);
    a.className = 'a'; a.innerHTML = fmt(d.answer); hist.push({ role: 'assistant', content: d.answer });
  } catch (e) {
    hist.pop(); a.className = 'a err'; a.innerHTML = fmt(e.message && !/fetch|network/i.test(e.message) ? e.message : T.err);
  }
  btn.disabled = false;
  if (window.ccLoaded && window.gtag) gtag('event', 'ask_vito', { turn: Math.ceil(hist.length / 2) });
}
f.addEventListener('submit', e => { e.preventDefault(); ask(q.value); });
sg.addEventListener('click', e => { const b = e.target.closest('button'); if (b) ask(b.textContent); });
})();</script><!--/ask:js-->
''' % (json.dumps(EP), json.dumps({'wait': T['wait'], 'err': T['err']}, ensure_ascii=False))

m = re.search(r'(<figure class="portrait">.*?</div>\n)(\s*</figure>)', h, re.S)
assert m, 'ritratto non trovato'
h = h[:m.end(1)] + HTML + h[m.start(2):]
h = h.replace('</head>', CSS + '</head>', 1)
h = h.replace('</body>', JS + '</body>', 1)
open(path, 'w', encoding='utf-8').write(h)
print('ok', path, 'EN' if EN else 'IT')
