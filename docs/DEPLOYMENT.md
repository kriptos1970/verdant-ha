# Installazione Home Assistant — 15 novembre 2026

- Versione installata: **0.2.0**, applicazione locale `local_plantcare_web`.
- Sorgenti copiati nella condivisione `addons/plantcare_web`: SHA256 coincidenti per tutti i 33 file trasferiti.
- Installazione e costruzione container eseguite da Home Assistant.
- Stato osservato: **In esecuzione**. Avvio automatico attivo.
- Collegamento **PlantCare** abilitato nella barra laterale.
- Dashboard aperta e verificata in Safari tramite Ingress: versione 0.2.0, archivio vuoto, nessun dato dimostrativo.
- Database SQLite e foto nelle directory predefinite persistenti `/data` e `/data/photos`. Nessuna migrazione a database esterno.
- Nessun archivio Apple importato e nessuna chiave AI trasferita.

Prova visiva: [dashboard installata](screenshots/0.2.0/home-assistant-installed.jpg).

Questa verifica copre installazione, avvio e caricamento della dashboard. Importazione dell’archivio personale, sensori reali, provider AI, aggiornamento e ripristino richiedono collaudi successivi.

## Aggiornamento 0.3.0 — 15 novembre 2026

- Completato l’aggiornamento dell’applicazione locale `local_plantcare_web` tramite Supervisor.
- Verificati con SHA256 tutti i 37 file sorgenti trasferiti via condivisione addons.
- Versione **0.3.0** e dashboard caricate correttamente attraverso Home Assistant Ingress in Safari.
- Archivio operativo ancora vuoto; nessun dato di collaudo copiato sul server. Nessuna chiave AI o località personale inviata a provider esterni.
- Percorsi persistenti e schema SQLite conservati. MariaDB esterno rimandato.
- Backup parziale `PlantCare-prima-0.3.0` (slug `2f9d6b48`) già completato prima della successiva indicazione dell’utente.
- **Preferenza dell’utente: durante la fase di sviluppo non creare ulteriori backup.**

Prova visiva: [dashboard 0.3.0 installata](screenshots/0.3.0/home-assistant-installed.jpg).

Le prove delle nuove funzioni sono state effettuate su dati sintetici separati; il collaudo con archivio personale e sensori reali rimane da eseguire.

## Aggiornamento 0.4.0 — 15 novembre 2026

- Step 6 implementato e collaudato: 61 test, 1.536 confronti Swift, build e smoke ARM64/AMD64.
- Trasferiti 39 file nella cartella locale dell’add-on e verificati con SHA256.
- Completato l’aggiornamento tramite Supervisor dopo la riapertura della sessione autenticata.
- Versione **0.4.0** e dashboard verificate tramite Ingress in Safari. Archivio operativo ancora vuoto; nessun dato dimostrativo copiato sul server.
- Prova visiva: [dashboard 0.4.0 installata](screenshots/0.4.0/home-assistant-installed.jpg).
- Nessun backup Home Assistant creato; chiavi/provider non modificati. Dati e risposta simulata di collaudo conservati soltanto in `/private/tmp/plantcare-step6-preview`.

## Correzione catalogo 0.4.1 — 15 novembre 2026

- Rilevati provider `none` e valore `gemini` nel campo del modello: corretti in provider Gemini e modello vuoto.
- La chiave iniziale è stata rifiutata da Google con HTTP 400 / `API_KEY_INVALID`.
- Installata la 0.4.1 con messaggi di errore sicuri e compatibili con Ingress; 70 test e build/smoke ARM64/AMD64 passati. 40 file trasferiti verificati con SHA256.
- Su istruzione esplicita dell’utente, copiata la chiave Gemini da `c7ff4cbc_verdant_server` a `local_plantcare_web` tramite Supervisor, usando soltanto pipe all’interno del server. Nessuna chiave visualizzata o salvata nei sorgenti/file di sviluppo. Altre opzioni conservate.
- Riavvio completato. Versione 0.4.1 verificata e catalogo Gemini reale caricato nell’interfaccia con selezione modello disponibile; riferimento corrente `gemini-3.5-flash-lite`.
- Nessuna richiesta di generazione AI o backup Home Assistant eseguita.

Prova visiva: [catalogo Gemini funzionante](screenshots/0.4.1/gemini-catalog.jpg).

## Importazione reale 0.4.2 — 15 novembre 2026

- Add-on aggiornato e avviato; fotografie configurate in `/share/plantcare/photos`.
- Importate 18 piante, 7 prodotti, 20 profili botanici, 731 eventi (730 attivi), 158 misure e 124 fotografie distinte (375 MB).
- Importazione tramite ZIP di soli metadati, con fotografie trasferite separatamente e validate SHA256. Nessuna foto attiva mancante nell’anteprima.
- Verificate in Ingress collezione con foto, scheda/diario Ficus, prodotti e calendario della settimana successiva.
- Originali Verdant invariati; nessun backup Home Assistant creato e nessuna generazione AI eseguita.

Prova visiva: [collezione importata](screenshots/0.4.2/imported-collection.jpg). Dettagli in [IMPORT.md](IMPORT.md).

## Correzione contesto AI 0.4.3 — 15 novembre 2026

- 77 test, build frontend e build/smoke ARM64/AMD64 passati.
- 40 file trasferiti nella cartella add-on e verificati SHA256. Nessuna modifica ad archivio, foto o opzioni.
- Supervisor: aggiornamento 0.4.2 → 0.4.3 completato con «Conserva il backup» disattivato.
- Versione 0.4.3 installata e in esecuzione. Ingress verificato; vecchio consiglio Ficus bloccato e nuovo consiglio Gemini generato con data del clima salvato esplicita. Piano non modificato. [Prova visiva](screenshots/0.4.3/dated-climate-advice.jpg).

## Incremento 0.5.0 — 15 novembre 2026

- Riconoscimento fotografico e biblioteca botanica: prima parte dello step 7.
- 95 test, build frontend e build/smoke ARM64/AMD64 passati. Flusso browser locale con servizi simulati verificato fino al salvataggio; mobile 390 px senza overflow.
- 42 file trasferiti e verificati con SHA256. Aggiornamento completato tramite Supervisor con backup disattivato. Versione 0.5.0 installata e in esecuzione.
- Ingress verificato: catalogo reale di 20 specie, filtro Ficus e configurazione mancante per Pl@ntNet/Perenual. Nuove chiavi non copiate; nessuna chiamata live ai nuovi provider. Gemini e opzioni fotografiche conservati.
- Nessuna nuova pianta, fotografia o cura scritta nell’archivio operativo. Nessun backup creato.

[Catalogo installato](screenshots/0.5.0/home-assistant-library.jpg). [Funzioni e limiti dell’incremento](STEP7.md).

## Incremento 0.6.0 — guide e controllo salute

103 test e build frontend passati. Confronto Swift: 63 combinazioni di sintomi e 288 valori stagionali; testi delle nove guide verificati. Flusso browser locale desktop/mobile 390 px verificato senza registrare cure. 45 file trasferiti e verificati SHA256. Aggiornamento completato in Supervisor con backup disattivato. Versione 0.6.0 e guide verificate in Ingress.

## Correzione 0.6.1 — foto dei prodotti

- Diagnosi: sette foto importate presenti e integre SHA256; la vista ignorava il campo `photoPath`.
- Schede con miniatura e apertura originale, ripiego sull’icona; editor con anteprima e caricamento foto e salvataggio disabilitato durante il trasferimento.
- 103 test e build frontend passati; build ARM64/AMD64 e smoke isolati passati. Aggiornamento e ricostruzione finale completati senza backup Home Assistant.
- Versione 0.6.1 in esecuzione, sette foto verificate visivamente in Ingress. Anteprima editor verificata e finestra chiusa con Annulla; nessun dato operativo modificato.

[Foto prodotti corrette](screenshots/0.6.1/product-photos.jpg). [Guide installate nella 0.6.0](screenshots/0.6.0/home-assistant-guides.jpg).

## Release raggruppata 0.7.0

Sfondo bianco, album salute, QR e Open Plantbook riuniti in un solo aggiornamento successivo, come richiesto. 123 test, verifiche collegamenti, build frontend e build/smoke ARM64/AMD64 passati. 49 file trasferiti e verificati SHA256. Aggiornamento completato con backup disattivato.

Credenziali native trovate nelle preferenze Verdant (nessuna copia in sorgenti o file temporanei). Dal Mac: Open Plantbook e Perenual hanno risposto alla ricerca Ficus elastica; Pl@ntNet ha risposto alla lista progetti autenticata, senza inviare fotografie. Configurazione HA completata nei quattro campi riservati, seguita da riavvio. Nessun valore di credenziale mostrato in chat o salvato nei sorgenti.

Verifica finale 0.7.0: add-on in esecuzione, fonte Open Plantbook ricevuta nel catalogo Ficus, collegamento `/app/local_plantcare_web/plant/<UUID>` apre la scheda nel pannello HA reale. Sfondo bianco e statistiche archivio verificati: 124 foto, 357,7 MiB, SQLite 0,6 MB. Nessuna sessione salute o cura creata nella collezione reale.

Prove: [scheda botanica](screenshots/0.7.0/home-assistant-botanical.jpg), [etichetta QR](screenshots/0.7.0/home-assistant-qr.jpg), [sfondo bianco e spazio](screenshots/0.7.0/home-assistant-white-settings.jpg).
