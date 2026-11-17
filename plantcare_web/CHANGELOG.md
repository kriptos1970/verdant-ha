# Non pubblicato

- Infrastruttura i18n italiano/inglese: cataloghi delle stringhe, selettore lingua in Impostazioni, prime schermate tradotte e controllo automatico delle traduzioni in CI.
- Giro di cure, calendario e cronologia tradotti in italiano e inglese, con plurali per scadenze e conteggi.
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
