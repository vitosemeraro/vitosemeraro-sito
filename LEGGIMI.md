# Pubblicare vitosemeraro.com su Firebase Hosting

**Dal 05/11/2026 la pubblicazione è automatica:** ogni push su `main` di questo repository avvia il workflow "Deploy to Firebase Hosting on merge", che carica `public/` su Firebase (progetto `vitosemeraro`). I passi manuali qui sotto restano solo come riserva.

La cartella è pronta. `public/` contiene il sito: la home, le due pagine, la pagina 404, la sitemap, il file robots, l'immagine di condivisione e tutte le immagini e i font in `assets/`. `firebase.json` contiene già le regole di URL e di cache.

## 1. Crea il progetto Firebase (una volta sola)
1. Vai su https://console.firebase.google.com e crea un progetto, per esempio `vitosemeraro`. Google Analytics non serve.
2. Se Firebase ti assegna un ID diverso da `vitosemeraro`, scrivilo in `.firebaserc` al posto di `vitosemeraro`.

## 2. Pubblica (ogni volta che cambi il sito)
Ti servono Node.js LTS (https://nodejs.org) e un terminale aperto in questa cartella:

```
npm install -g firebase-tools
firebase login
firebase deploy --only hosting
```

Alla fine il comando stampa un indirizzo `https://<id-progetto>.web.app`: aprilo e controlla il sito.

## 3. Collega il dominio comprato su Netsons
1. In Firebase vai su Hosting, poi "Aggiungi dominio personalizzato", e inserisci `vitosemeraro.com`.
2. Firebase ti dà un record **TXT** per la verifica e uno o più record **A**.
3. In Netsons apri l'area clienti, poi il dominio e la gestione DNS. Aggiungi esattamente quei record e cancella gli eventuali record A già presenti per `@`, quelli della pagina di parcheggio.
4. Ripeti con `www.vitosemeraro.com`, scegliendo "Reindirizza a vitosemeraro.com".
5. La propagazione dei DNS richiede da pochi minuti a 24 ore. Il certificato HTTPS lo emette Firebase in automatico.

## 4. Fatti trovare
- Su Google Search Console (https://search.google.com/search-console) aggiungi la proprietà di dominio `vitosemeraro.com`, verificala con un altro record TXT su Netsons e invia `https://vitosemeraro.com/sitemap.xml`.

## Costi
- Il piano gratuito Spark offre 10 GB di spazio e 360 MB al giorno di traffico. Una prima visita completa alla home pesa circa 1,2 MB, quindi stai nel gratuito fino a circa 290 nuovi visitatori al giorno. Chi torna sul sito usa la cache e pesa molto meno.
- Se un giorno superi la soglia, passa al piano Blaze, a 0,15 $ per GB oltre la quota gratuita, e imposta un avviso di budget di pochi euro.

## Ancora da fare sul sito
- Il modulo della newsletter non invia ancora nulla: serve un servizio come Brevo o Buttondown.
- Alcuni link puntano ancora a `#`: "Tutti i progetti", "Leggi" nel Playbook, "Tutte le interviste" e Privacy.
- L'email è ancora quella Gmail. Con il dominio puoi creare un indirizzo come `vito@vitosemeraro.com`.
