# Riferimento funzionale — 15 novembre 2026

Origine: ../PlantCare2.0/VerdantMultiplatform/Sources/Verdant e ../PlantCare2.0/VerdantServer/verdant_server.
Riferimento autorevole: codice Swift, non README storico. Non sono stati modificati i progetti originali.

| Area | Riferimento | Destinazione |
|---|---|---|
| Navigazione | ContentView.swift | Colonne desktop; Oggi/Piante/Cure/Prodotti/Altro mobile |
| Tema | Theme.swift | forest #1a4230, moss #406e4d, mint #dbebd9, cream #f5f2e8 |
| Archivio/cure | Models.swift, PlantStore.swift | SQLite centrale; eventi con tombstone per proiezione corretta |
| Pianificazione | PlantCareStateReducer, PlantCareScheduleProjector | Data locale, allineamento concime, rinvii autorevoli |
| Apprendimento | CarePlanLearner.swift | ≥3 cure, ultime 7, mediana, ±1 giorno, baseline ±30% |
| AI | LocalPlantAIService.swift | Gemini/OpenAI, baseline stabile, limiti acqua ±25%, proposte obsolete rifiutate |
| Backup | MacCollectionTools.swift | Envelope v1–v3, SHA256 dei byte payload, dati base64 e fotografie |
| Sensori | HomeAssistantSensors.swift | Classi ammesse, mapping pianta/stanza, freschezza/unità |
| Motore avanzato | CareEngine/* | Porting separato, mantenere shadow fino a equivalenza |
| Fotografie | GrowthAndKnowledgeViews, IOSCareTools | Diario, salute, caricamento file, QR |

## Decisioni
- Add-on separato, nessuna sincronizzazione con app native o vecchio server.
- Importazione atomica solo su archivio vuoto. Backup originale conservato dall'utente.
- Manuale predefinito per le nuove piante finché il pianificatore adattivo completo non è verificato.
- AI disattivata senza credenziali; applicazione automatica disabilitata di default.
- Nessuna attivazione pompe. Token Supervisor mai inviato al browser.
- Screenshot nativi e verifica su HA OS/hardware sono necessari prima del rilascio stabile.

## Matrice dei rilasci
1. Riferimenti e contratti.
2. Add-on, Ingress, layout responsive.
3. Archivio, prodotti, foto, importazione.
4. Dashboard, calendario, eventi, giro di cura — prima milestone utilizzabile.
5. Sensori e motore adattivo con equivalenza Swift.
6. AI e proposte.
7. Cataloghi, guide, diario e strumenti.
8. Backup e QA HA OS multiarch.

L'esistenza di un endpoint non certifica la parità con l'app nativa. Le limitazioni effettive sono riportate in STATUS.md.

## Confronto scheda di modifica pianta (17 novembre 2026)

Lettura di `PlantEditorView.swift` e `Models.swift` a confronto con `PlantEditor` nel frontend: 38 voci confrontate: 17 presenti nel form web, 4 parziali e 17 assenti. La maggior parte dei dati mancanti è già nell’archivio importato (`plantingMethod`, `careFrequencyPreference`, `fertilizerDose`, `lastFertilized`, `fertilizerType`, `setup.container`). Dettaglio, tabella campo per campo e proposta in [PLANT_EDITOR_COMPARISON.md](PLANT_EDITOR_COMPARISON.md).

## Confronto Home (17 novembre 2026)

Lettura di `DashboardView.swift` a confronto con la Home web: il nativo non contiene un elenco generale delle piante, ha la scheda meteo in intestazione, indicatori Piante/Da curare/Luoghi e una sezione analitica con quattro metriche, barre 30 giorni, ciambella dei tipi di cura e piante da osservare. La Home web ha rimosso l’anteprima parziale di 6 piante. Differenze e proposta in [HOME_COMPARISON.md](HOME_COMPARISON.md).

## Confronto schermate (17 novembre 2026)

Dettaglio pianta, collezione, cure, prodotti, misure e impostazioni confrontati con `PlantDetailView.swift`, `PlantListView.swift`, `CareCalendarView.swift`, `FertilizerViews.swift`, `MeasurementModels.swift` e `DefaultLocationSettingsView.swift`. Lacune principali: cestino con ripristino a 30 giorni, filtro categoria e registrazione utilizzo prodotti, “Sposta pianta”, località predefinita. Dettaglio e piano in [SCREENS_COMPARISON.md](SCREENS_COMPARISON.md).

## Incremento 0.2.0 — confronto con il nativo in esecuzione

Osservata l’app `/Applications/Verdant.app` in sola lettura: Panoramica, Cure e calendario, Prodotti e trattamenti e modulo Pianifica ciclo. Il modulo è stato chiuso con Annulla; nessuna cura, prodotto o pianta originale è stato modificato. Riferimenti locali in `docs/screenshots/native/` (non inclusi nel pacchetto di distribuzione).

Adeguamenti: sidebar grigio chiaro, fondo crema, pannelli bianchi, scheda riepilogo verde scuro, settimana con indicatori colorati, terza colonna con selezione vuota. Il confronto su iOS fisico e quello delle funzioni ancora da implementare restano nelle verifiche finali.

Logica trasferita in questo incremento: `CareRoundView`, `TreatmentPlanSheet`, `nextTreatmentAction`, `CareTaskGrouping` e `CareScheduleProjection`. Il giro usa una lista iniziale stabile anziché indicizzare una lista che si accorcia: questo evita di saltare attività. Le modifiche/eliminazioni dei trattamenti ricalcolano il ledger conservando il conteggio importato non rappresentato da eventi.

Contratti aggiunti: `_actions` contiene le proiezioni operative raggruppate, `_schedule` conserva le date di base, `_treatments` espone stato e progressi; comandi `/api/care-round/actions` e CRUD dei cicli sotto `/api/plants/{id}/treatments`. Nessuna modifica allo schema SQLite o all’archivio fotografico.

## Incremento 0.4.0 — assistente AI

Riferimenti: `CloudAIModelCatalog`, `OpenAIChatClient.singlePlantSchema`, `PlantAdviceViewModel`, `PlantAdviceApplicationService` e `DailyOpenAICareCoordinator`. Il controllo web usa la versione della scheda: è più prudente del confronto delle sole cure giornaliere del nativo e invalida anche modifiche non rilevanti al calendario. Gli errori provider vengono sintetizzati e le risposte troncate rifiutate anziché recuperate parzialmente.

Documentazione provider consultata: [OpenAI Models](https://developers.openai.com/api/reference/resources/models/methods/list), [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat), [Gemini Models](https://ai.google.dev/api/models), [Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output). I modelli predefiniti del nativo sono conservati; la disponibilità effettiva dipende dal catalogo dell’account.

## Incremento 0.5.0 — prima parte step 7

Riferimenti nativi: `PlantIdentificationService`, `PlantIdentificationView`, `PlantIdentificationViewModel`, `PlantEditorView.applyIdentification` e `PerenualService`. Stesso endpoint Pl@ntNet, organi, lingua italiana, primi cinque risultati, JPEG qualità 86 a 2.000 pixel, categorie inferite. Le miniature correlate non vengono scaricate in questo incremento. La bozza resta Manuale per la decisione iniziale del progetto: il riconoscimento da solo non approva intervalli, clima o piano.

Perenual: corrispondenza esatta prima del primo risultato, sinonimo Goeppertia/Calathea, fallback sintetico su dettagli 403/429, benchmark giornaliero con arrotondamento Swift e limite 1–60 e baseline per categoria. Il nome della specie risultante è visibile con avviso per le corrispondenze approssimative; tossicità mancante resta sconosciuta. Consultazione informativa, senza modifica dei piani né sovrascrittura dei profili del motore.

Contratti verificati con documentazione ufficiale: [Pl@ntNet identification](https://my.plantnet.org/doc/api/identify) e [Perenual API v2](https://www.perenual.com/docs/api). Biblioteca locale: anagrafica delle specie già importate, non ancora catalogo online completo o editor dei requisiti fisiologici. Guide, diagnosi, album salute annotati, QR e Open Plantbook rimangono negli incrementi successivi dello step 7.

## Incremento 0.6.0 — guide e diagnosi

Porting di `DiagnosisView`/`Symptom` (ToolViews.swift), `CareActionGuide` (CareEventViews.swift), `PlantKnowledgeGrid` e `SeasonalWateringChart` (GrowthAndKnowledgeViews.swift). Le regole diagnostiche sono locali: giallo prima di secco/cadente, poi macchie/insetti e infine crescita lenta. Nessuna analisi foto o chiamata Gemini.

Nove guide testuali estratte dal sorgente; le sequenze fotografiche native non sono incluse, per evitare circa 19 MB di asset fissi. Guida pratica con valori generali della categoria e ritmo stagionale esattamente come nel nativo, non soglie fisiologiche verificate per ogni specie. Il grafico segue lo schema dei mesi nativo e non corregge automaticamente l’emisfero. Nessuna modifica al pianificatore operativo.

Verifica: `.venv/bin/python scripts/verify_health_guides.py` esegue il corpo Swift originale per tutte le 63 combinazioni non vuote di sintomi e 288 punti stagionali; controlla anche titoli, passi e suggerimenti delle nove guide.

## Incremento 0.7.0 — salute, etichette e Open Plantbook

Riferimenti nativi: `GuidedHealthPhotographyView`, `PlantLabelView`, `HealthPhotoSession`, `PhotoAnnotation`, `PlantStore.addHealthPhotoSession`, `OpenPlantbookService` e `BotanicalProfileProvider`. Le quattro foto creano un unico evento «Controlla salute», come nel nativo. Le coordinate web si riferiscono all’intera immagine visualizzata senza ritaglio, evitando lo spostamento delle annotazioni su schermi diversi.

I collegamenti QR usano il pannello Home Assistant e il protocollo ufficiale [proprietà del frame](https://github.com/home-assistant/frontend/blob/dev/src/panels/app/ha-panel-app.ts). Le credenziali rimangono sul server, il QR contiene solo host, identificativo dell’add-on e UUID della pianta. Generazione locale tramite [node-qrcode](https://github.com/soldair/node-qrcode). Open Plantbook segue la [documentazione ufficiale](https://open.plantbook.io/docs/) e le regole native di alias/irrigazione.
