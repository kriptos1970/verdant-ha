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
