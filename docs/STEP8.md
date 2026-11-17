# Step 8 — consolidamento dell’archivio (0.9.0)

La collezione usa `GET /api/plants?summary=true`: conserva anagrafica, conteggi, calendario, trattamenti e apprendimento, senza trasferire di nuovo cronologia, crescita e album salute di tutte le piante. La singola scheda completa viene richiesta all’apertura e dopo una variazione della sua versione. Risposte superate dopo cambio pianta vengono ignorate; errori di caricamento offrono «Riprova». Una scheda sintetica non può essere salvata al posto di quella completa.

La cronologia generale usa `GET /api/history` con 50 eventi per pagina, limite API massimo 100, filtri per ambiente, pianta, tipo e date. Query SQLite JSON in sola lettura, ordinamento deterministico per istante/pianta/evento, eventi eliminati esclusi. Le date sono giorni locali nel fuso configurato, incluso il cambio d’ora. Al cambio filtri/versioni si torna alla prima pagina. Le pagine rappresentano l’archivio corrente, non un’istantanea permanente tra client differenti.

Nel diario di una pianta si mostrano 50 cure e 12 storie di crescita per pagina. Tutti gli elementi rimangono nell’archivio. Conteggi dell’analisi ricavati dalla proiezione completa sul server. Nessuna modifica a provider/prompt AI, calcoli nativi, schema SQLite, percorso foto o politica di conservazione; nessuna eliminazione automatica dei file.

## Verifiche

- 140 test automatici, compresi equivalenza delle proiezioni, conservazione del documento completo, blocco del salvataggio sintetico, paginazione senza duplicati su date uguali, filtri e giorno locale di 25 ore.
- Browser con archivio sintetico di tre piante: 219 eventi e 45 storie. Cronologia 50 righe, seconda pagina, filtro ambiente e tipo (37 eventi), dettaglio e diario 50/23 cure, 12 storie per pagina. Modifica note salvata conservando tutti i 219 eventi e 45 storie. Layout mobile 390 px senza overflow.
- Benchmark ripetibile: `.venv/bin/python scripts/benchmark_archive.py`. Archivio temporaneo isolato, 100 piante e 50.000 eventi; nessun backup o richiesta esterna. Risposta completa 12.361.171 byte, collezione sintetica 118.971 byte (−99,04%), pagina cronologia circa 18,5 KB. Tempi sul Mac di sviluppo: circa 0,38 s / 0,14 s / 0,16 s rispettivamente. Sono misure locali sintetiche, non tempi garantiti su HA o iPhone.

## Limiti e parti successive

Il server continua a leggere i documenti JSON completi per il calendario nativo; la cronologia usa `json_each`, senza un indice relazionale separato. La scheda aperta carica ancora tutto il documento di una singola pianta. La lista delle piante non è ancora paginata. Con volumi molto superiori può essere necessaria la normalizzazione locale; MariaDB esterno rimane rimandato.

Restano il collaudo Companion/iPhone fisico e della scansione QR, la revisione dei file fotografici non referenziati e il ripristino quando l’utente vorrà riattivare i backup. Non si cancellano foto automaticamente e non si creano backup operativi durante lo sviluppo.

Distribuzione della 0.9.0: 53 file sorgente trasferiti e verificati nella condivisione add-on. Build/smoke ARM64 e AMD64 passati. Pacchetto circa 232 KB, integro, senza foto o credenziali native. Installata il 16 novembre 2026 senza backup: stato «In esecuzione» e versione 0.9.0 verificati in Safari. Cronologia reale di 730 registrazioni attive, passaggio alla pagina 2 e filtro Balcone (213 eventi, ritorno alla pagina 1) verificati. Scheda Ficus, fotografia e diario completo caricati su richiesta; nessuna modifica alle cure o ai piani reali.

## Verifica 0.11.0 — 17 novembre 2026

La 0.11.0 è stata installata sull’installazione Home Assistant reale:

- sorgenti copiati in `/local_apps/plantcare_web` e copia dei sorgenti 0.10.3 conservata in `/tmp/plantcare_web-0.10.3-src.tgz`;
- `ha refresh-updates` e `ha apps update local_plantcare_web` completati;
- add-on **in esecuzione**, versione **0.11.0**, nessun errore nei log;
- opzioni esistenti conservate, nuova opzione `language: auto`;
- fotografie condivise intatte: 124 file, 358,5 MB in `/share/plantcare/photos`;
- consumo osservato: circa 76 MB di RAM, 0,1% CPU; Supervisor sano e supportato;
- nessun backup Home Assistant creato durante l’aggiornamento.

Benchmark sintetico ripetuto: 100 piante e 50.000 eventi, risposta della collezione ridotta del 99,04%, pagina cronologia circa 18,5 KB e 0,163 s sul Mac di sviluppo. Restano aperti i collaudi che richiedono hardware o archivi reali:

- iPhone fisico con Companion e area sicura;
- scansione QR/NFC con fotocamera reale;
- ripristino completo su un’installazione HA isolata;
- sensori HA e Open-Meteo live;
- archivio reale molto più grande del benchmark sintetico.

### Collaudo Ingress 0.11.0 — 17 novembre 2026

Accesso reale tramite `https://sicoli.ovh/app/local_plantcare_web` con sessione Home Assistant:

- versione **0.11.0** mostrata in Impostazioni, con archivio reale di **18 piante**, 124 foto (357,7 MB), SQLite 0,6 MB e 174,8 GB liberi;
- lingua `auto` in italiano; passaggio a inglese verificato con navigazione, impostazioni e calendario tradotti, poi ripristino a `auto`/italiano;
- calendario del 17 novembre con 1 attività in scadenza e 1 attività precedente ancora in attesa;
- etichetta QR/NFC generata per Ficus Elastica: collegamento `https://sicoli.ovh/app/local_plantcare_web/plant/170F12A0-7D2E-489E-AF4A-116A108D6985`, senza token Ingress; la scansione con fotocamera reale resta da fare;
- layout mobile reale a 734 × 766 CSS px, con barra inferiore e schede piante;
- nessun errore console; nessuna cura registrata e nessun piano modificato durante il controllo.

Restano distinti i collaudi su iPhone fisico/Companion, la scansione QR/NFC reale, il ripristino su HA isolato, i sensori e il meteo live, e un archivio reale molto più grande.

### Prestazioni foto 0.11.1 — 17 novembre 2026

Prima della correzione la lista piante caricava gli originali: 18 immagini 3024 × 4032, **43,18 MB** in totale, con singole richieste da 3,2–4,7 MB e tempi di 3,6–5,3 s. Il middleware inoltre forzava `no-store` sulle risposte `/api`, annullando la cache anche per le miniature.

La 0.11.1:

- usa miniature 480 px nella lista, con relazioni 360 × 480 e file da 25–39 KB;
- applica `Cache-Control` immutabile ed ETag alle foto, che sono indirizzate per hash;
- genera le miniature con draft JPEG e scrittura atomica, protetta da lock.

Misura sull’archivio reale via Ingress:

- primo passaggio alla lista: immagini visibili caricate in circa 0,2–0,3 s ciascuna, circa **251 KB** per le immagini nel viewport;
- secondo passaggio: **12 ms**, 14 immagini già complete e **0 byte** trasferiti dalla rete, servite dalla cache del browser;
- le immagini fuori schermo restano `loading="lazy"` e vengono caricate solo quando servono.
