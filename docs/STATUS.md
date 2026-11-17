# Stato dell’incremento 0.11.1

## Stato rispetto agli otto step

| Step | Stato |
|---|---|
| 1 — Riferimento funzionale e visivo | Matrice funzionale presente; confronto con macOS eseguito per panoramica, calendario, prodotti e pianificazione dei cicli. Riferimento iOS aggiornato con le schermate native e web Avocado fornite dall’utente; verifica finale nel Companion fisico ancora necessaria. |
| 2 — Add-on e interfaccia | Installata e aggiornata alla 0.10.3 su Home Assistant il 16 novembre 2026; avvio e interfaccia Ingress verificati in Safari. |
| 3 — Archivio e importazione | Archivio personale importato su Home Assistant: 18 piante, 7 prodotti e 124 fotografie; collezione, diario, prodotti e scadenze verificati in Ingress. |
| 4 — Cure e calendario | Completato per questo incremento: giro guidato, calendario settimana/mese, cronologia filtrabile, registrazioni e cicli di trattamento. |
| 5 — Motore adattivo e sensori | Implementato: pianificatore adattivo verificato con Swift, meteo opzionale, apprendimento e Care Engine avanzato in shadow. Attivazione operativa delle raccomandazioni esclusa da questo incremento. |
| 6 — Assistente AI | Implementati catalogo modelli, scelta modello, applicazione selettiva con anteprima, cache, notifiche e controlli delle risposte. Test simulati passati; Gemini reale verificato su Ficus con risposta strutturata e anteprima selettiva. Applicazione su dati reali e analisi giornaliera ancora da collaudare. |
| 7 — Funzioni aggiuntive native | Prima parte implementata: riconoscimento Pl@ntNet, biblioteca delle specie importate e consultazione Perenual. Guide e diagnosi guidata implementate; album salute annotati, QR/NFC e consultazione Open Plantbook aggiunti nella 0.7.0. Catalogo online e collegamento guidato dei profili botanici implementati nella 0.8.0; installata e avviata su HA il 16 novembre 2026. |
| 8 — Consolidamento | 0.11.1 installata e verificata via Ingress su Home Assistant con archivio reale; benchmark sintetico 100 piante/50.000 eventi; restano collaudi fisici, ripristino isolato e archivio reale molto grande. |

## Grafici — fase 1 (17 novembre 2026)

- Porting di `healthAssessment` in `backend/health.py`, con i casi di `HealthScoreTests.swift` come riferimento: punteggio 20–100, etichetta e consiglio con codici traducibili.
- `_health` disponibile nella scheda pianta e nella collezione sintetica, senza reintrodurre la cronologia nella lista.
- Endpoint `/api/analytics` per cure completate, giorni attivi, regolarità dell’acqua, attività giornaliera, tipi di cura, ambienti, stato salute e piante da osservare.
- Endpoint `/api/plants/{id}/timeline` per unire eventi e misure.
- **180 test backend**; benchmark 100 piante/50.000 eventi: analisi circa 52 ms, indice salute circa 24 ms per 100 piante. Nessun dato reale modificato.
- Verifica in sola lettura sull’archivio reale: 18 piante, 732 eventi; 103 cure/20 giorni attivi/71% a 30 giorni, 495/77/83% a 90 giorni, 677/129/85% a 365 giorni. Scadenze acqua e concime identiche alla 0.11.1 per tutte le piante.
- Dettagli e contratto in [ANALYTICS.md](ANALYTICS.md).

## Grafici — fase 2 (17 novembre 2026)

- Componenti condivisi: palette, pannello, stati vuoti, scheletri, tabelle dati accessibili e `DeferredSection` con `IntersectionObserver`.
- Recharts 3.11.0 confinato in `charts.tsx`, caricato con `React.lazy` solo nella pagina Analisi e solo quando il pannello si avvicina alla vista; il chunk principale cresce di circa 13 kB, Recharts resta un chunk separato da circa 130 kB gzip.
- Anello salute in SVG puro: quota di piante valutate in salute, con legenda e tabella. Nessuna animazione.
- Tre grafici reali su dati 30 giorni: attività giornaliera, tipi di cura, piante per ambiente con annaffiature in ritardo.
- Accessibilità: `accessibilityLayer`, titolo/descrizione SVG, tabelle con intestazioni e conteggi; animazioni disattivate con `prefers-reduced-motion`.
- Verifica: build e i18n (746 chiavi), 180 test backend, layout 320/390/430/1280 px senza overflow, chunk grafici non richiesto nella pagina Piante.
- Restano per le fasi successive il selettore 30/90/365 e i grafici di tendenza della singola pianta.

## Grafici — fase 3, Home (17 novembre 2026)

- La pagina Oggi aggiunge “Il tuo giardino in numeri”: anello salute della collezione, ritmo delle ultime due settimane e fino a tre piante da controllare per motivo salute.
- Solo componenti condivisi SVG/CSS: la Home non importa Recharts e il chunk `charts-*.js` non viene richiesto né all’avvio né scorrendo.
- La richiesta `/api/analytics?days=30` parte tramite `DeferredSection` solo quando il blocco si avvicina alla vista; caricamento, errore con “Riprova”, nessuna pianta valutata e collezione vuota sono gestiti.
- Accessibilità: nomi accessibili su anello e barre, tabella dati per l’attività, righe “Da controllare” come pulsanti con nome e stato visibili, colore sempre affiancato da etichette.
- Verifica: build, **763 chiavi i18n**, 180 test backend, layout 320/390/430/1280 px senza overflow, italiano e inglese, Lighthouse accessibilità 0.96 con i due rilievi preesistenti.
- Dettagli in [ANALYTICS.md](ANALYTICS.md).

## Correzione 0.4.1 — catalogo AI

- Corretti sul server `ai_provider` (Gemini) e `ai_model` (vuoto), senza modificare la chiave.
- Diagnosi reale di Google: HTTP 400, `INVALID_ARGUMENT`, motivo `API_KEY_INVALID`. Non è stato acquisito il valore della chiave nella chat o nei file di sviluppo.
- Gestione degli errori esterni migliorata: messaggi specifici e sicuri restituiti con 422/424, evitando che un 502 perda il dettaglio attraverso Ingress.
- **70 test automatici**, build e smoke ARM64/AMD64 passati. Su richiesta esplicita dell’utente, copiata la chiave di Verdant Server nella configurazione PlantCare tramite pipe interne a Home Assistant, senza output della chiave o file temporanei. Catalogo Gemini reale caricato correttamente in Ingress dopo il riavvio. Nessuna richiesta di generazione AI eseguita.

## Incremento 0.4.0 — step 6

- Prompt e provider nativi conservati. Schema della singola pianta con enum stabili, limite output 4.000 token e normalizzazione delle frequenze del view model nativo.
- Cataloghi testuali OpenAI/Gemini, paginazione, modello scelto sul server e invalidazione della scelta quando cambia la configurazione dell’add-on.
- Consiglio conservato per pianta, firma della richiesta senza prompt duplicato e cache delle richieste identiche.
- Applicazione selettiva di acqua, concime, controllo, potatura e rinvaso; anteprima del risultato effettivo con le politiche native Manuale/Intelligente/AI. Note aggiunte e conferma idempotente.
- Proposte obsolete e modifiche durante analisi rifiutate; risposte incomplete/rifiutate/non strutturate non applicate. Errori HTTP restituiti senza chiavi né messaggi grezzi del provider.
- Notifiche persistenti HA; un errore di notifica lascia disponibili le proposte. Analisi manuale aggiorna anche il giorno dell’ultima analisi.
- **61 test automatici** e **1.536 combinazioni** di applicazione selettiva confrontate eseguendo i metodi Swift originali.
- Provider e cataloghi verificati con trasporto HTTP simulato; nessuna credenziale prelevata dalle app native e nessuna richiesta AI a pagamento. Prova reale da eseguire quando saranno configurate le chiavi.
- Nessun backup Home Assistant creato durante questo incremento.
- Sorgenti 0.4.0 trasferiti (39 file verificati). Container aggiornato e dashboard 0.4.0 verificata su Home Assistant Ingress in Safari.
- Build e smoke test ARM64/AMD64 passati, inclusi consiglio simulato, anteprima e applicazione selettiva.
- Verificato il flusso browser locale a 390 px con risposta esplicitamente simulata; applicate soltanto concimazione e controllo salute.

## Incremento 0.3.0 — step 5

- Anteprima e applicazione atomica del piano, con controllo di versione e scadenza di 30 minuti.
- Piano stagionale per specie/famiglia/esposizione/clima, emisferi, soglie succulente, botanica salvata, motivazioni e aggiustamenti nativi.
- Meteo Open-Meteo esplicito e ricalcolo giornaliero; errori e modifiche concorrenti conservano i dati precedenti. Storico delle ultime 12 revisioni climatiche.
- Apprendimento dopo annaffiatura, protezione delle revisioni manuali/AI e rinvio del concime sulla nuova data dell’acqua.
- Consigli shadow per cinque domini, gate, confidenza, dati mancanti e analisi dell’asciugatura. Nessuna attivazione pompe.
- Osservazioni HA deduplicate e freschezza sulla data originale; conversione unità e validazione delle misure manuali.
- **45 test automatici passati**. **4.096 piani**, **7.160 raccomandazioni** e **20 serie di asciugatura** confrontati eseguendo i sorgenti Swift originali; conservati anche i precedenti 162 confronti.
- Flusso browser verificato su archivio sintetico separato: creazione pianta, anteprima, applicazione e aggiornamento effettivo di intervalli/calendario. Layout controllati a 390 e 1440 px.
- Build e smoke test isolati ARM64/AMD64: UI, API, SQLite, trattamenti, replay, piano intelligente, shadow engine, backup e confine Ingress.
- Chiamate meteo simulate nei test: non è stata inviata una località personale a Open-Meteo; integrazione live da verificare quando l’utente abilita il meteo.

## Novità verificate dello step 4

- Giro per ambiente ordinato per stanza e scadenza, una pianta alla volta, con Completata, Rimanda a domani e Salta.
- Lista iniziale stabile: il salvataggio di una cura non provoca il salto dell’attività successiva. Le attività cambiate altrove non vengono registrate come completate.
- Il giro tratta le attività di oggi, come il nativo. Le attività precedenti restano nel calendario.
- Acqua e concime raggruppati quando previsti nello stesso giorno; conferma esplicita dell’utente. I prodotti fogliari non vengono abbinati all’acqua.
- Comandi del giro idempotenti: ripetere una richiesta con lo stesso identificativo non crea doppie applicazioni; una richiesta basata su una scadenza o applicazione cambiata viene rifiutata.
- Calendario settimanale/mensile, prossime attività in attesa e cronologia con filtri per ambiente, pianta, tipo e date. Nessun evento storico inventato dalle proiezioni.
- Cicli di trattamento con prodotto, dose, note, primo intervento, intervallo, numero di applicazioni ed eventuale termine. Creazione da Prodotti e gestione dalla scheda della pianta.
- Modifica, interruzione reversibile e ripresa dei cicli. Il diario resta conservato. Conteggi e scadenze ricalcolati anche dopo modifica/eliminazione di un evento.
- Applicazioni importate prive di eventi di dettaglio preservate come baseline. Date Swift startDate/endDate convertite durante l’importazione.
- Panoramica, settimana, palette e disposizione desktop adeguate al riferimento macOS osservato.

## Verifiche

- **35 test automatici**: precedenti 26 più scenari dei trattamenti, replay, concorrenza, rinvii separati, termine del ciclo, modifica/eliminazione e importazione nativa.
- **162 confronti con esecuzione del codice Swift originale**: apprendimento, intervalli concime, allineamento, proiezione delle scadenze e cicli di trattamento, incluso cambio d’ora.
- TypeScript e build frontend.
- Build e avvio isolato dei container ARM64 e AMD64.
- Browser 390 px e 1440 px: giro completo su tre ambienti, trattamento, acqua+concime, rinvio, riepilogo corretto, creazione/interruzione/ripresa di un ciclo e viste calendario/cronologia. Nessun overflow orizzontale osservato su mobile.
- Riferimenti macOS in `docs/screenshots/native/`; prove web in `docs/screenshots/0.2.0/`. Le schermate native non sono incluse nel pacchetto di distribuzione.
- Le prove funzionali locali usano dati sintetici isolati in `/private/tmp/plantcare-step4-preview`. Installata la 0.2.0 e aggiornata alla 0.4.0 su Home Assistant con archivio vuoto: avvio automatico attivo, collegamento laterale PlantCare e dashboard Ingress verificati. Nessuna modifica degli archivi Apple.

## Funzioni precedenti conservate

Add-on Ingress senza porta pubblicata; SQLite locale; piante, prodotti, stanze, foto, diario di crescita; importazione nativa v1–v3; backup ZIP con checksum; percorso foto condiviso configurabile, miniature e statistiche; sensori autorizzati con campionamento e conservazione; OpenAI/Gemini con prompt nativi, proposte e controlli sulle proposte obsolete.

## Limiti ancora presenti

- I piani importati mantengono gli intervalli finché non vengono ricalcolati esplicitamente. Il meteo automatico richiede attivazione esplicita per pianta. Le misure dei sensori non cambiano il calendario: il Care Engine resta shadow, come previsto dal piano.
- Il motore legge i profili botanici e i dati di vaso/substrato dell’archivio importato. Catalogo e collegamento guidato sono disponibili dalla 0.8.0; la configurazione avanzata dei profili fisiologici resta da approfondire. Senza un profilo affidabile non vengono presunti requisiti idrici/nutrizionali.
- L’adattatore dati web e gli identificativi delle raccomandazioni usano una rappresentazione locale Python; i confronti Swift verificano gli esiti del pianificatore/evaluatori, non la parità binaria dell’intera app nativa.
- Le valutazioni usano al massimo le 10.000 letture SQL più recenti per pianta, oltre alle letture native conservate. Archivi molto grandi richiedono ancora il collaudo dello step 8.
- Gemini reale verificato con una richiesta sul Ficus; OpenAI e analisi giornaliera restano verificati con risposte simulate. L’equivalenza verificata non certifica l’intero motore AI/cure.
- Il contesto climatico salvato è un’istantanea: dalla 0.4.3 l’assistente ne riceve data e provenienza, con istruzioni per non trattarlo come meteo attuale o usarlo per modificare frequenze. La risposta AI resta da valutare; non viene eseguita una lettura meteo durante la domanda.
- Primo avvio e dashboard verificati su Home Assistant/Ingress reale in Safari; archivio personale importato e verificato nelle viste principali; collaudo con app Companion e iPhone fisico ancora da eseguire. Il confronto nativo eseguito è macOS.
- JSON nativo fino a 150 MB; ZIP web fino a 2 GB; foto nuove fino al limite configurato. Il JSON nativo richiede più RAM del peso del file per via dell’envelope base64.
- L’export ZIP usa file separati su disco e richiede spazio temporaneo in `/data` circa pari all’archivio fotografico. Le foto esterne in `/share` richiedono il relativo backup.
- Dalla 0.9.0 la collezione usa una proiezione senza cronologia; cronologia generale e diario sono paginati. La lista delle piante e la manutenzione dei file non referenziati restano da completare. Nessuna cancellazione automatica delle foto.
- MariaDB esterno rimandato per scelta dell’utente. Nessuna modifica allo schema SQLite o al percorso foto; provider e prompt AI conservati.

## Preferenze operative

Durante lo sviluppo non creare ulteriori backup, come richiesto dall’utente. MariaDB esterno resta rimandato.

## Importazione reale completata (0.4.2)

Supporto alle foto già presenti nella cartella condivisa, con controllo SHA256 e rispetto dei riferimenti eliminati. 74 test e build/smoke ARM64/AMD64 passati. Collezione reale letta in sola lettura e validata localmente: 18 piante, 7 prodotti, 731 eventi e 124 foto deduplicate (375 MB). Foto predisposte in `/share/plantcare/photos`. Importazione operativa completata e verificata in Safari: foto della collezione, scheda e diario Ficus, sette prodotti e calendario. Nessun backup creato, nessuna generazione AI avviata; dettaglio in IMPORT.md.

## Collaudo Gemini reale — 15 novembre 2026

- Singola richiesta autorizzata sul Ficus Elastica, modello `gemini-3.5-flash-lite`, risposta ricevuta alle 21:48:57. Nessuna fotografia inviata.
- Risposta strutturata accettata, riferimenti a specie, pianerottolo, concime COMPO e contesto climatico importato. Acqua 9 giorni e concime 18 giorni coerenti con il piano.
- Anteprima iniziale: controllo 7, potatura 90, rinvaso 365 giorni. Deselezionando queste tre attività, l’anteprima le mantiene non impostate.
- Non premuto «Applica attività selezionate»: frequenze, note e cronologia della pianta invariate; consiglio salvato e disponibile. Nessun backup creato.
- Limite osservato: dati climatici del piano storico presentati nella risposta senza data. Il prompt testuale nativo non include `generatedAt`; non viene eseguito un aggiornamento meteo per la richiesta.
- Prova: [anteprima selettiva reale](screenshots/0.4.2/live-ai-preview.jpg). Nessuna modifica al codice durante questo collaudo.

## Correzione contesto climatico 0.4.3

- Contesto del consiglio con data del piano (oppure data sconosciuta), data della richiesta e distinzione esplicita fra clima salvato e meteo attuale. Nessuna soglia arbitraria di freschezza.
- Stessa provenienza/data nell’analisi giornaliera. Regole numeriche native e provider conservati.
- Data visibile accanto al consiglio; versione del contesto per segnalare come obsoleti i consigli precedenti e impedirne cache, anteprima o applicazione fino alla rigenerazione. I consigli già applicati restano nello storico.
- 77 test passati, inclusi data valida/mancante/non valida e rigenerazione dei consigli precedenti; build frontend passata.

- Build e smoke isolati ARM64/AMD64 passati (nessun dato operativo usato). 40 file trasferiti e verificati SHA256. Aggiornamento 0.4.2 → 0.4.3 completato in Supervisor con backup disattivato; add-on in esecuzione e interfaccia Ingress verificati.

- Verifica reale 22:05:42: vecchio consiglio segnalato obsoleto e applicazione disabilitata; rigenerazione Gemini riuscita. Avviso visibile «Clima del piano salvato: 20/09/2026, 07:47:46. Questi dati non rappresentano il meteo attuale». Nuova risposta senza usare i valori climatici storici per motivare le frequenze (acqua 9, concime 18 giorni). Nessuna applicazione al piano, nessun backup. [Prova visiva](screenshots/0.4.3/dated-climate-advice.jpg).

## Incremento 0.5.0 — riconoscimento e biblioteca botanica

- API riconoscimento senza persistenza della foto; consenso esplicito, limite upload configurato, immagine normalizzata a 2.000 pixel/qualità 86 senza EXIF, massimo cinque risultati, errori sicuri.
- Bozza nuova pianta da candidato con nome/specie/famiglia/categoria e confidenza; fotografia caricata solo al salvataggio. Frequenze da verificare, nessun piano AI/adattivo generato automaticamente.
- Ricerca locale delle specie importate per nome, famiglia e sinonimi; consultazione esterna Perenual separata e facoltativa. Schede non esatte segnalate, tossicità assente non convertita in falsa sicurezza.
- 95 test passati e build frontend. Browser locale con trasporto provider simulato: consenso, riconoscimento, profilo Perenual, bozza e salvataggio completo con foto. Mobile 390 px senza overflow, filtro sinonimo verificato. Nessuna credenziale reale usata nel collaudo.
- Le funzioni esterne richiedono chiavi Pl@ntNet/Perenual; collaudo live ancora da eseguire con credenziali configurate. Guide, diagnosi, album salute, QR e Open Plantbook restano da implementare: lo step 7 non è ancora completo.

- Installata la 0.5.0 su Home Assistant: add-on in esecuzione, interfaccia Ingress verificata. Catalogo reale con 20 specie e ricerca Ficus verificati; Pl@ntNet e Perenual non ancora configurati, messaggi e pulsanti disabilitati corretti. Archivio operativo non modificato. 42 file trasferiti e verificati SHA256; build e smoke ARM64/AMD64 passati. Nessun backup Home Assistant creato. [Dettagli](STEP7.md) e [prova visiva](screenshots/0.5.0/home-assistant-library.jpg).

## Incremento 0.6.0 — guide native e controllo salute

Nove guide operative testuali, guida pratica per pianta e ritmo stagionale indicativo; diagnosi guidata locale con sei sintomi e priorità native. Nessuna scrittura di cure né chiamata AI. 103 test passati, 63 combinazioni diagnostiche e 288 punti stagionali verificati con esecuzione Swift originale; testi delle nove guide verificati. Build frontend e flusso browser desktop/mobile 390 px passati.

- 0.6.0 installata su Home Assistant e in esecuzione: guide verificate tramite Ingress. Build e smoke ARM64/AMD64 passati, 45 file trasferiti con verifica SHA256. Nessun backup creato.

## Correzione 0.6.1 — fotografie prodotti

Le sette foto dei prodotti risultano presenti in `/share/plantcare/photos`, con SHA256 corretto e riferimenti conservati nell’importazione. La pagina Prodotti usava sempre l’icona generica, ignorando `photoPath`. Aggiunta visualizzazione delle miniature, apertura dell’originale, ripiego sull’icona e anteprima/caricamento nell’editor. Nessuna reimportazione e nessuna modifica ai file esistenti. 103 test e build frontend passati.

- Correzione 0.6.1 installata e in esecuzione su Home Assistant, ricostruita con protezione del salvataggio durante l’upload. Verificate visivamente tutte e sette le fotografie nella pagina Prodotti e l’anteprima nell’editor cactacee (chiuso con Annulla). Nessun prodotto, fotografia o cura modificato durante il collaudo. Build ARM64/AMD64 e smoke isolati passati; [prova visiva](screenshots/0.6.1/product-photos.jpg).

## Sfondo bianco raggruppato nella 0.7.0

Sfondo principale impostato su bianco nei sorgenti CSS (root e superfici condivise), raggruppato nella 0.7.0 su richiesta dell’utente. Nessuna installazione intermedia dedicata al colore.

## Incremento 0.7.0 — album, QR e servizi botanici

- Sfondo bianco raggruppato nella nuova release, senza installazione intermedia dedicata al colore.
- Album salute con quattro angoli nativi, note e coordinate normalizzate; confronto precedente. Foto caricate solo alla conferma finale; metadati sessione ed evento salute salvati atomicamente, retry idempotente e conflitti di versione rifiutati. Immagini nei percorsi condivisi esistenti.
- QR PNG generato nel browser, stampa/download e copia collegamento NFC. URL HA stabile `/app/local_plantcare_web/plant/<UUID>`; proprietà di navigazione ricevute soltanto dal frame genitore della stessa origine. Nessun token Ingress nel QR. Apertura anche da etichette Verdant incollate nell’app. Fotocamera QR affidata al sistema del telefono.
- Open Plantbook: OAuth, alias nativi, ricerca/dettaglio e stima irrigazione nativa; Perenual alternativo. Consultazione informativa, senza applicazione automatica di soglie/intervalli. Testo italiano richiesto al provider; nessun traduttore esterno aggiunto.
- 123 test passati, build frontend e verifiche collegamenti. Browser isolato: salvataggio quattro foto e annotazione, confronto precedente, QR, navigazione HA simulata; mobile senza overflow e sfondo misurato `rgb(255, 255, 255)`.
- Credenziali trovate nelle preferenze Verdant, senza esporne i valori. Verifica dal Mac riuscita su Open Plantbook e Perenual con specie Ficus elastica; chiave Pl@ntNet presente, nessuna foto inviata al servizio. Configurazione HA completata: quattro campi riservati salvati e add-on riavviato.

- Pl@ntNet verificato dal Mac con chiamata autenticata alla lista dei progetti, senza fotografie o coordinate personali; risposta valida. Build e smoke ARM64/AMD64 passati, 49 file trasferiti e verificati SHA256. Aggiornamento raggruppato 0.7.0 avviato, backup disattivato.

- Release 0.7.0 installata su Home Assistant con un unico aggiornamento raggruppato e backup disattivato. Credenziali Pl@ntNet, Open Plantbook e Perenual copiate dalle preferenze Verdant nei campi riservati HA, senza output dei valori né file temporanei. Provider Gemini e altre opzioni conservati.
- Open Plantbook verificato dal server HA sul Ficus: fonte corretta, dati e soglie numeriche ricevuti. I testi del provider restano in inglese quando non tradotti dalla fonte; l’app richiede `lang=it` e non usa un servizio di traduzione aggiuntivo.
- Collegamento QR stabile verificato nel pannello HA reale: apertura diretta Ficus. QR generato con URL privo di token; nessuna stampa o scrittura NFC effettuata. Album già collaudato nell’archivio sintetico; nessun controllo sanitario aggiunto alle piante reali.

## Consolidamento iniziale — step 8

Verificati pacchetto sorgente integro (circa 208 KB, nessuna credenziale nativa e nessuna collezione fotografica), build/smoke ARM64/AMD64, 123 test e collegamenti. UI HA: SQLite circa 0,6 MB, 124 foto per 375120804 byte (357,7 MiB) in `/share/plantcare/photos`, oltre 177 GB liberi. Applicazione AI automatica disattivata, Gemini e fuso Europe/Rome conservati. Nessun dato operativo modificato nei controlli finali. Nessun backup creato.

Restano il collaudo Companion/iPhone fisico, scansione QR con dispositivo reale, carico su archivi molto più grandi, paginazione/manutenzione dei file non referenziati e prova di ripristino quando l’utente vorrà attivare i backup. Catalogo online e applicazione guidata dei profili botanici sono implementati nella 0.8.0. MariaDB esterno sempre rimandato.

## Correzione visiva inclusa nella 0.8.0

Dallo screenshot iPhone dell’utente: le bande grigie ai lati delle confezioni dipendevano da `.product-photo` con sfondo `#f8f8f3`. Impostato `#fff`; immagini originali e proporzioni conservate. Correzione raggruppata con catalogo e piano guidato nella release 0.8.0.

## Incremento 0.8.0 — verifica locale

Catalogo online e collegamento esplicito al piano implementati (vedi STEP7.md). 132 test e 4.096 confronti Swift passati. Flusso browser completo su archivio sintetico e mobile 390 px verificati. Sfondo foto prodotto bianco incluso nella release. Nessuna modifica alle cure reali e nessun backup operativo creato. Distribuita su HA il 16 novembre 2026: 52 file sorgente verificati, aggiornamento 0.8.0 e stato «In esecuzione» confermati in Safari. Foto prodotti visualizzate con contenitore bianco. Build e smoke ARM64/AMD64 passati. Nessun backup creato.

### Collaudo HA 0.8.0

Catalogo iNaturalist caricato nell’add-on reale: 12 specie della categoria Da interno, nomi italiani disponibili, fotografie autorizzate con attribuzione e link fonte. Le specie senza foto autorizzata mostrano un segnaposto. La risposta di ricerca corrente non include la famiglia per queste specie: l’interfaccia indica «Famiglia non disponibile», senza inventarla. Ricerca Ficus elastica verificata anche dal Mac. Prodotti: foto visibili e bande laterali bianche, inclusa la confezione Fosforo dello screenshot utente. Non applicati profili o piani alle piante reali. Pacchetto sorgente circa 224 KB; integrità, assenza foto e assenza credenziali native verificate.

## Incremento 0.9.0 — consolidamento archivio

Collezione leggera, dettaglio su richiesta e cronologia paginata. 140 test e benchmark su 100 piante/50.000 eventi: −99,04% di byte nella risposta della collezione. Browser mobile e modifica sintetica con conservazione del diario verificati. Dettaglio e limiti in STEP8.md. 53 file sorgente trasferiti e verificati; build/smoke ARM64/AMD64 passati. Installata e avviata la 0.9.0 su HA il 16 novembre 2026: cronologia 730 eventi attivi, pagina 2, filtro Balcone con 213 eventi e ritorno a pagina 1 verificati. Scheda e diario Ficus caricati correttamente. Nessuna modifica alle cure o ai piani reali. Nessun backup operativo creato.

## Priorità aggiornata — layout Verdant iOS

Su richiesta dell’utente, prima riallineare il layout al Verdant iOS attuale; desktop e altri step rimandati. Riferimenti nativi acquisiti su simulatore iPhone 17 Pro/iOS 26.5 con dati dimostrativi. Revisione locale di navigazione, panoramica, lista Piante/Ambienti, scheda, strumenti, calendario e prodotti; dettagli e differenze in IOS_LAYOUT.md. Anteprima interattiva in ios-preview.html. Prima anteprima locale; poi distribuita nella 0.10.0 (vedi incremento seguente), senza backup.

## Incremento 0.10.0 — layout iOS

Riallineamento iOS preparato per la distribuzione: lista e scheda, navigazione, strumenti raggruppati, prodotti e visualizzatore fotografico. Lista piante alfabetica su mobile; testi e immagini ingranditi. 140 test passati; verifiche browser su archivio temporaneo. Motore e credenziali conservati, nessun backup. Desktop e altri step rimangono rimandati. 55 file sorgente trasferiti e verificati. Build e smoke ARM64/AMD64 passati; pacchetto circa 246 KB, integro e privo di foto/credenziali native. 0.10.0 installata e in esecuzione su Home Assistant il 16 novembre 2026, senza backup. Collaudo Safari responsive 390 × 844: panoramica reale, prodotti, dettaglio Fosforo e foto a tutta schermata verificati; nessuna modifica alle cure. Safari riportato alla visualizzazione normale.

## Patch 0.10.1 — conferma attività

Guide native illustrate aperte in tutte le finestre di cura; nove asset ottimizzati WebP (462 KB totali). Scheda di conferma più leggibile, controllo salute con sintomi/aree e annotazioni nel formato nativo; salute selezionabile anche nei progressi. Inclusi icone piene iOS e abbassamento barra di 8 px. Verificati 140 test, confronto guide/diagnosi/stagionalità con Swift, build e smoke isolati ARM64/AMD64. Sorgenti trasferiti e confrontati SHA256 (67 file); pacchetto ZIP 716.877 byte. Installata e in esecuzione su Home Assistant il 16 novembre 2026, backup disattivato. Ingress Safari responsive 390×844 verificato su annaffiatura, concimazione e controllo salute: immagini visibili e campi disponibili, nessuna cura registrata. Archivio ancora a 18 piante; Safari ripristinato alla visualizzazione normale.

## Patch 0.10.2 — scheda e riepilogo iOS

Riepilogo completo e alternanza Scadenze/Frequenze, scadenza concime conservata con acqua/concime raggruppati, valori altezza/vaso e attività opzionali. Migliorati foto, didascalia, intestazione e pulsante del piano per modalità. Barra inferiore compatta: safe-area conservata fuori da Ingress e non duplicata nel contenitore HA. Nessuna modifica al motore AI o di cura.

Verificati 140 test, regressioni del riepilogo in Node, build e smoke isolati ARM64/AMD64, anteprima responsive 320/390/430 senza overflow; cambio rappresentazione da tastiera e apertura modifica piano manuale. Trasferiti e confrontati SHA256 68 file sorgente. 0.10.2 installata e in esecuzione su Home Assistant il 16 novembre 2026, con backup disattivato. Verificata Avocado in Ingress Safari responsive 390×844: Annaffiatura e Concimazione entrambe Tra 2 giorni; cambio alle frequenze Ogni 7 giorni e Ogni 21 giorni. Diario crescita, altezza 30 cm e vaso presenti. Nessuna cura/piano reale modificato, 18 piante conservate; Safari riportato alla vista normale. Posizione barra nel Companion fisico ancora da confermare.

## Patch 0.10.3 — sezioni secondarie e icone

Sezioni espandibili nella scheda iOS; cronologia delle cure separata dalla crescita, note e prodotto assegnato con foto. Dosaggio esplicito confrontato con il metodo Swift originale (40 casi standard più gli stessi 40 nel fallback Intl). Icone SVG piene estese a strumenti e cure, senza nuovi font o immagini nell’archivio. Corpi delle sezioni caricati uno alla volta e richieste misure invalidate quando si cambia pianta/scheda.

Verificati 140 pytest, riepilogo Node, browser mobile 320/390/430 e diario desktop 1440; build e smoke ARM64/AMD64 passati. Trasferiti e verificati SHA256 69 file sorgente; ZIP circa 0,73 MB, senza foto dell’archivio o credenziali. 0.10.3 installata e in esecuzione su Home Assistant il 16 novembre 2026, backup disattivato. Verificata Avocado in Ingress Safari responsive 390×844: pannello prodotto con fotografia reale Compo e dose 10 ml per litro d’acqua; Diario crescita con 6 aggiornamenti e cronologia distinta con 23 attività. Nessuna cura registrata o piano modificato durante il collaudo; collezione ancora a 18 piante.

### Preparazione i18n — dominio canonico (17 novembre 2026)

Le cure e gli stati di salute hanno ora codici canonici inglesi (`water`, `fertilize`, `prune`, `good`, `excellent`…) usati da pianificatore, apprendimento, trattamenti e Care Engine. Il modulo `backend/care_kinds.py` converte i valori italiani dell'archivio nativo e delle API.

Lo storage SQLite scrive i codici canonici; i payload già presenti vengono canonicalizzati in lettura e riscritti al primo salvataggio. L'API continua a restituire i valori italiani attesi dal frontend, quindi nessuna schermata cambia. La cronologia accetta filtri in entrambe le forme e legge i record precedenti alla migrazione.

Verifiche: **149 test**, 7.160 raccomandazioni Care Engine, 4.096 piani adattivi, 162 casi nativi e 1.536 combinazioni AI equivalenti al codice Swift. Prompt AI e note conservano i nomi italiani nativi. Nessun archivio operativo modificato.

### Preparazione i18n — infrastruttura P2 (17 novembre 2026)

Il frontend ha ora cataloghi italiano/inglese e un provider React con `t()`, plurali tramite `Intl.PluralRules` e formattazione di date e numeri con `Intl`. La lingua si sceglie in **Altro → Impostazioni** (`auto`, italiano, inglese) e viene ricordata nel browser; `auto` segue la lingua del documento o del browser, con fallback inglese.

Sono migrate le parti di struttura: navigazione desktop e mobile, titoli delle pagine, elenco e gruppi degli strumenti, impostazioni, footer, caricamento, dettaglio vuoto, paginazione e chiusura finestre. L'inglese è segnalato come beta perché i flussi di cura e le guide restano italiani fino a P3/P4.

Verifiche: build TypeScript/Vite passata, 95 chiavi allineate tra italiano e inglese, controllo di chiavi e segnaposto in CI (`scripts/check_i18n.mjs`). Nessun cambiamento al backend o ai dati.

### Internazionalizzazione P3a — giro e calendario (17 novembre 2026)

Etichette delle cure, scadenze e date usano la lingua attiva tramite `care-labels.ts`. Il **giro di cure** e il **calendario/cronologia** sono tradotti in italiano e inglese: selezione ambiente, conteggi, avvio, conferma, rinvio, salto, riepilogo, viste settimana/mese, filtri, paginazione e stati vuoti. I nomi di piante, ambienti e prodotti restano dati dell'utente.

Verifiche: 191 chiavi allineate, build TypeScript/Vite, 149 test backend e prova browser su archivio sintetico con giro, calendario e cronologia in inglese, senza errori console. Restano da migrare home, scheda pianta, prodotti, trattamenti, moduli di cura, guide e messaggi di errore del backend. Nessun dato reale modificato.

### Internazionalizzazione P3b/P3c — moduli, prodotti, trattamenti (17 novembre 2026)

Tradotti i moduli di cura (conferma e modifica attività, crescita, misure), la testata della scheda pianta, i prodotti su desktop e mobile con il relativo editor, e i trattamenti con pianificazione, modifica, interruzione e ripresa. Stati di salute, sintomi e aree usano etichette tradotte senza cambiare i valori salvati.

Le API aggiungono un `code` stabile agli errori (`conflict`, `not_found`, `validation`, `forbidden`, `too_large`, `remote`). Il frontend usa messaggi inglesi generici per i codici noti; i dettagli specifici restano italiani finché non verranno associati a codici dedicati.

Verifiche: 393 chiavi allineate, build TypeScript/Vite, **150 test backend** (nuovo test sui codici errore) e prova browser in inglese su prodotti, editor prodotto, trattamenti, moduli di cura e testata pianta. Restano home, dettaglio iOS completo, testi lunghi e messaggi specifici. Nessun dato reale modificato.

### Internazionalizzazione P4a — home e lingua server (17 novembre 2026)

Tradotti home e riepilogo Oggi (saluto, data localizzata, hero, statistiche, attività e proposte AI) e l'elenco piante (ricerca, filtri, modalità Piante/Ambienti, conteggi e stato vuoto).

Aggiunta la preferenza lingua lato server: opzione `language` dell'add-on, endpoint `GET/PUT /api/preferences` e stato SQLite. Il frontend invia la lingua effettiva; notifiche delle proposte AI e istruzioni di risposta al provider usano italiano o inglese. La cache dei consigli include il prompt, quindi il cambio lingua invalida le risposte precedenti.

Verifiche: 450 chiavi allineate, build TypeScript/Vite, **151 test backend** (nuovo test su preferenze e validazione), nessun dato reale modificato. Restano dettaglio iOS completo, guide, diagnosi, testi lunghi e documentazione inglese.

### Internazionalizzazione P4b — iOS, guide e osservazioni (17 novembre 2026)

Tradotto il dettaglio iOS: riepilogo, scadenze/frequenze, azioni rapide, dati della pianta, sezioni espandibili e prodotto assegnato. Le nove guide di cura hanno una versione inglese completa (`care-guides.en.json`) con immagini condivise; guida pratica e ritmo stagionale ricevono valori e consigli inglesi dal backend.

La diagnosi guidata mostra sintomi e testo in inglese e invia la lingua al server, che restituisce il consiglio nella stessa lingua. Osservazioni, piano intelligente, azioni, motivazioni, dati mancanti e stima di asciugatura sono tradotti.

Verifiche: 623 chiavi allineate, build TypeScript/Vite, 151 test backend, prova browser su guide e diagnosi in inglese. Restano documentazione inglese e revisione editoriale delle traduzioni lunghe.

### Internazionalizzazione P5 — documentazione e rifiniture (17 novembre 2026)

Aggiunta la documentazione inglese in `docs/en/` (indice, installazione, stato, architettura) e collegata dai README. Circa 30 messaggi di errore comuni hanno una traduzione inglese specifica; i casi non mappati usano i codici generici. Il bundle frontend è stato diviso in chunk React, icone e QR: il principale scende a circa 441 KB e non supera più la soglia di avviso.

Verifiche: 623 chiavi allineate, build frontend, **151 test backend** e controllo di parità in CI. Nessun dato reale modificato.

### Rifiniture i18n finali (17 novembre 2026)

Tradotte le tassonomie delle piante (categoria, esposizione, materiale del vaso, posizione e frequenza), l'editor della pianta, i metadati dell'add-on e la documentazione inglese. Il pianificatore adattivo restituisce una motivazione inglese sintetica quando la lingua è `en`; l'apprendimento e il motivo degli interventi di trattamento sono localizzati. I messaggi backend molto lunghi già salvati negli archivi restano nella lingua originale.

Verifiche: 685 chiavi allineate, build frontend, 151 test backend e prova browser. Nessun dato reale modificato.

### Prossimi confronti iOS

1. Grafico della timeline e indice salute nativo: portare il calcolo, senza simulare valori.
2. Moduli di crescita e album salute: confronto dei flussi completi e delle fotografie.
3. Luxmetro e percorso fotocamera: verificare capacità del browser e qualità delle misure prima di proporlo come equivalente nativo.
4. Collaudo Companion fisico, poi passare agli altri dispositivi come richiesto.

Restano separati gli step originari 5/6 (collaudo sensori e applicazione AI su dati reali) e 8 (ripristino su macchina isolata). Nessun backup Home Assistant durante lo sviluppo; DB esterno rinviato.
