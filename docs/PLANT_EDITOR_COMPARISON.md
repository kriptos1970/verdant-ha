# Confronto funzionale — scheda di modifica pianta (17 novembre 2026)

Confronto richiesto tra la scheda **Modifica pianta** dell’app nativa Verdant e il form web di PlantCare.

Fonti lette in sola lettura:

- nativo: `PlantCare2.0/VerdantMultiplatform/Sources/Verdant/PlantEditorView.swift` (1.027 righe) e `Models.swift` (`Plant`, `PlantSetup`);
- web: `plantcare_web/frontend/src/main.tsx` → `PlantEditor`, tipi in `types.ts`, modello in `plantcare_web/backend/models.py`.

Legenda: ✅ presente, 🟡 parziale, ❌ assente nel form web. “Nel dato” indica che il campo è già nell’archivio importato e serve solo esporlo.

## Struttura nativa

| Sezione | Campi |
|---|---|
| Foto | fotografia della pianta; identificazione e reidentificazione Pl@ntNet con consenso |
| Identità | nome, nome scientifico, famiglia botanica, categoria |
| Posizione | luogo (con “Aggiungi nuovo luogo…”), esposizione reale (`placement`), esposizione (`light`) |
| Profilo fisico | altezza, metodo di coltivazione |
| Vaso e substrato | materiale, diametro, fori di drenaggio, qualità del drenaggio, altezza vaso, volume in litri, cachepot, sottovaso, nome substrato, ritenzione idrica, drenaggio, aerazione |
| Modalità del piano | tipo di piano segmentato (Manuale/Intelligente/AI) con ricalcolo immediato, ritmo delle cure, intervallo acqua, ultima annaffiatura, intervallo concime, ultima fertilizzazione, tipo/prodotto fertilizzante, dose |
| Attività aggiuntive | rotazione, controllo salute, diario di crescita, potatura, controllo rinvaso: interruttore + intervallo |
| Altre informazioni | con te dal, note |

## Confronto campo per campo

| Campo nativo | Web | Nel dato | Note |
|---|---|---|---|
| Fotografia | ✅ | – | caricamento dal form web |
| Identificazione Pl@ntNet nel form | ❌ | – | il web ha lo strumento “Identifica” separato, non dentro la modifica |
| Reidentificazione con consenso | ❌ | – | solo nativo |
| Nome | ✅ | – | |
| Nome scientifico | ✅ | – | |
| Famiglia botanica | ✅ | – | |
| Categoria | ✅ | – | |
| Luogo / ambiente | ✅ | – | input con suggerimenti; il nativo ha selettore e creazione guidata |
| Esposizione reale (`placement`) | ✅ con piano | `adaptivePlan.placement` | il web la chiede solo nel pianificatore |
| Esposizione (`light`) | ✅ | – | |
| Altezza | ✅ | `heightCM` | aggiunta il 17 novembre 2026 |
| Metodo di coltivazione | ✅ | `plantingMethod` | es. “In vaso” già presente nell’archivio reale |
| Materiale del vaso | ✅ | `potMaterial` e `setup.container.material` | |
| Diametro del vaso | ✅ | `potDiameterCM` / `setup.container.diameterCM` | |
| Fori di drenaggio | ✅ | `potHasDrainage` | il nativo ha anche `setup.container.drainageHoles` |
| Qualità del drenaggio | ✅ | `setup.container.drainageQuality` | |
| Altezza del vaso | ✅ | `setup.container.heightCM` | |
| Volume del vaso in litri | ✅ | `setup.container.volumeLiters` | |
| Cachepot | ✅ | `setup.container.hasCachepot` | |
| Sottovaso | ✅ | `setup.container.hasSaucer` | |
| Nome substrato | ✅ | `setup.substrate.displayName` | |
| Ritenzione idrica substrato | ✅ | `setup.substrate.properties.waterRetention` | |
| Drenaggio substrato | ✅ | `setup.substrate.properties.drainage` | |
| Aerazione substrato | ✅ | `setup.substrate.properties.aeration` | |
| Tipo di piano | 🟡 | `carePlanMode` | web: Manuale/AI; “Intelligente” solo se già attivo; nativo: tre modalità con ricalcolo nel form |
| Ritmo delle cure | ✅ | `careFrequencyPreference` | nell’archivio reale è “Molto frequente”; il nativo ridimensiona gli intervalli |
| Spiegazione della modalità | 🟡 | – | il web mostra un’indicazione, il nativo una spiegazione per modalità |
| Annaffia ogni N giorni | ✅ | – | |
| Ultima annaffiatura | ✅ | – | |
| Fertilizza ogni N giorni | ✅ | – | |
| Ultima fertilizzazione | ✅ | `lastFertilized` | presente nell’archivio |
| Tipo di fertilizzante (senza prodotti) | ✅ | `fertilizerType` | presente nell’archivio |
| Prodotto fertilizzante | ✅ | – | |
| Dose del fertilizzante | ✅ | `fertilizerDose` | es. “Dose intera” già presente |
| Interruttore attività aggiuntive | ✅ | – | il web ha solo l’intervallo: vuoto = disattiva |
| Rotazione, controllo salute, diario, potatura, rinvaso | ✅ | – | mancano gli interruttori e i limiti di intervallo del nativo |
| Con te dal | ✅ | – | |
| Note | ✅ | – | |

## Differenze di comportamento

- **Piano Verdant**: il nativo applica il ricalcolo quando si sceglie “Verdant” nel form; dal 18 novembre 2026 anche il web calcola il piano al salvataggio con la località predefinita e il meteo Open-Meteo, oppure restituisce un errore chiaro se la località manca o il servizio non risponde. Resta disponibile anche “Configura piano Verdant” nella scheda pianta.
- **Nuova pianta**: il web precompila ora altezza 30 cm, vaso in terracotta da 18 cm, drenaggio attivo, metodo “In vaso” e ritmo “Normale”.
- **Ritmo delle cure**: il nativo ridimensiona subito gli intervalli; il web non espone la preferenza.
- **Identificazione**: resta solo nel nativo; il web usa lo strumento “Identifica” separato. È l’unico campo del confronto ancora assente.

## Sintesi

- Voci confrontate: **38** (33 campi singoli, 5 attività raggruppate).
- Presenti nel form web: **34** intere, **2** parziali, **2** assenti (identificazione e reidentificazione nel form).
- I dati mancanti sono in gran parte **già nell’archivio**: il backend conserva i campi extra (`extra='allow'`) e l’archivio reale contiene `plantingMethod`, `careFrequencyPreference`, `fertilizerDose`, `lastFertilized`, `fertilizerType`, `heightCM` e `setup.container` (materiale, diametro, drenaggio, cachepot, sottovaso, qualità). L’allineamento è quindi soprattutto interfaccia, senza migrazione.

## Layout web-first dell’editor (19 novembre 2026)

Scelta deliberata: **non copiare** l’impostazione nativa a otto sezioni sempre aperte. Il web usa la divulgazione progressiva.

| Blocco | Contenuto | Comportamento |
|---|---|---|
| Foto e riconoscimento | foto, cambio foto, Pl@ntNet con risultati inline | sempre visibile |
| Dati essenziali | nome, specie, famiglia e categoria, ambiente ed esposizione, piano, annaffiatura, ultima annaffiatura | sempre visibili, griglia a due colonne |
| Posizione e profilo | posizione reale, altezza, metodo di coltivazione | richiudibile, riepilogo |
| Vaso e substrato | materiale, diametro, altezza, volume, drenaggio, cachepot, sottovaso, substrato e proprietà | richiudibile, riepilogo |
| Frequenze e concimazione | ritmo, concimazione, ultima fertilizzazione, tipo/prodotto/dose | richiudibile, riepilogo |
| Attività aggiuntive | rotazione, controllo, diario, potatura, rinvaso | richiudibile, conteggio attività |
| Altre informazioni | data di acquisizione, note | richiudibile, data o nota |

- Una sola barra **Annulla / Salva** sticky a fine form, con `env(safe-area-inset-bottom)`.
- Riepiloghi sempre leggibili: titolo su una riga e valore secondario sotto, senza troncamenti aggressivi.
- Campi brevi in due colonne; sotto 360 px tornano a una colonna.
- I campi obbligatori restano fuori dalle sezioni chiuse; se un controllo non valido finisce comunque in una sezione chiusa, il submit la apre e porta il focus sul campo.
- Misure: contenuto del dialog a 390 px da ~4.038 px a ~1.392 px; 2.975 px con tutte le sezioni aperte; nessun overflow a 320/390/430 px.

## Allineamento visivo e ordine delle sezioni (18 novembre 2026)

Confronto diretto con `PlantEditorView.swift`:

| Aspetto | Nativo | Web dopo l’intervento |
|---|---|---|
| Ordine sezioni | Foto, Identità, Posizione, Profilo fisico, Vaso e substrato, Modalità del piano, Attività aggiuntive, Altre informazioni | identico |
| Campo | controllo in alto, etichetta caption sotto | identico, con etichette secondarie e controlli a tutta larghezza |
| Sezioni | gruppi del `Form` | card con bordo, sfondo tenue e intestazione |
| Foto | miniatura + pulsante di scelta | area cliccabile con selettore file nascosto |
| Piano | selettore segmentato Manuale/Verdant/AI e spiegazione sotto | selettore a tre voci e spiegazione che cambia con la modalità |
| Testata | Annulla / Salva | Annulla / Salva in testa, ripetuti in fondo per i form lunghi |
| Scheda pianta desktop | hero, griglia “In sintesi”, pila di sezioni richiudibili | stessa struttura: hero, “In sintesi”, card richiudibili; rimosse le schede a tab |

Verifica: screenshot e misure DOM a 686 px (telefono/tablet) e 1280 px (desktop), nessun overflow orizzontale, sezioni nell’ordine nativo, apertura delle sezioni e filtri Piano/Sicurezza, salvataggio riletto con versione incrementata.

## Associazione del fertilizzante (19 novembre 2026)

- Rimosso il campo libero **“Tipo di fertilizzante”**.
- Il prodotto si sceglie da un **elenco visuale** con miniatura, nome, marca, categoria e forma; la prima voce è **“Nessun fertilizzante”**.
- La dose si sceglie solo dopo aver associato un prodotto.
- Il backend deriva sempre `fertilizerType` dal prodotto collegato; l’elenco mostra i prodotti fertilizzanti (Fertilizzante, Biostimolante, Ammendante, Radicante) più l’eventuale prodotto già associato.

## Stato dopo l’allineamento del 17 novembre 2026

- **Impaginazione**: form a sezioni non richiudibili (Identità, Posizione, Profilo fisico, Modalità del piano di cura, Attività aggiuntive, Vaso e substrato, Altre informazioni), righe etichetta/controllo, sottotitolo e Annulla/Salva in testa e in fondo; interruttori a levetta. Verificato a 1280 px (righe flex, toggle 44 px) e con CSS dedicato al telefono.

- **Fatto**: posizione reale, metodo di coltivazione, altezza (già), qualità del drenaggio, altezza e volume del vaso, cachepot, sottovaso, substrato con nome e tre proprietà, ritmo delle cure con ridimensionamento, ultima fertilizzazione, tipo e dose del fertilizzante, interruttori e valori predefiniti delle attività, valori iniziali per una nuova pianta.
- **Allineato**: il form espone le tre modalità Manuale / Verdant / AI. Verdant calcola gli intervalli al salvataggio; Manuale li conserva; AI li affida alle proposte giornaliere. La spiegazione cambia con la modalità scelta.
- **Allineato (19 novembre 2026)**: identificazione Pl@ntNet **dentro il form** con consenso, fino a cinque corrispondenze e compilazione automatica di nome (se vuoto), specie, famiglia e categoria. Resta il riconoscimento come strumento separato per le foto già archiviate.
- **Persistenza**: i campi viaggiano in `setup` (container e substrato) e nei campi già previsti dall’archivio; verificati su archivio sintetico con salvataggio e rilettura.
