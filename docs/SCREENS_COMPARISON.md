# Confronto con Verdant — schermate (17 novembre 2026)

Confronto funzionale delle schermate oltre a Home e form pianta, letto dai sorgenti Swift in `PlantCare2.0/VerdantMultiplatform/Sources/Verdant` e dal frontend web.

## 1. Dettaglio pianta — `PlantDetailView.swift`

| Area | Nativo | Web |
|---|---|---|
| Sintesi | griglia completa: acqua, concime, rotazione, controllo, diario, potatura, rinvaso, luce, posizione, dal, altezza, vaso | sintesi iOS completa; desktop con esposizione, ambiente, piano, vaso, altezza, prodotto |
| Piano adattivo | stato, anteprima standard/adattivo, revisioni AI e manuali, storico clima | piano, apprendimento, revisione clima, pulsante pianificatore |
| Fotografia | origine, licenza, credito | credito catalogo; foto pianta |
| Sicurezza | scheda con fonte, aggiornamento, assenza dati esplicita | scheda con fonte e testi; nessun aggiornamento dalla scheda |
| Prodotto | scheda, formato, modalità, dose | prodotto collegato e dose |
| Misure | profilo luce della specie, affidabilità, confronto | tabella misure e link sensori |
| Diario | eventi, crescita, salute | eventi, crescita, salute |
| Azioni | modifica, sposta pianta, altre azioni | modifica, azioni rapide, QR, trattamenti |

**Lacune principali**: modifica della posizione (“Sposta pianta”) come azione dedicata; aggiornamento della scheda di sicurezza dalla scheda; profilo luce con affidabilità nel dettaglio.

## 2. Collezione — `PlantListView.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Ricerca | `searchable` | presente |
| Piante / Ambienti | segmentato | presente |
| Filtro sicurezza | menu | chip “Rischio animali” |
| Ordine | per nome, sezioni | alfabetico su telefono, ordine archivio su desktop |
| Azioni riga | menu contestuale e swipe: modifica, annaffia, elimina | apertura scheda; azioni dentro la scheda |
| Cestino | eliminazione con **ripristino entro 30 giorni** | eliminazione definitiva con conferma |
| Paginazione | nessuna | 12 per pagina |

**Lacuna principale**: il **cestino con ripristino a 30 giorni** non esiste nel web; l’eliminazione è definitiva. È la differenza funzionale più rilevante di questa schermata e richiede un cambio backend (soft delete, scadenza, ripristino, pulizia).

## 3. Cure e calendario — `CareCalendarView.swift`, `CareEventViews.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Calendario settimana/mese | sì | sì |
| Cronologia | sì, filtri | sì, filtri e paginazione |
| Giro di cura | sì | sì |
| Sezioni “Oggi e in ritardo” / “In arrivo” | sì | il giro e la Home coprono le scadenze |
| Rinvi/annulla | sì | sì |

Confronto puntuale da completare sul campo; le funzioni principali risultano presenti.

## 4. Prodotti — `FertilizerViews.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Elenco e schede | sì | sì |
| Filtro per categoria | picker “Tutti” + categorie | assente |
| Registra utilizzo | sì | non nella lista |
| Pianifica ciclo | sì | sì |
| Scheda etichetta: acquisto, scadenza, foto | sì | dose, note, foto, NPK; verificare acquisto/scadenza |
| Eliminazione | conferma | conferma |

**Lacune**: filtro categoria e “registra utilizzo” dalla lista.

## 5. Misure e sensori — `MeasurementModels.swift`, `LightMeterView.swift`, `HomeAssistantSensors.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Elenco misure | sì | tabella misure |
| Inserimento manuale | sì | sì |
| Sensori HA e mapping | sì | strumento “Sensori Home Assistant” |
| Classificazione luce e affidabilità | sì | motore lato server; UI sintetica |
| Luxmetro fotocamera | sperimentale | non presente (valutazione rimandata) |

## 6. Impostazioni — `ContentView.swift`, `DefaultLocationSettingsView.swift`, `LocalAISettingsView.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Lingua | sì | sì |
| Servizi e credenziali | sì | sì (config add-on) |
| AI locale/provider | sì | provider e modelli |
| Località predefinita e meteo | editor dedicato | nessun editor; il meteo usa la località del piano |
| Archivio e spazio | sì | statistiche e backup |
| Sensori esposti | app | opzioni add-on |

**Lacuna**: manca una **località predefinita** modificabile dall’interfaccia; oggi la località arriva dal piano adattivo.

## Piano C

1. **C1 Collezione** — cestino con ripristino a 30 giorni (backend + UI), poi azioni rapide (annaffia/modifica) sulle righe.
2. **C2 Prodotti** — filtro categoria e “registra utilizzo” dalla lista; verifica acquisto/scadenza nell’editor.
3. **C3 Dettaglio** — azione “Sposta pianta”, aggiornamento sicurezza, profilo luce con affidabilità.
4. **C4 Impostazioni** — località predefinita e stato meteo.
5. **C5 Cure** — verifica puntuale di calendario, rinvii e storico sul campo.
6. **C6 Misure** — affidabilità e sorgente visibili nella tabella.

Nessuna di queste voci è ancora implementata.
