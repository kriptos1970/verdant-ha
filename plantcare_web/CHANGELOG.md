# 0.11.23 — icona dell’azione sulle immagini degli eventi

- Nelle card delle cure e nella cronologia l’immagine della pianta mostra in basso a destra una piccola icona dell’azione da compiere: annaffiatura, concimazione, rotazione, controllo salute, diario di crescita e le altre cure.
- L’icona usa il colore della categoria ed è decorativa per l’accessibilità: l’azione resta scritta nella card.
- 224 test backend, 1014 chiavi i18n, build frontend.

# 0.11.22 — saluto della Home su una sola riga

- Su telefono l’intestazione della Home non divide più “Buongiorno 🌿” su due righe: il saluto resta su una riga e la colonna meteo/icona non occupa più metà della testata.
- Il meteo compatto mostra solo la temperatura; la località resta nell’etichetta accessibile.
- Sotto i 360 px il saluto usa una scala leggermente ridotta per evitare sovrapposizioni; 390, 375, 360 e 320 px verificati senza ritorno a capo.
- Nessun cambiamento a contenuti, flussi o dati; build frontend.

# 0.11.21 — modalità del motore di cura più chiara

- In **Impostazioni → Motore di cura** la modalità attiva è ora indicata da un pallino e dalla dicitura “Modalità attiva nell’add-on”; le due modalità sono elencate separatamente e quella corrente è evidenziata.
- La descrizione non inizia più con “Solo osservazione (shadow)” quando è attiva la modalità operativa: il valore mostrato e la spiegazione non si confondono.
- Dopo una modifica dell’opzione `care_engine_mode` nell’add-on, riavviare l’add-on; la web UI aggiorna il valore entro un minuto o al ritorno sulla scheda.
- 224 test backend, 1014 chiavi i18n, build frontend.

# 0.11.20 — sfondo verde tenue

- Lo sfondo della pagina usa un verde tenue (`--vc-canvas`); pannelli, schede e finestre restano bianchi, così le sezioni si separano visivamente come nell’app nativa.
- Su telefono anche l’intestazione del dettaglio segue lo sfondo della pagina, mentre le schede cura restano bianche.
- Nessun cambiamento a contenuti, flussi o dati; 224 test backend, 1013 chiavi i18n, build frontend.

# 0.11.19 — foto nel layout precedente dell’attività

- L’attività **Diario di crescita** torna al layout di conferma precedente — data, rinvio, stato di salute e note — con l’aggiunta di **Scatta una foto** e **Scegli fotografie**.
- Le foto vengono salvate nella voce di crescita; l’evento “Aggiorna progressi” resta registrato nella cronologia. Corregge il percorso introdotto nella 0.11.18.
- 224 test backend, 1013 chiavi i18n, build frontend.

# 0.11.18 — foto nel diario di crescita e dipendenze sicure

- Dalla sezione **Attività**, l’attività **Diario di crescita** apre ora l’editor del diario invece del form generico della cura: “Scatta una foto” usa la fotocamera, “Scegli fotografie” apre la libreria; le immagini vengono salvate nella voce di crescita e l’attività viene registrata.
- Aggiornati **Pillow 13.0.0** e **python-multipart 0.0.31** per correggere le vulnerabilità segnalate.
- `pip-audit` sul lock aggiornato e `npm audit` non segnalano più vulnerabilità note.
- 223 test backend, 1013 chiavi i18n.

# 0.11.17 — validazione più chiara, niente banner generico

- Il banner globale “Controlla i dati inseriti.” non viene più mostrato quando la risposta non contiene un dettaglio utile o quando l’errore arriva da un form modale; l’errore specifico resta nel form.
- Il backend di validazione restituisce ora il **campo** e il **motivo** (ad esempio `name: Campo obbligatorio`), così un eventuale banner è azionabile.
- Aggiunti limiti `maxLength` ai testi lunghi dell’editor pianta, delle note cura, dei prodotti e della crescita per evitare rifiuti evitabili.
- 223 test backend, build frontend.

# 0.11.16 — profilo di esperienza del coltivatore

- Nuova impostazione **Esperienza del coltivatore**: principiante, intermedio, esperto, professionista (default intermedio), salvata nelle preferenze dell’app e visibile in Impostazioni.
- Apprendimento Verdant: il passo massimo è 1, 2, 3 o 4 giorni secondo il profilo; con almeno due rinvii onorati (o due anticipati) il passo è pari al numero di rinvii, fino al massimo. I ritardi senza rinvio non accelerano; restano il limite ±30% e il target.
- L’analisi AI giornaliera e l’assistente ricevono `experienceLevel`; il prompt calibra prudenza e peso dei rinvii. `contextVersion` portato a 4.
- Il PUT delle preferenze unisce lingua ed esperienza senza sovrascriversi.
- 222 test backend, 1012 chiavi i18n.

# 0.11.15 — apprendimento adattivo ai rinvii

- L’apprendimento Verdant non usa più un passo fisso di ±1 giorno: parte da 1 e sale a **2 giorni** quando almeno **2 rinvii onorati** (con almeno un giorno di rinvio) confermano un ritmo più lungo, oppure quando almeno **2 rinvii anticipati** indicano un ritmo più corto.
- I **ritardi senza rinvio** restano evidenza debole e non accelerano l’apprendimento; il limite ±30% e il mancato superamento del target restano invariati.
- `careLearning` espone `adaptiveStepDays`, `honoredPostponements`, `earlyPostponements`, `medianDeferredDays` e `lateGapsWithoutPostponement`.
- 220 test backend, build frontend.

# 0.11.14 — contesto AI con rinvii e località

- L’analisi AI giornaliera riceve ora la **località** (dal piano o da quella predefinita) e `careTiming`: intervalli osservati, rinvii intenzionali con data, nuova data e nota, e ritardi senza rinvio.
- Il prompt distingue esplicitamente **rinvii e ritardi**: i primi sono scelte del coltivatore, i secondi no; i rinvii onorati e coerenti pesano come evidenza del ritmo reale.
- Anche l’assistente della scheda pianta riceve località e rinvii recenti; `contextVersion` portato a 3 per non riusare i consigli precedenti.
- 217 test backend, build frontend.

# 0.11.13 — pulsante Completa compatto su desktop

- Nelle card della sezione Attività su desktop il pulsante **Completa** ha ora una larghezza proporzionata di 200 px (massimo 100% della card) e altezza 44 px, invece di occupare tutta la riga.
- Su telefono il pulsante resta a tutta larghezza.
- 215 test backend, build frontend.

# 0.11.12 — conferma cura senza scorrimento orizzontale

- Su telefono la finestra che si apre con **Completa** accetta solo lo scorrimento verticale: overflow orizzontale nascosto, overscroll orizzontale disattivato e `touch-action` limitata a pan verticale e pinch-zoom.
- Nomi pianta, passaggi della guida e motivazioni lunghe vanno a capo; campi e pulsanti non superano la larghezza del pannello.
- Verifica a 320/390 px con un nome pianta molto lungo: nessun overflow orizzontale.
- 215 test backend, build frontend.

# 0.11.11 — maniglia del pannello destro sempre disponibile

- La maniglia del pannello dettaglio è ora presente anche quando il pannello è nello stato vuoto (prima compariva solo con una pianta aperta), quindi la colonna destra si ridimensiona subito.
- Z-index delle maniglie alzato per evitare sovrapposizioni con il contenuto del dettaglio.
- 215 test backend, build frontend.

# 0.11.10 — pannelli desktop ridimensionabili

- Nella versione desktop la **colonna sinistra** e il **pannello del dettaglio** si ridimensionano trascinando il bordo; maniglia visibile al passaggio del mouse, doppio clic per tornare alla larghezza predefinita.
- Larghezza memorizzata per browser, frecce da tastiera, limiti: colonna 190–420 px, dettaglio 320–720 px, almeno 420 px per il contenuto.
- Le maniglie sono disponibili solo sopra i 1000 px; su telefono e tablet resta il layout esistente.
- 215 test backend, build frontend.

# 0.11.9 — nome Verdant

- Add-on, pannello laterale, web app, titolo della pagina, notifiche e messaggi visibili ora usano il nome **Verdant**.
- Slug dell’add-on, cartella `/data`, database, percorsi delle foto, formato dei backup e identificatori interni restano invariati: aggiornamento e dati sono preservati.
- 215 test backend, build frontend.

# 0.11.8 — risposte AI in Markdown

- Le risposte dell’assistente AI nel riquadro verde vengono renderizzate come Markdown: titoli, paragrafi, grassetto e corsivo, elenchi puntati e numerati, citazioni, codice e tabelle GFM.
- Il renderer viene caricato solo quando serve ed è separato dal bundle principale; non interpreta HTML grezzo.
- Stesso comportamento per Gemini e OpenAI, che restituiscono lo stesso campo `summaryMarkdown`.
- 215 test backend, build frontend.

# 0.11.7 — etichette QR con lo slug dell’add-on

- Le etichette QR/NFC usano lo slug dell’add-on corrente (`local_plantcare_web` per l’installazione locale, `309d34f7_plantcare_web` per quella da repository) invece del valore fisso `local_plantcare_web`.
- Il parser delle etichette accetta qualsiasi percorso `/app/<slug>/plant/<id>`, mantenendo compatibili le etichette già stampate.
- 215 test backend.

# 0.11.6 — migrazione assistita tra add-on

- Nuovo import guidato per spostare l’archivio su un add-on con slug diverso (locale → repository): se `/data` è vuoto e esiste `/share/plantcare/migrate/import-request`, l’app importa `/share/plantcare/migrate/plantcare.sqlite` all’avvio.
- Il database viene validato come SQLite e sostituito atomicamente; il file di migrazione resta in `/share` per il rollback e la richiesta viene consumata una sola volta.
- 215 test backend.

# 0.11.5 — scelta visuale del fertilizzante

- Nell’editor pianta il fertilizzante si sceglie da un **elenco visuale** con miniatura, nome, marca, categoria e forma; “Nessun fertilizzante” resta la prima voce.
- Rimosso il campo libero **“Tipo di fertilizzante”**: il tipo viene derivato dal prodotto scelto, anche lato backend, e non è più modificabile.
- Sono proposti solo i prodotti fertilizzanti (Fertilizzante, Biostimolante, Ammendante, Radicante), più l’eventuale prodotto già associato; la dose compare solo con un prodotto selezionato.
- 213 test backend, 1001 chiavi i18n.

# 0.11.4 — un solo interruttore per il motore di cura

- La modalità del motore di cura ha ora **una sola fonte**: l’opzione `care_engine_mode` nella configurazione dell’add-on, con default **Operativo**.
- Rimossa la preferenza salvata dal web che poteva divergere dalla configurazione: niente più doppio valore shadow/active.
- In **Impostazioni → Motore di cura** la web UI mostra la modalità effettiva e spiega entrambe le modalità e dove cambiarle; l’endpoint di scrittura è stato rimosso.
- 212 test backend, 1000 chiavi i18n.

# 0.11.3 — editor pianta web-first

- Editor **Nuova pianta / Modifica pianta** riorganizzato per il web, senza copiare il form nativo: foto e riconoscimento in alto, poi i dati essenziali sempre visibili (nome, specie, famiglia e categoria, ambiente ed esposizione, piano, annaffiatura e ultima annaffiatura).
- Le informazioni secondarie passano a cinque sezioni richiudibili con riepilogo: Posizione e profilo, Vaso e substrato, Frequenze e concimazione, Attività aggiuntive, Altre informazioni.
- Una sola barra **Annulla / Salva pianta** sticky in fondo al dialog, con rispetto della safe area; rimossa la doppia barra in testa.
- Griglie a due colonne per i campi brevi e una colonna sotto 360 px; contenuto ridotto da circa 4.038 px a circa 1.392 px a 390 px.
- I campi obbligatori restano nelle sezioni sempre visibili; un controllo non valido dentro una sezione chiusa la apre e riceve il focus.
- Diario della pianta e editor pianta con riquadri verde tenue: crescita, cronologia, linea del tempo, sezioni e riconoscimento Pl@ntNet.
- 212 test backend, 999 chiavi i18n.

# 0.11.2 — parità funzionale, token visivi e riconoscimento

- Collezione: cestino con ripristino a 30 giorni, azioni rapide sulle card, paginazione e layout telefono compatto.
- Prodotti: filtro per categoria, “Registra utilizzo”, date di acquisto/scadenza.
- Dettaglio pianta: spostamento con ricalcolo del piano, sicurezza aggiornabile, grafico attività, cronologia separata dal diario di crescita.
- Impostazioni: località predefinita con ricerca Open-Meteo e stato del ricalcolo meteo.
- Cure: attività raggruppate, rinvio dalla riga, cronologia con filtri richiudibili e motivazioni della cura.
- Misure: sorgente e affidabilità nella tabella, misure native senza duplicati.
- Motore di cura operativo: può solo rinviare l’annaffiatura quando il terreno è umido e la misura è affidabile.
- Editor pianta riordinato come il nativo, con riconoscimento Pl@ntNet nel form e compilazione automatica di nome, specie, famiglia e categoria.
- Icone piene, token visivi in `tokens.css`, layout Home/Cure/Cronologia allineato a Verdant.
- Pulizia foto non utilizzate, con protezione dei caricamenti recenti.
- Grafici e analisi, fase 1: indice salute per pianta portato dal nativo (`healthAssessment`), con ritardi di acqua e concime, ultima osservazione, controlli e misure di luce; normalizzazione 20–100 e consigli con codici traducibili.
- `_health` incluso nella scheda pianta e nella collezione sintetica; endpoint `/api/analytics?days=30|90|365` e `/api/plants/{id}/timeline` per unire eventi e misure.
- 212 test backend, 988 chiavi i18n.

# 0.11.1 — caricamento fotografie

- La lista piante usa miniature da 480 px invece degli originali: il trasferimento iniziale scende da decine di MB a poche centinaia di KB.
- Foto e miniature sono contenuti indirizzati per hash e ora hanno `Cache-Control` immutabile ed ETag; il middleware non forza più `no-store` sulle immagini.
- Generazione miniature più rapida con draft JPEG e scrittura atomica, protetta da lock.
- 152 test backend.

# 0.11.0 — italiano/inglese e codici canonici

- Infrastruttura i18n italiano/inglese: cataloghi delle stringhe, selettore lingua in Impostazioni, prime schermate tradotte e controllo automatico delle traduzioni in CI.
- Giro di cure, calendario e cronologia tradotti in italiano e inglese, con plurali per scadenze e conteggi.
- Moduli di cura, testata della scheda pianta, prodotti, editor prodotto e trattamenti tradotti.
- Errori API con codice stabile; messaggi inglesi generici per i codici noti.
- Home e elenco piante tradotti; preferenza lingua lato server per notifiche e risposte AI.
- Dettaglio iOS, nove guide di cura, diagnosi, osservazioni e piano intelligente tradotti in inglese.
- Documentazione inglese in `docs/en/`, messaggi di errore comuni tradotti e code-splitting del frontend.
- Tassonomie delle piante, editor, metadati dell'add-on e motivazioni generate del piano tradotti.
- Codici canonici per tipi di cura e stati di salute nel backend, con API e backup ancora nel formato italiano per compatibilità.

# 0.10.3 — sezioni della scheda iOS

- Sezioni espandibili nella scheda, con icone circolari colorate: piano, osservazioni, cronologia, profilo, crescita, misure, sicurezza, album, trattamenti e AI.
- Cronologia delle cure e diario di crescita separati su iOS; prodotto assegnato e note consultabili nella scheda.
- Dose del prodotto calcolata con la frazione salvata e gli stessi arrotondamenti del nativo; 40 casi confrontati con Swift, anche con fallback Intl.
- Icone piene anche negli strumenti e nelle altre attività di cura; profilo botanico consultabile dal pannello Profilo e cura.
- Contenuti montati solo per la sezione aperta; risultati di misure obsolete scartati dopo cambio pianta o scheda.

# 0.10.2 — scheda pianta iOS

- Riepilogo completo con cambio Scadenze/Frequenze, Controllo, Diario crescita, Altezza e Vaso; testi e spazi riallineati al riferimento iOS.
- Concimazione mostrata anche quando l’attività operativa è raggruppata con l’annaffiatura: lettura delle scadenze separate del server, senza cambiare il motore.
- Foto, contrasto della didascalia e intestazione rifiniti; pulsante del piano distinto per Manuale/Intelligente/AI.
- Barra inferiore più compatta e senza sommare nuovamente l’area sicura nel contenitore Home Assistant; area sicura conservata fuori da Ingress.

# 0.10.1 — finestre di cura iOS

- Icone iOS a sagoma piena per navigazione, azioni della pianta, cure e riepilogo; indicatori del riepilogo su fondi circolari colorati. SVG originali, senza font aggiuntivi.

- Barra inferiore iOS abbassata di 8 px, conservando l’area sicura dell’iPhone.

- Finestre di tutte le cure riallineate a Verdant: guida aperta con sequenze fotografiche native, passaggi numerati e icone; immagini WebP condivise (462 KB totali).
- Conferma attività e moduli più leggibili; controllo salute con sintomi, aree, possibile problema e prossimo intervento nelle note; selezione salute anche per i progressi.

# 0.10.0 — layout iOS

- Riallineamento visivo a Verdant iOS: navigazione, lista Piante/Ambienti, scheda con foto e riepilogo, strumenti raggruppati e prodotti con dettaglio separato.
- Testi e immagini ingranditi per iPhone; moduli touch e settimana scorrevole.
- Foto di piante e prodotti ingrandibili a tutta schermata; lista piante ordinata alfabeticamente su mobile.
- 140 test e build frontend passati; nessuna modifica a motore AI o regole di cura.

# 0.9.0

- Collezione leggera: cronologia, crescita e album completi caricati solo all’apertura della pianta.
- Cronologia generale paginata, con filtri sul server e date nel fuso configurato.
- Diario con 50 cure e 12 storie di crescita per pagina; tutti i dati rimangono conservati.
- Conteggi analisi preservati e salvataggio delle schede incomplete bloccato.
- 140 test; benchmark con 100 piante e 50.000 eventi: risposta iniziale della collezione ridotta del 99,04%.

# 0.8.0

- Catalogo botanico iNaturalist con ricerca, quattro categorie native, paginazione e fotografie con licenza e attribuzione; cache limitata ai metadati.
- Preparazione della scheda dal catalogo senza applicazione automatica delle cure.
- Collegamento esplicito di Open Plantbook/Perenual al pianificatore, con anteprima, conferma delle corrispondenze approssimative e controllo di versione.
- Motore adattivo e provider AI conservati.

- Sfondo bianco anche nel contenitore delle fotografie dei prodotti, eliminando le bande grigie ai lati delle immagini.

# 0.7.0

- Sfondo principale bianco, incluso in questa release insieme alle nuove funzioni.
- Album salute con quattro inquadrature, annotazioni e confronto precedente; conferma, controllo versione e salvataggio idempotente con evento salute nativo.
- Etichette QR/NFC generate localmente, download/stampa e apertura della scheda tramite collegamento Home Assistant stabile senza token Ingress nell’etichetta.
- Open Plantbook con credenziali lato server e fallback Perenual; campi botanici e provenienza visibili.
- 123 test passati; flusso album, QR, collegamento nel contenitore HA simulato e layout mobile verificati.

# 0.6.1

- Mostrate le fotografie dei prodotti già importate, con apertura dell’immagine originale e icona di ripiego se non disponibile.
- Anteprima e caricamento della foto nell’editor prodotto.
- Nessuna reimportazione o duplicazione delle immagini esistenti.

# 0.6.0

- Nove guide operative native, accessibili da Altro e dalle finestre di registrazione delle cure.
- Guida pratica della pianta con luce, temperatura, umidità, terreno, concimazione, potatura, rinvaso e propagazione.
- Ritmo stagionale indicativo con gli stessi valori del nativo, separato dal calendario operativo.
- Controllo salute guidato con sei sintomi e priorità native; nessuna chiamata AI né scrittura di cure.
- 103 test passati; 63 combinazioni di sintomi e 288 valori stagionali confrontati con esecuzione Swift; testi delle nove guide verificati.

# 0.5.0

- Riconoscimento Pl@ntNet con consenso esplicito, parte fotografata e cinque candidati; immagine temporanea JPEG a 2.000 pixel senza metadati.
- Bozza della pianta compilata da un risultato, con fotografia salvata solo alla conferma della scheda.
- Biblioteca delle specie importate con ricerca per nome, famiglia e sinonimi.
- Consultazione Perenual con provenienza, corrispondenze approssimative, schede sintetiche e dati di sicurezza mancanti distinti da «non tossica».
- Chiavi Pl@ntNet/Perenual nelle opzioni Home Assistant, mai esposte al browser.
- 95 test passati; flusso completo verificato con servizi simulati e layout mobile a 390 px.

# 0.4.3

- Data e provenienza del clima salvato esplicite nel contesto AI e nell’interfaccia.
- Istantanee climatiche distinte dal meteo attuale anche nell’analisi giornaliera.
- Consigli precedenti da rigenerare, protetti da applicazione e cache obsolete.
- 77 test passati e build frontend verificata.

# 0.4.2

- Importazione con riuso delle foto già presenti nella cartella configurata, verificate tramite nome e SHA256.
- Le fotografie eliminate nel diario non sono considerate foto attive mancanti; i tombstone sono conservati.
- Supporto agli archivi fotografici grandi senza reinviare le immagini attraverso il browser.
- 74 test automatici passati; build ARM64/AMD64 verificate.

# 0.4.1

- Errori dei servizi esterni restituiti con messaggi sicuri e codici compatibili con Home Assistant Ingress, evitando la perdita del dettaglio dietro un generico 502.
- Diagnosi distinte per chiave non valida/scaduta, restrizioni di accesso, disponibilità geografica, modello assente, quota e connessione.
- Nessun testo grezzo del provider o credenziale nei messaggi mostrati all’utente.
- 70 test automatici passati, build ARM64/AMD64 verificate.

# 0.4.0

- Assistente botanico con ultimo consiglio conservato, cache delle richieste identiche e applicazione selettiva delle cinque attività.
- Anteprima server del piano effettivo, note aggiunte alla scheda, conferme idempotenti e protezione dalle modifiche concorrenti.
- Schema strutturato e frequenze stabili allineati al nativo; revisione AI registrata con il valore nativo corretto.
- Catalogo OpenAI/Gemini con filtri nativi, paginazione Gemini e scelta del modello; chiavi conservate nelle opzioni Home Assistant.
- Notifiche persistenti Home Assistant per proposte e applicazioni automatiche. Gli errori di notifica non eliminano i risultati.
- Rifiuti, risposte incomplete, JSON malformato e credenziali non valide gestiti senza applicare dati parziali.
- 61 test automatici e 1.536 confronti con il codice Swift originale sull’applicazione selettiva.

# 0.3.0

- Piano intelligente con anteprima, applicazione esatta della proposta, controllo versione e scadenza dell’anteprima.
- Pianificatore nativo: specie/famiglia, esposizione, emisfero, stagione, temperatura, umidità, pioggia, profilo botanico salvato, soglie succulente e allineamento del concime.
- Meteo Open-Meteo opzionale e aggiornamento giornaliero; piani importati conservati finché l’utente non abilita il meteo. Ricalcoli falliti non alterano il piano.
- Apprendimento dalle annaffiature completate, con passo prudente e conservazione delle revisioni manuali/AI.
- Care Engine in modalità shadow per acqua, luce, nutrizione, temperatura e umidità: consigli, confidenza, dati mancanti e controlli di sicurezza. Nessuna modifica automatica delle scadenze dai sensori.
- Analisi delle curve di asciugatura, cicli comparabili, stima e incertezza; invalidazione dopo cambio substrato/vaso e distinzione delle sorgenti.
- Freschezza basata sull’osservazione originale HA; campionamenti identici deduplicati e unità/valori manuali validati.
- 4.096 piani, 7.160 raccomandazioni e 20 serie di asciugatura confrontati con esecuzione del codice Swift originale.

# 0.2.0

- Giro di cure guidato per ambiente, con avanzamento stabile, rinvio, salto e riepilogo.
- Cicli di trattamento: prodotto, dose, frequenza, applicazioni, data finale; modifica, interruzione reversibile e ripresa.
- Conteggi coerenti dopo modifica/eliminazione degli eventi e conservazione delle applicazioni importate.
- Protezione dalle registrazioni duplicate e dalle attività cambiate durante il giro.
- Calendario settimanale/mensile e cronologia globale filtrabile.
- Proiezione delle scadenze e raggruppamento acqua/concime allineati al nativo; esclusione dei prodotti fogliari.
- Confronto visivo con PlantCare macOS e adeguamento di palette, panoramica e disposizione a colonne.
- Correzione delle date Swift startDate/endDate nell’importazione dei cicli.

# 0.1.0

- Primo incremento: archivio, interfaccia responsive, calendario e diario delle cure.
- Importazione backup nativi v1–v3 e backup ZIP con fotografie separate.
- Foto su percorso configurabile, miniature, deduplicazione e statistiche spazio.
- Sensori Home Assistant autorizzati, mapping pianta/stanza e campionamento.
- Assistente OpenAI/Gemini, prompt nativi e proposte AI con controlli di validità.
- Motore avanzato e ricalcolo adattivo completo ancora in trasferimento.
