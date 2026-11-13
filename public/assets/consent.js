/*! consent.js v1.0.0 · banner cookie unico: "Accetta tutti" in evidenza, "Impostazioni" con le categorie,
 *  X di chiusura = solo cookie tecnici. Google Consent Mode v2 (default denied) e nessuno script di
 *  terze parti prima del consenso. Licenza MIT.
 *
 *  Uso (nel <head>, PRIMA di ogni altro script che chiama gtag):
 *    <script src="/assets/consent.js" data-ga="G-XXXX" data-policy="/privacy/#cookie"></script>
 *  Attributi facoltativi:
 *    data-gtm="GTM-XXXX"      carica anche Google Tag Manager dopo il consenso
 *    data-clarity="abcd123"   carica anche Microsoft Clarity dopo il consenso
 *    data-lang="it"           lingua del banner (di default <html lang>): it en fr de nl es
 *    data-legacy="vecchia_chiave"  rilegge la scelta salvata dal banner precedente
 *    data-accent="#123F37"    colore del pulsante principale
 *  Per riaprire le impostazioni: un elemento con l'attributo data-cc-open (es. link "Cookie" nel footer).
 *  API: window.cc.open(), window.cc.granted(), document 'cc:change' (detail.analytics true/false).
 */
(function () {
  if (window.cc) return;
  var S = document.currentScript, D = (S && S.dataset) || {}, C = window.CC_CONFIG || {};
  function opt(k) { return C[k] != null ? C[k] : D[k]; }
  var KEY = 'cc-consent', VER = 1, DAY = 864e5;
  var KEEP_YES = 365 * DAY, KEEP_NO = 182 * DAY; // si richiede dopo 12 mesi se accettato, 6 se rifiutato
  var GA = opt('ga'), GTM = opt('gtm'), CLARITY = opt('clarity');

  // 1. Consent Mode v2: tutto negato finché la persona non sceglie
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  gtag('consent', 'default', { ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied',
    analytics_storage: 'denied', functionality_storage: 'granted', security_storage: 'granted' });
  gtag('set', 'ads_data_redaction', true);

  // 2. scelta salvata (con migrazione dal banner precedente del sito)
  function read() {
    var v = null;
    try { v = JSON.parse(localStorage.getItem(KEY)); } catch (e) {}
    if (v && v.v === VER && Date.now() - v.t < (v.a ? KEEP_YES : KEEP_NO)) return v;
    var old = opt('legacy');
    if (!v && old) {
      var raw = null; try { raw = localStorage.getItem(old); } catch (e) {}
      if (raw != null) {
        var yes = /^(y|1|si|sì|yes|true|granted|accept(ed)?|all)$/i.test(raw) || /"analytics"\s*:\s*true/.test(raw);
        var no = /^(n|0|no|false|denied|reject(ed)?|tech)$/i.test(raw) || /"analytics"\s*:\s*false/.test(raw);
        if (yes || no) { var m = { v: VER, a: yes ? 1 : 0, t: Date.now() }; write(m); return m; }
      }
    }
    return null;
  }
  function write(m) { try { localStorage.setItem(KEY, JSON.stringify(m)); } catch (e) {} }

  // 3. caricamento degli strumenti di statistica solo dopo il consenso
  var loaded = false;
  function add(src) { var s = document.createElement('script'); s.async = true; s.src = src; document.head.appendChild(s); }
  function load() {
    if (loaded) return; loaded = true; window.ccLoaded = true;
    gtag('consent', 'update', { analytics_storage: 'granted' });
    if (GA) { add('https://www.googletagmanager.com/gtag/js?id=' + GA); gtag('js', new Date()); gtag('config', GA); }
    if (GTM) { window.dataLayer.push({ 'gtm.start': Date.now(), event: 'gtm.js' }); add('https://www.googletagmanager.com/gtm.js?id=' + GTM); }
    if (CLARITY) {
      window.clarity = window.clarity || function () { (window.clarity.q = window.clarity.q || []).push(arguments); };
      add('https://www.clarity.ms/tag/' + CLARITY);
    }
  }
  function wipe() {
    document.cookie.split(';').forEach(function (c) {
      var n = c.split('=')[0].trim();
      if (/^(_ga|_gid|_gat|_clck|_clsk|_gcl)/.test(n)) {
        var h = location.hostname, ds = ['', h, '.' + h, '.' + h.split('.').slice(-2).join('.')];
        ds.forEach(function (d) { document.cookie = n + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + (d ? '; domain=' + d : ''); });
      }
    });
  }

  var state = read();
  if (state && state.a) load();

  // 4. testi
  var L = {
    it: { t: 'Cookie', x: 'Usiamo cookie tecnici, necessari al sito, e, solo se accetti, cookie di statistica ({tools}) per capire quali pagine sono utili.',
      p: 'Cookie policy', ok: 'Accetta tutti', set: 'Impostazioni', close: 'Chiudi: continua solo con i cookie tecnici',
      st: 'Preferenze cookie', nec: 'Tecnici', necd: 'Servono a far funzionare il sito e a ricordare questa scelta.', on: 'Sempre attivi',
      an: 'Statistica', and: 'Misurano in forma aggregata visite e contatti ({tools}). Nessuna pubblicità.', save: 'Salva le scelte' },
    en: { t: 'Cookies', x: 'We use technical cookies the site needs and, only if you accept, statistics cookies ({tools}) to learn which pages are useful.',
      p: 'Cookie policy', ok: 'Accept all', set: 'Settings', close: 'Close: continue with technical cookies only',
      st: 'Cookie preferences', nec: 'Technical', necd: 'Needed for the site to work and to remember this choice.', on: 'Always on',
      an: 'Statistics', and: 'Aggregated measurement of visits and contacts ({tools}). No advertising.', save: 'Save choices' },
    fr: { t: 'Cookies', x: 'Nous utilisons des cookies techniques nécessaires au site et, seulement si vous acceptez, des cookies de statistiques ({tools}) pour savoir quelles pages sont utiles.',
      p: 'Politique cookies', ok: 'Tout accepter', set: 'Paramètres', close: 'Fermer : continuer avec les cookies techniques uniquement',
      st: 'Préférences cookies', nec: 'Techniques', necd: 'Nécessaires au fonctionnement du site et pour mémoriser ce choix.', on: 'Toujours actifs',
      an: 'Statistiques', and: 'Mesure agrégée des visites et des contacts ({tools}). Aucune publicité.', save: 'Enregistrer mes choix' },
    de: { t: 'Cookies', x: 'Wir verwenden technisch notwendige Cookies und, nur mit deiner Zustimmung, Statistik-Cookies ({tools}), um zu sehen, welche Seiten nützlich sind.',
      p: 'Cookie-Richtlinie', ok: 'Alle akzeptieren', set: 'Einstellungen', close: 'Schließen: nur mit technischen Cookies fortfahren',
      st: 'Cookie-Einstellungen', nec: 'Technisch', necd: 'Nötig, damit die Seite funktioniert und diese Wahl gespeichert bleibt.', on: 'Immer aktiv',
      an: 'Statistik', and: 'Zusammengefasste Messung von Besuchen und Kontakten ({tools}). Keine Werbung.', save: 'Auswahl speichern' },
    nl: { t: 'Cookies', x: 'We gebruiken technische cookies die de site nodig heeft en, alleen als je akkoord gaat, statistiekcookies ({tools}) om te zien welke pagina’s nuttig zijn.',
      p: 'Cookiebeleid', ok: 'Alles accepteren', set: 'Instellingen', close: 'Sluiten: doorgaan met alleen technische cookies',
      st: 'Cookievoorkeuren', nec: 'Technisch', necd: 'Nodig om de site te laten werken en deze keuze te onthouden.', on: 'Altijd actief',
      an: 'Statistiek', and: 'Geaggregeerde meting van bezoeken en contacten ({tools}). Geen advertenties.', save: 'Keuzes opslaan' },
    es: { t: 'Cookies', x: 'Usamos cookies técnicas necesarias para el sitio y, solo si aceptas, cookies de estadística ({tools}) para saber qué páginas son útiles.',
      p: 'Política de cookies', ok: 'Aceptar todo', set: 'Configuración', close: 'Cerrar: continuar solo con cookies técnicas',
      st: 'Preferencias de cookies', nec: 'Técnicas', necd: 'Necesarias para que el sitio funcione y para recordar esta elección.', on: 'Siempre activas',
      an: 'Estadística', and: 'Medición agregada de visitas y contactos ({tools}). Sin publicidad.', save: 'Guardar elección' }
  };
  var lang = String(opt('lang') || document.documentElement.lang || 'it').slice(0, 2).toLowerCase();
  var T = L[lang] || L.en;
  var tools = [GA || GTM ? 'Google Analytics' : '', CLARITY ? 'Microsoft Clarity' : ''].filter(Boolean).join(', ') || 'Google Analytics';
  function tx(k) { return T[k].replace('{tools}', tools); }

  // 5. interfaccia
  var accent = opt('accent') || '#1a1a1a';
  var CSS = '.cc-box{position:fixed;z-index:2147483000;left:16px;right:16px;bottom:16px;max-width:420px;margin-left:auto;box-sizing:border-box;' +
    'background:#fff;color:#1a1a1a;border:1px solid rgba(0,0,0,.14);border-radius:14px;box-shadow:0 10px 32px rgba(0,0,0,.18);' +
    'padding:18px 18px 14px;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;text-align:left}' +
    '.cc-box *{box-sizing:border-box}.cc-box[hidden]{display:none}' +
    '.cc-h{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin:0 0 6px}' +
    '.cc-h b{font-size:16px;font-weight:650}' +
    '.cc-x{flex:none;width:28px;height:28px;margin:-6px -6px 0 0;border:0;background:none;color:#8a8a8a;font-size:20px;line-height:28px;cursor:pointer;border-radius:50%;padding:0}' +
    '.cc-x:hover{color:#444;background:rgba(0,0,0,.05)}' +
    '.cc-box p{margin:0 0 14px;color:#3a3a3a;font-size:14px}.cc-box a{color:inherit;text-decoration:underline;text-underline-offset:2px}' +
    '.cc-ok{display:block;width:100%;padding:13px 16px;border:0;border-radius:10px;background:' + accent + ';color:#fff;font-family:inherit;font-weight:600;font-size:16px;line-height:1.2;cursor:pointer}' +
    '.cc-ok:hover{filter:brightness(1.12)}' +
    '.cc-set{display:block;margin:8px auto 0;padding:6px 8px;border:0;background:none;color:#555;font-family:inherit;font-size:14px;line-height:1.3;text-decoration:underline;text-underline-offset:2px;cursor:pointer}' +
    '.cc-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:10px 0;border-top:1px solid rgba(0,0,0,.08)}' +
    '.cc-row strong{display:block;font-size:14px}.cc-row small{display:block;color:#666;font-size:13px;line-height:1.4}' +
    '.cc-row em{font-style:normal;font-size:12px;color:#666;white-space:nowrap;padding-top:2px}' +
    '.cc-sw{position:relative;flex:none;width:42px;height:24px;margin-top:2px}.cc-sw input{position:absolute;opacity:0;width:100%;height:100%;margin:0;cursor:pointer}' +
    '.cc-sw span{position:absolute;inset:0;border-radius:24px;background:#c9c9c9;transition:background .15s;pointer-events:none}' +
    '.cc-sw span:after{content:"";position:absolute;left:3px;top:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:transform .15s}' +
    '.cc-sw input:checked+span{background:' + accent + '}.cc-sw input:checked+span:after{transform:translateX(18px)}' +
    '.cc-sw input:focus-visible+span{outline:2px solid ' + accent + ';outline-offset:2px}' +
    '.cc-save{display:block;width:100%;margin-top:12px;padding:11px 16px;border:1px solid rgba(0,0,0,.25);border-radius:10px;background:#fff;color:#1a1a1a;font-family:inherit;font-weight:600;font-size:15px;line-height:1.2;cursor:pointer}' +
    '.cc-box button:focus-visible{outline:2px solid ' + accent + ';outline-offset:2px}' +
    '@media (prefers-color-scheme:dark){.cc-box{background:#1f1f1f;color:#f2f2f2;border-color:rgba(255,255,255,.16)}.cc-box p{color:#d0d0d0}' +
    '.cc-x{color:#9a9a9a}.cc-x:hover{color:#eee;background:rgba(255,255,255,.08)}.cc-set{color:#c8c8c8}.cc-row{border-color:rgba(255,255,255,.1)}' +
    '.cc-row small,.cc-row em{color:#aaa}.cc-save{background:#1f1f1f;color:#f2f2f2;border-color:rgba(255,255,255,.3)}}' +
    '@media (max-width:480px){.cc-box{left:10px;right:10px;bottom:10px;padding:16px 16px 12px}}' +
    '@media print{.cc-box{display:none}}';

  var box, view;
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function policy() { var p = opt('policy'); return p ? ' <a href="' + esc(p) + '">' + esc(T.p) + '</a>' : ''; }
  function head(title) {
    return '<div class="cc-h"><b id="cc-t">' + esc(title) + '</b><button type="button" class="cc-x" data-cc="close" aria-label="' +
      esc(T.close) + '" title="' + esc(T.close) + '">&times;</button></div>';
  }
  function render(v) {
    view = v;
    if (v === 'settings') {
      var on = !!(state && state.a);
      box.innerHTML = head(T.st) +
        '<div class="cc-row"><div><strong>' + esc(T.nec) + '</strong><small>' + esc(T.necd) + '</small></div><em>' + esc(T.on) + '</em></div>' +
        '<div class="cc-row"><div><strong>' + esc(T.an) + '</strong><small>' + esc(tx('and')) + policy() + '</small></div>' +
        '<label class="cc-sw"><input type="checkbox" id="cc-an" aria-label="' + esc(T.an) + '"' + (on ? ' checked' : '') + '><span></span></label></div>' +
        '<button type="button" class="cc-save" data-cc="save">' + esc(T.save) + '</button>' +
        '<button type="button" class="cc-ok" data-cc="all" style="margin-top:8px">' + esc(T.ok) + '</button>';
    } else {
      box.innerHTML = head(T.t) + '<p>' + esc(tx('x')) + policy() + '</p>' +
        '<button type="button" class="cc-ok" data-cc="all">' + esc(T.ok) + '</button>' +
        '<button type="button" class="cc-set" data-cc="settings">' + esc(T.set) + '</button>';
    }
  }
  function decide(a) {
    var was = !!(state && state.a);
    state = { v: VER, a: a ? 1 : 0, t: Date.now() }; write(state);
    if (a) { load(); if (!was) gtag('event', 'cookie_choice', { choice: 'accept' }); }
    else { gtag('consent', 'update', { analytics_storage: 'denied' }); wipe(); }
    box.hidden = true;
    try { document.dispatchEvent(new CustomEvent('cc:change', { detail: { analytics: !!a } })); } catch (e) {}
    if (was && !a) setTimeout(function () { location.reload(); }, 50); // revoca: ferma subito gli script già caricati
  }
  function show(v) { if (!box) return; render(v || 'banner'); box.hidden = false; var b = box.querySelector(v === 'settings' ? '#cc-an' : '.cc-ok'); if (b) b.focus({ preventScroll: true }); }

  function init() {
    var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    box = document.createElement('div'); box.className = 'cc-box'; box.id = 'cc-consent'; box.hidden = true;
    box.setAttribute('role', 'dialog'); box.setAttribute('aria-labelledby', 'cc-t'); box.setAttribute('aria-live', 'polite');
    document.body.appendChild(box);
    box.addEventListener('click', function (e) {
      var b = e.target.closest('[data-cc]'); if (!b) return;
      var a = b.getAttribute('data-cc');
      if (a === 'all') decide(true);
      else if (a === 'close') decide(false);
      else if (a === 'settings') show('settings');
      else if (a === 'save') decide(document.getElementById('cc-an').checked);
    });
    box.addEventListener('keydown', function (e) { if (e.key === 'Escape' && view === 'settings' && state) box.hidden = true; });
    document.addEventListener('click', function (e) {
      var o = e.target.closest && e.target.closest('[data-cc-open],.cc-open');
      if (o) { e.preventDefault(); show('settings'); }
    });
    if (!state) { render('banner'); box.hidden = false; }
  }
  if (document.body) init(); else document.addEventListener('DOMContentLoaded', init);

  window.cc = { open: function () { show('settings'); }, granted: function () { return !!(state && state.a); }, version: '1.0.0' };
})();
