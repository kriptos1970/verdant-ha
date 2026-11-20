# Confronto con Verdant — schermate (17 novembre 2026)

Confronto funzionale delle schermate oltre a Home e form pianta, letto dai sorgenti Swift in `PlantCare2.0/VerdantMultiplatform/Sources/Verdant` e dal frontend web.

## 1. Dettaglio pianta — `PlantDetailView.swift`

| Area | Nativo | Web |
|---|---|---|
| Sintesi | griglia completa: acqua, concime, rotazione, controllo, diario, potatura, rinvaso, luce, posizione, dal, altezza, vaso | sintesi iOS completa; desktop con esposizione, ambiente, piano, vaso, altezza, prodotto |
| Piano adattivo | stato, anteprima standard/adattivo, revisioni AI e manuali, storico clima | piano, apprendimento, revisione clima, pulsante pianificatore |
| Fotografia | origine, licenza, credito | credito catalogo; foto pianta |
| Sicurezza | scheda con fonte, aggiornamento, assenza dati esplicita | scheda con fonte, data, collegamento e **Aggiorna** dalla scheda |
| Prodotto | scheda, formato, modalità, dose | prodotto collegato e dose |
| Misure | profilo luce della specie, affidabilità, confronto | tabella misure, link sensori e affidabilità del profilo luce nei consigli |
| Diario | eventi, crescita, salute | eventi, crescita, salute |
| Azioni | menu Altre azioni con Modifica e Sposta pianta | menu **⋯** con Modifica e Sposta pianta, azioni rapide, QR, trattamenti |

**Allineato (C3, 18 novembre 2026)**: “Sposta pianta” con ambiente, esposizione, data e nota; il backend aggiorna la stanza e ricalcola il piano intelligente con il clima già salvato (nessuna chiamata meteo), registrando un evento di spostamento con la rotta. La scheda Sicurezza mostra fonte, data e collegamento e può aggiornare il profilo Perenual. I consigli di cura mostrano l’affidabilità del profilo luce della specie. Resta da portare l’intervallo del profilo luce con le fasce lux complete nel dettaglio.

## 2. Collezione — `PlantListView.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Ricerca | `searchable` | presente |
| Piante / Ambienti | segmentato | presente |
| Filtro sicurezza | menu | chip “Rischio animali” |
| Ordine | per nome, sezioni | alfabetico su telefono, ordine archivio su desktop |
| Azioni riga | menu contestuale e swipe: modifica, annaffia, elimina | menu per card: registra annaffiatura, modifica, sposta nel cestino |
| Cestino | eliminazione con **ripristino entro 30 giorni** | eliminazione definitiva con conferma |
| Paginazione | nessuna | 12 per pagina |

**Allineato (C1, 18 novembre 2026)**: il web ha ora un **cestino con ripristino entro 30 giorni**. L’eliminazione sposta la pianta nel cestino (sparisce da collezione, calendario, analisi e storico), `GET /api/trash` elenca gli elementi con i giorni rimanenti, il ripristino la riporta nell’archivio e l’eliminazione definitiva (singola o svuotando il cestino) cancella dati collegati e misure. La pulizia automatica avviene all’avvio e a ogni apertura del cestino. Il backup esporta solo le piante attive. Le card hanno ora il menu **Registra annaffiatura / Modifica / Sposta nel cestino**, equivalente al menu contestuale nativo.

## 3. Cure e calendario — `CareCalendarView.swift`, `CareEventViews.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Calendario settimana/mese | sì | sì |
| Cronologia | sì, filtri | sì, filtri e paginazione |
| Giro di cura | sì | sì |
| Sezioni “Oggi e in ritardo” / “In arrivo” | sì | il giro e la Home coprono le scadenze |
| Attività raggruppate per tipo | sì | sì, nel giorno selezionato |
| Rinvi/annulla | sì, azione dedicata sulla riga | sì, “Rinvia” sulla riga con data precompilata; modifica e annulla dalla cronologia |
| Cronologia raggruppata per giorno | sì, con salute | sì, con salute e conteggio per giorno |
| Filtri cronologia | pianta, tipo, date con azzeramento | pianta, tipo, date con **Azzera filtri** |

**Allineato (C5, 18 novembre 2026)**: le attività del giorno sono raggruppate per tipo, ogni riga ha **Rinvia** (il modulo si apre già impostato sul rinvio con data a domani) e la cronologia è raggruppata per giorno con salute e conteggio, oltre al pulsante **Azzera filtri**. Verificati rinvio reale (evento `postponed` con `postponedUntil`), modifica/eliminazione dalla cronologia e layout a 390/1280 px. Resta la verifica sul campo con notifiche e Companion fisico.

## 4. Prodotti — `FertilizerViews.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Elenco e schede | sì | sì |
| Filtro per categoria | picker “Tutti” + categorie | selettore su telefono e desktop |
| Registra utilizzo | sì, con pianta, data, dose e note | sì, scheda prodotto e griglia desktop |
| Pianifica ciclo | sì | sì |
| Scheda etichetta: acquisto, scadenza, foto | sì | sì: acquisto e scadenza con interruttori, foto, dose, note |
| Eliminazione | conferma | conferma |

**Allineato (C2, 18 novembre 2026)**: filtro per categoria su telefono e desktop, “Registra utilizzo” con pianta, data, dose e note (registra una concimazione o un trattamento secondo la categoria del prodotto) e date di acquisto/scadenza nell’editor e nella scheda.

## 5. Misure e sensori — `MeasurementModels.swift`, `LightMeterView.swift`, `HomeAssistantSensors.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Elenco misure | sì | tabella misure |
| Sorgente e affidabilità | sì | sì, per misura importata o inserita a mano |
| Inserimento manuale | sì | sì |
| Sensori HA e mapping | sì | strumento “Sensori Home Assistant” |
| Classificazione luce e affidabilità | sì | motore lato server; affidabilità del profilo nei consigli |
| Luxmetro fotocamera | sperimentale | non presente (valutazione rimandata) |

**Allineato (C6, 18 novembre 2026)**: `/api/plants/{id}/measurements` unisce le misure native (con sorgente e affidabilità originali, senza duplicare quelle già migrate) e quelle inserite a mano, che riportano affidabilità 100%. La tabella mostra sorgente, affidabilità in percentuale e “non disponibile” per le righe importate prive di metadati. Restano fuori il luxmetro dalla fotocamera e la verifica su sensori reali.

## 6. Impostazioni — `ContentView.swift`, `DefaultLocationSettingsView.swift`, `LocalAISettingsView.swift`

| Funzione | Nativo | Web |
|---|---|---|
| Lingua | sì | sì |
| Servizi e credenziali | sì | sì (config add-on) |
| AI locale/provider | sì | provider e modelli |
| Località predefinita e meteo | editor dedicato con ricerca | editor con ricerca Open-Meteo; il piano intelligente la propone |
| Archivio e spazio | sì | statistiche, backup e **pulizia foto non utilizzate** |
| Sensori esposti | app | opzioni add-on |
| Motore di cura | shadow nel nativo | modalità **shadow/operativa** impostata nella configurazione dell’add-on e mostrata in Impostazioni |

**Allineato (C4, 18 novembre 2026)**: la pagina Impostazioni mostra la **località predefinita** con ricerca Open-Meteo, coordinate, salvataggio e rimozione; il pianificatore intelligente la propone automaticamente per nome, latitudine e longitudine. Lo stato del ricalcolo meteo resta visibile accanto, con gli eventuali piani da riprovare.

## Piano C

1. **C1 Collezione** — ✅ cestino con ripristino a 30 giorni e azioni rapide sulle card.
2. **C2 Prodotti** — ✅ filtro categoria, “registra utilizzo” e date di acquisto/scadenza.
3. **C3 Dettaglio** — ✅ “Sposta pianta”, aggiornamento sicurezza e affidabilità del profilo luce nei consigli.
4. **C4 Impostazioni** — ✅ località predefinita con ricerca e stato meteo.
5. **C5 Cure** — ✅ raggruppamento per tipo, rinvio dalla riga e cronologia per giorno con filtri azzerabili; resta il collaudo sul campo.
6. **C6 Misure** — ✅ sorgente e affidabilità visibili nella tabella; restano luxmetro e sensori reali.

C1–C6 sono implementate e verificate; restano i collaudi sul campo (dispositivo fisico, sensori reali, ripristino isolato, archivio molto grande).
