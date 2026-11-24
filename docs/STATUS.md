# Stato dell’incremento 1.1.2

## Patch 1.1.2

- Apprendimento bidirezionale: rinvii onorati e annaffiature anticipate influenzano il ritmo; scadenze registrate e stime storiche sono distinte. Duplicati e rinvii multipli nello stesso ciclo non aggiungono conferme indipendenti.
- Guardrail AI proporzionati al profilo: ±15/25/35/50% per principiante/intermedio/esperto/professionista, con soglie botaniche vincolanti e controllo del profilo prima dell’applicazione.
- Prompt arricchito con stati, rinvii, anticipi, note e completamenti; motivazioni esplicite anche quando l’output viene limitato. Nessuna nuova applicazione automatica dei piani AI.
- Verifiche locali: 289 test backend, 25 test browser, controllo i18n e build frontend. Aggiornamento Home Assistant non eseguito per questa patch.

## Patch 1.1.1

- Concimazione preselezionata nel completamento combinato, con possibilità di deselezionarla.
- Intervallo minimo di concimazione pari a due annaffiature: controllo dei valori manuali al salvataggio, piani adattivi e output AI, con vincolo esplicito nei prompt.
- Errori di sessione, connessione e server distinti dai problemi di validazione; dettagli dei campi preservati in italiano e inglese.
- Verifiche locali: 267 test backend, 25 test browser, controllo i18n e build frontend. Aggiornamento Home Assistant non eseguito per questa patch.

## Stato rispetto agli otto step

| Step | Stato |
|---|---|
| 1 — Riferimento funzionale e visivo | Matrice funzionale presente; confronto con macOS eseguito per panoramica, calendario, prodotti e pianificazione dei cicli. Riferimento iOS aggiornato con le schermate native e web Avocado fornite dall’utente; verifica finale nel Companion fisico ancora necessaria. |
| 2 — Add-on e interfaccia | Installata e aggiornata alla 0.10.3 su Home Assistant il 16 novembre 2026; avvio e interfaccia Ingress verificati in Safari. |
| 3 — Archivio e importazione | Archivio personale importato su Home Assistant: 18 piante, 7 prodotti e 124 fotografie; collezione, diario, prodotti e scadenze verificati in Ingress. |
| 4 — Cure e calendario | Completato per questo incremento: giro guidato, calendario settimana/mese, cronologia filtrabile, registrazioni e cicli di trattamento. |
| 5 — Motore adattivo e sensori | Implementato: pianificatore adattivo verificato con Swift, meteo opzionale, apprendimento e motore operativo (shadow/operativo, default operativo). Dettagli in `docs/CARE_ENGINE.md`. |
| 6 — Assistente AI | Implementati catalogo modelli, scelta modello, applicazione selettiva con anteprima, cache, notifiche e controlli delle risposte. Test simulati passati; Gemini reale verificato su Ficus con risposta strutturata e anteprima selettiva. Applicazione su dati reali e analisi giornaliera ancora da collaudare. |
| 7 — Funzioni aggiuntive native | Prima parte implementata: riconoscimento Pl@ntNet, biblioteca delle specie importate e consultazione Perenual. Guide e diagnosi guidata implementate; album salute annotati, QR/NFC e consultazione Open Plantbook aggiunti nella 0.7.0. Catalogo online e collegamento guidato dei profili botanici implementati nella 0.8.0; installata e avviata su HA il 16 novembre 2026. |
| 8 — Consolidamento | Collaudo concluso per l’uso domestico dell’add-on. [Esiti e limiti](#chiusura-dello-step-8). |

## Chiusura dello Step 8

- Il manutentore ha confermato layout e VoiceOver in Home Assistant Companion su iPhone fisico, apertura della pianta corretta tramite QR, temperatura esterna Open-Meteo, sensori HA di umidità, illuminamento e umidità del substrato, Pl@ntNet nell’editor e Gemini su dati reali.
- Ripristino ZIP Verdant e backup parziale Home Assistant (add-on + `/share`) riusciti su un’istanza isolata. La prova sintetica fino a 500.000 eventi non è un requisito per l’uso domestico e non sarà ripetuta per ora; la correzione del limite ZIP resta rinviata.
- Il collaudo NFC è fuori perimetro. Non sono stati confermati sensori di temperatura interna o conducibilità; OpenAI non è stato provato perché non era configurata una chiave. [Riepilogo per issue](STEP8.md#chiusura-dello-step-8).

## Collaudo backup e ripristino su Home Assistant isolato

- Home Assistant OS 18.4 ARM in una VM sul Mac, con l’add-on Verdant 1.0.3 del repository. Tutte le piante, le cure e le foto usate erano di prova.
- **ZIP Verdant:** l’anteprima ha mostrato una pianta nel backup e due nell’archivio corrente; l’import senza `replace=true` è stato rifiutato. Il ripristino ha recuperato pianta e cura originali mantenendo anche la foto non più collegata. Lo snapshot SQLite precedente conteneva entrambe le piante.
- **Backup parziale Home Assistant (add-on + `/share`):** dopo aver cambiato cartella foto e modalità del motore e aggiunto una pianta, il ripristino ha riportato indietro i dati e le impostazioni. Verificati l’avvio dell’add-on, la cronologia e gli SHA-256 delle due foto anche nel backup scaricato. L’istanza Home Assistant reale non è stata modificata.

## Archivi grandi

- Aggiunto un indice SQLite derivato per la cronologia generale; si crea al primo avvio, si aggiorna nella stessa transazione delle cure e si ripopola durante il ripristino. L’archivio JSON, il formato dei backup e le foto non cambiano.
- Nel benchmark diretto sul Mac con 400 piante e 200.000 eventi sintetici, il p95 scende da **706 a 33 ms** senza filtri e da **488 a 25 ms** con filtri. Aumenta lo spazio SQLite; la collezione sintetica resta il flusso più lento. [Metodo e misure](ARCHIVE_SCALE.md).
- **Collaudo Home Assistant OS 18.4 in VM:** per 200.000 eventi via Ingress il p95 della cronologia scende da **798 a 26 ms**, o da **501 a 21 ms** con filtri. Con 500.000 eventi la cronologia resta sotto 63 ms e la collezione raggiunge 2,19 s; scheda, diario e filtro sono stati provati anche in Chromium. Un ZIP con note più lunghe ha rivelato un limite effettivo dei metadati inferiore a quello previsto, dovuto al passaggio interno in base64. Nessun uso di dati reali.

## Frontend e accessibilità

- Playwright e axe su Chromium con archivio temporaneo: navigazione, editor pianta, lingua, ripristino web e blocco dell’import nativo su archivio non vuoto. La CI esegue la suite dopo la build.
- La suite verifica anche che annullare un’annaffiatura non modifichi la scheda e che completarla la registri nel diario della pianta e nella cronologia generale, anche dopo il ricaricamento. Le schede pianta sono testate su desktop (cambio pianta senza trascinare il diario precedente) e telefono (apertura e chiusura della sezione di crescita); la sezione è stata controllata visivamente a 320, 360, 375 e 390 px.
- Aggiunti salto al contenuto, indicazione della vista attiva, nomi accessibili per le finestre e ritorno del focus alla chiusura. Migliorati contrasto del testo secondario, nomi dei giorni nel calendario e messaggi di stato del ripristino.
- Controllata visivamente l’anteprima e la conferma del ripristino a 320, 360, 375 e 390 px in Chromium. Il manutentore ha confermato il funzionamento di VoiceOver su iPhone fisico con Companion. Queste prove non certificano l’accessibilità dell’intera app.

## Rilascio 1.1.0 (22 novembre 2026)

- **Indice della cronologia**: `care_history_index` è una tabella derivata dall’archivio — i payload JSON restano l’unica fonte — creata da `ensure_history_index` al primo avvio, con backfill transazionale dell’archivio esistente e trigger su inserimento, modifica della cronologia/ambiente e cancellazione. `GET /api/history` legge l’indice con una transazione di lettura per conteggio e pagina, quindi conteggio e risultati sono coerenti.
- **Prestazioni misurate**: con 200.000 eventi via Ingress su Home Assistant OS in VM il p95 scende da 798 a 26 ms senza filtri e da 501 a 21 ms con filtri; con 400 piante/200.000 eventi in locale da 706 a 33 ms e da 488 a 25 ms. Con 500.000 eventi la cronologia resta sotto 63 ms e la collezione raggiunge 2,19 s. Metodo, compromessi e limite ZIP in [ARCHIVE_SCALE.md](ARCHIVE_SCALE.md).
- **Integrità verificata**: 4 nuovi test backend coprono il backfill di un database esistente senza riscrivere i payload, modifiche e rollback delle cure, la ricostruzione dell’indice dopo un ripristino e la cancellazione definitiva.
- **Accessibilità e test browser**: Playwright e axe in CI, salto al contenuto, vista attiva, nomi accessibili delle finestre, ritorno del focus, contrasto migliorato. 15 test browser con archivio temporaneo, anche per cure, schede pianta e diario mobile.
- Verifiche: 234 test backend (4 nuovi), 15 test browser, 1.234 chiavi i18n allineate, build frontend. La 1.1.0 è la prima versione che include l’indice; il collaudo HA confrontava solo i file backend dell’indice sovrapposti all’immagine 1.0.3, quindi il bundle frontend non è stato provato su HA in quella prova.

## Rilascio 1.0.3 (22 novembre 2026)

- **Ripristino in-place**: `import_archive(store, archive, replace=True)` sostituisce l’archivio attuale con un backup web (ZIP o JSON) in una sola transazione; `POST /api/import?replace=true` è l’unico modo per chiederlo e l’anteprima restituisce `web` e i conteggi dell’archivio corrente. I backup nativi restano limitati all’archivio vuoto.
- **Protezione**: prima della sostituzione il database viene copiato in `restore-snapshot.sqlite` con `Connection.backup` (una copia coerente anche con WAL) e sovrascritto al ripristino successivo. Le foto sono content-addressed e non vengono mai eliminate: i file non più collegati restano disponibili alla pulizia fotografie.
- **Atomicità verificata**: un test fa fallire il secondo inserimento e controlla che piante e misure precedenti siano ancora presenti; il ripristino risponde 409 e lo snapshot conserva l’archivio di partenza. Un secondo test ripristina lo stesso ZIP due volte e verifica che il checksum già importato non blocchi il ripristino.
- **Interfaccia**: pannello Archivio e backup interamente in italiano e inglese (36 chiavi, plurali inclusi); l’anteprima separa contenuto del backup e archivio attuale, il ripristino è a due passi con **Annulla** / **Conferma ripristino**.
- **Verifica visiva**: flusso completo con Chrome headless a 320, 360, 375, 390 e 1440 px, nessun overflow orizzontale; una pianta aggiunta dopo l’esportazione sparisce dopo il ripristino e le piante del backup tornano disponibili.
- Verifiche: 230 test backend (5 nuovi), 1.231 chiavi i18n allineate, build frontend.

## Rilascio 1.0.2 (22 novembre 2026)

- **Foto del diario**: le miniature nella scheda pianta aprono un modale con l'originale (`growthPhoto` in `main.tsx`), con stato di errore localizzato (`detail.growthPhotoUnavailable`); prima erano link a un nuovo tab che su telefono restava vuoto. Il comando è un `<button>` con `aria-label` e la miniatura ha `alt=""`.
- **`Intl` memorizzato**: nuovo modulo `intl-cache.ts` con cache per `DateTimeFormat`, `NumberFormat` e `PluralRules`; usato da `i18n`, calendario, grafico del trend e guide. Micro-misura: 0,95 → 0,01 ms per render del calendario (35 celle).
- **Controlli i18n**: `scripts/check_i18n.mjs` verifica le 24 chiavi plurali usate nel codice; una chiave mancante ora blocca il controllo invece di comparire a schermo. La guardia è stata provata con una chiave finta e rimossa subito dopo.
- Verifiche: 225 test backend, 1.195 chiavi allineate, build frontend. Il modale foto non è stato esercitato nel preview demo (l'archivio di prova non ha foto di crescita): la verifica visiva è sul tuo archivio reale.

## Rilascio 1.0.1 (22 novembre 2026)

- **Verifica visiva misurata** con `scripts/preview_ios.py` e Chrome headless a 320/360/375/390 px: zero overflow orizzontale su Panoramica, Dettaglio pianta e Prodotti; la barra delle tab non copre il contenuto a fine scroll.
- **Tocco**: tap highlight visibile (`rgba(25,67,48,.12)`), `touch-action: manipulation` sui controlli e stato premuto `filter: brightness(.94)`; prima non esisteva alcuna regola `:active` nel cascade.
- **Prodotti**: la select "Categoria" duplicata è stata rimossa nascondendo `main[data-page=products] .collection-toolbar`; il filtro desktop resta invariato a 1440 px.
- **Dettaglio**: pulsanti `ios-plan-button` e `ios-more-trigger` a 44 px, griglia "In sintesi" non più cliccabile, `autoFocus` disattivato su telefono, `color-scheme: light`, `overscroll-behavior: contain` su modali e overlay prodotto.
- **i18n**: Album salute, etichette QR/NFC, biblioteca botanica, riconoscimento, libreria specie, assistente AI e catalogo modelli passano a `t()`; date, numeri e dosi usano `formatDate`/`formatNumber`/locale. Rimosso l'helper `dueLabel` in `api.ts` che restituiva italiano fisso.
- Verifiche: 225 test backend, 1.193 chiavi i18n allineate, build frontend, `verify_product_dose.mjs` con parità Swift su 40 casi, screenshot in italiano e inglese.

## Rilascio 1.0.0 (22 novembre 2026)

- **Prima versione stabile.** Il codice è invariato rispetto alla 0.11.28: cambiano la presentazione e il processo di distribuzione.
- **Vetrina dell'add-on**: `icon.png` e `logo.png` ricavati da `AppIcon-1024.png` dell'app nativa, `plantcare_web/README.md` come introduzione nello store, `translations/en.yaml` e `translations/it.yaml` per tutte le opzioni.
- **Pannello**: `panel_admin: false` (visibile anche ai non amministratori), `stage: stable`.
- **README**: badge `my.home-assistant.io` per l'aggiunta del repository in un clic, cinque schermate reali in inglese (390×844 a 2x, 1440×900), FAQ e sezione privacy; `README.it.md` allineato.
- **Release**: note bilingui generate da `scripts/release_notes.py`, con installazione da repository come primo passo.
- **Lingua**: corretto il plurale `calendar.daySummary.other`, tradotte le didascalie della scheda desktop e il nome del piano nella UI inglese (`detail.yourPlant`, `detail.editPlant`, `detail.closePlant`).
- **Immagini**: `.github/workflows/publish.yml` pubblica `ghcr.io/kriptos1970/verdant-ha-{arch}:<versione>` per aarch64 e amd64; l'immagine viene attivata in `config.yaml` dopo la prima pubblicazione.
- Verifiche: 225 test backend, 1024 chiavi i18n allineate, build frontend, CI verde sul commit di presentazione.

## Rilascio 0.11.28 (21 novembre 2026)

- **Cestino su telefono**: il comando era dentro `.page-heading`, che su mobile è nascosto (`main:not([data-page=today]) .page-heading{display:none}`), quindi dopo lo swipe-elimina non era possibile ripristinare. Aggiunto un pulsante tondo `.ios-title-action` accanto a `.ios-page-title` nella pagina Piante (`main.tsx`, `ios-layout.css`), visibile solo sotto 760 px.
- Desktop invariato: il comando resta in `.collection-heading-actions`, accanto all’icona della foglia.
- Verificato a 320 e 375 px (44 × 44 px, nessun overflow orizzontale, modale del cestino che si apre) e a 813 px (pulsante mobile `display:none`, riga del titolo alta 0 px).

## Rilascio 0.11.27 (21 novembre 2026)

- **Elenco piante su telefono**: swipe verso sinistra sulla riga, pulsante rosso **Elimina** scoperto sotto la card e pianta spostata nel cestino (nuovo componente `SwipeRow` in `plantcare_web/frontend/src/main.tsx`, stili in `ios-layout.css`). Nessuna conferma: il ripristino entro 30 giorni è la rete di sicurezza e l’avviso “Pianta spostata nel cestino” conferma l’esito.
- Il gesto usa `touch-action: pan-y`, si attiva solo con `pointerType` touch, apre una riga alla volta e chiude con un tocco sulla riga o altrove; il desktop mantiene il menu ⋯ con la conferma.
- **Cestino**: nuovo pulsante **Svuota cestino** con conferma `trash.emptyConfirm` (una o più piante) e avviso “Cestino svuotato”. La finestra di conferma generica usa ora `common.confirmTitle`, `common.cancel` e `common.delete` invece di testi italiani fissi.
- Verificato a 320/375 px: swipe, chiusura al tocco, eliminazione, ripristino, svuotamento con conferma e annullamento; a 1000 px il pulsante resta `display:none` e la griglia non cambia.

## Rilascio 0.11.26 (21 novembre 2026)

- **Calendario su telefono**: la vista settimanale non usa più le frecce; la striscia dei giorni scorre in orizzontale in modo continuo (380 giorni, da 14 giorni prima di oggi a un anno avanti) con `scroll-snap-type: x proximity` e scrollbar nascosta (`plantcare_web/frontend/src/care-calendar.tsx`, `ios-layout.css`).
- Il giorno selezionato viene centrato all’apertura, al tocco e con **Oggi** solo se non è già interamente visibile; il tocco seleziona il giorno e aggiorna l’elenco sottostante.
- Il desktop resta invariato (griglia a 7 giorni con frecce); in vista mensile le frecce restano anche su telefono. Verificato a 320, 375, 390 px e 800 px, incluso il passaggio dinamico tra i due layout senza ricaricare.

## Rilascio 0.11.25 (21 novembre 2026)

- **Calendario su telefono**: le regole `main[data-page=care] .calendar-panel .section-heading{display:none}` e `main[data-page=care] .calendar-navigation{display:none}` introdotte nella 0.11.19 nascondevano mese, pulsante **Oggi**, frecce e passaggio settimana/mese; sono state sostituite da una testata compatta (`plantcare_web/frontend/src/ios-layout.css`).
- Sotto 430 px l’etichetta “Vista mensile” resta solo come `aria-label` dell’icona; i pulsanti mantengono 38 px di altezza.
- La striscia settimanale è passata da carosello orizzontale a griglia a sette colonne: `scrollWidth == clientWidth` a 320, 375 e 390 px e giorno selezionato sempre visibile.
- Verifica nel browser a 320, 375, 390 e 500 px: frecce 16–22 → 23–29 novembre, vista mensile con 42 celle (26 ottobre – 6 dicembre), **Oggi** che riporta selezione e mese correnti. I chip delle stanze restano nascosti su telefono.

## Rilascio 0.11.24 (21 novembre 2026)

- **Diario di crescita**: la foto scelta o scattata viene ridotta a 2400 px e ricodificata in JPEG nel browser prima dell’invio, così il trasferimento è circa un terzo e la miniatura appare prima anche attraverso Ingress o da remoto.
- La compressione conserva l’orientamento EXIF ed è applicata anche ad album salute, foto pianta e prodotto; il server lavora in un thread separato e decodifica a risoluzione ridotta le foto molto grandi.
- 225 test backend, 1014 chiavi i18n, build frontend.

## Rilascio 0.11.23 (21 novembre 2026)

- Nelle card delle cure e nella cronologia l’immagine della pianta mostra in basso a destra una piccola icona dell’azione (annaffiatura, concimazione, rotazione, controllo salute, diario di crescita e le altre cure), con il colore della categoria.
- L’icona è decorativa per l’accessibilità: l’azione resta scritta nella card. 224 test backend, 1014 chiavi i18n, build frontend.

## Rilascio 0.11.22 (21 novembre 2026)

- **Home su telefono**: il saluto “Buongiorno 🌿” non va più a capo; la colonna meteo/icona usa solo la larghezza del contenuto invece di metà testata.
- Il meteo compatto mostra solo la temperatura, la località resta nell’etichetta accessibile; sotto i 360 px il saluto usa 26 px.
- Verifica locale a 390, 375, 360 e 320 px senza ritorno a capo né sovrapposizioni. Correzione pronta per l’aggiornamento da repository.

## Rilascio 0.11.21 (20 novembre 2026)

- **Impostazioni → Motore di cura**: la modalità attiva ha un indicatore e la dicitura “Modalità attiva nell’add-on”; le due modalità sono elencate separatamente e quella corrente è evidenziata.
- La descrizione non confonde più il valore corrente con l’altra modalità; dopo una modifica dell’opzione l’add-on va riavviato e la web UI si aggiorna entro un minuto.
- 224 test backend, 1014 chiavi i18n, build frontend.

## Rilascio 0.11.20 (20 novembre 2026)

- Sfondo della pagina in verde tenue (`--vc-canvas`); pannelli, schede e finestre restano bianchi e le sezioni si separano come nell’app nativa.
- Su telefono l’intestazione del dettaglio segue lo sfondo della pagina; le schede cura restano bianche.
- Nessun cambiamento a contenuti, flussi o dati. 224 test backend, 1013 chiavi i18n, build frontend.

## Rilascio 0.11.19 (20 novembre 2026)

- Attività **Diario di crescita** con il layout di conferma precedente (data, rinvio, salute, note) e i pulsanti **Scatta una foto** / **Scegli fotografie**.
- Foto salvate nella voce di crescita; evento “Aggiorna progressi” registrato in cronologia. Corretto il percorso della 0.11.18.
- 224 test backend, 1013 chiavi i18n, build frontend.

## Rilascio 0.11.18 (20 novembre 2026)

- Attività **Diario di crescita**: apertura dell’editor del diario con **Scatta una foto** e **Scegli fotografie**; foto salvate nella voce di crescita e attività registrata.
- Aggiornati **Pillow 13.0.0** e **python-multipart 0.0.31**; `pip-audit` e `npm audit` senza vulnerabilità note.
- 223 test backend, 1013 chiavi i18n, build frontend.

## Rilascio 0.11.17 (20 novembre 2026)

- Il banner generico “Controlla i dati inseriti.” non viene più mostrato per errori senza dettaglio o durante un form modale; il messaggio di validazione indica campo e motivo e resta inline nel form.
- Limiti `maxLength` sui testi lunghi per evitare validazioni evitabili.
- 223 test backend, build frontend.

## Rilascio 0.11.16 (20 novembre 2026)

- Motore di cura, passo 1.3: profilo di esperienza **principiante / intermedio / esperto / professionista** in Impostazioni, con passo massimo 1/2/3/4 giorni.
- L’apprendimento usa il numero di rinvii onorati o anticipati, fino al massimo del profilo; ritardi senza rinvio e dati insufficienti restano a 1 giorno.
- AI giornaliera e assistente ricevono `experienceLevel`; `contextVersion` 4.
- 222 test backend, 1012 chiavi i18n, build frontend.

## Rilascio 0.11.15 (20 novembre 2026)

- Motore di cura, passo 1.2: apprendimento adattivo ai rinvii. Passo di 1 giorno per default; 2 giorni con almeno due rinvii onorati (o due rinvii anticipati nella direzione opposta).
- I ritardi senza rinvio non accelerano l’apprendimento; restano il limite ±30% e il target.
- `careLearning` espone il passo e i conteggi di rinvii/ritardi usati.
- 220 test backend, build frontend.

## Rilascio 0.11.14 (20 novembre 2026)

- Motore di cura, passo 1.1: l’analisi AI riceve **località** e `careTiming` (intervalli osservati, rinvii con nota, ritardi senza rinvio); il prompt distingue rinvii intenzionali e ritardi.
- Anche l’assistente della scheda pianta riceve località e rinvii recenti; `contextVersion` aggiornato a 3.
- 217 test backend, build frontend.

## Rilascio 0.11.13 (20 novembre 2026)

- Card Attività desktop: pulsante **Completa** largo 200 px (massimo 100% della card) e alto 44 px, non più a tutta riga.
- Su telefono resta a tutta larghezza.
- 215 test backend, build frontend.

## Rilascio 0.11.12 (20 novembre 2026)

- Finestra **Completa** su telefono: solo scorrimento verticale; overflow orizzontale nascosto, overscroll disattivato e `touch-action: pan-y pinch-zoom`.
- Testi lunghi a capo; campi e pulsanti contenuti nella larghezza del pannello.
- Verifica a 320/390 px con nome pianta molto lungo, nessun overflow orizzontale.
- 215 test backend, build frontend.

## Rilascio 0.11.11 (20 novembre 2026)

- Maniglia del pannello dettaglio disponibile anche nello stato vuoto, non solo con una pianta aperta; la colonna destra si ridimensiona subito.
- Z-index delle maniglie alzato per evitare sovrapposizioni con il contenuto.
- 215 test backend, build frontend.

## Rilascio 0.11.10 (20 novembre 2026)

- Desktop: **colonna sinistra** e **pannello dettaglio** ridimensionabili trascinando il bordo, con larghezza persistente e ripristino con doppio clic.
- Frecce da tastiera, limiti 190–420 px (colonna) e 320–720 px (dettaglio), almeno 420 px per il contenuto.
- Maniglie solo sopra 1000 px; layout telefono/tablet invariato.
- 215 test backend, build frontend.

## Rilascio 0.11.9 (19 novembre 2026)

- Nome visibile di add-on e web app cambiato in **Verdant**: nome add-on, pannello, brand, titolo pagina, notifiche e messaggi.
- Slug `plantcare_web`, `/data`, database, foto, formato backup e identificatori interni invariati per preservare dati e aggiornamenti.
- 215 test backend, build frontend.

## Rilascio 0.11.8 (19 novembre 2026)

- Risposte AI formattate come Markdown nel riquadro verde: titoli, paragrafi, grassetto/corsivo, elenchi, citazioni, codice e tabelle.
- Renderer caricato su richiesta in un chunk separato; nessuna interpretazione di HTML grezzo.
- Gemini e OpenAI usano lo stesso campo `summaryMarkdown` e lo stesso rendering.
- 215 test backend, build frontend.

## Rilascio 0.11.7 (19 novembre 2026)

- Etichette QR/NFC con lo slug dell’add-on corrente, ricavato dall’hostname del container; le etichette già stampate restano leggibili.
- Migrazione reale al repository add-on completata: `309d34f7_plantcare_web` 0.11.7, archivio e opzioni copiati, 124 foto; il vecchio `local_plantcare_web` resta fermo per rollback.
- Documentazione del motore di cura nelle tre modalità: `docs/CARE_ENGINE.md` e `docs/en/CARE_ENGINE.md`.
- 215 test backend.

## Rilascio 0.11.6 (19 novembre 2026)

- Migrazione assistita locale → repository add-on: import del database da `/share/plantcare/migrate/plantcare.sqlite` quando `/data` è vuoto ed esiste `import-request`.
- Validazione dell’intestazione SQLite, sostituzione atomica, richiesta consumata una sola volta; il file resta per il rollback.
- 215 test backend.

## Rilascio 0.11.5 (19 novembre 2026)

- Associazione del fertilizzante ripensata nell’editor pianta: elenco visuale con miniatura, nome, marca, categoria e forma, più “Nessun fertilizzante”.
- Rimosso il campo libero “Tipo di fertilizzante”; il tipo è derivato dal prodotto scelto anche lato backend.
- Filtro ai prodotti fertilizzanti (Fertilizzante, Biostimolante, Ammendante, Radicante) con l’eventuale prodotto già associato; dose visibile solo con un prodotto.
- Verifica: 213 test backend, 1001 chiavi i18n, build frontend, nessun overflow a 320/390 px.

## Rilascio 0.11.4 (19 novembre 2026)

- Motore di cura con **una sola fonte di configurazione**: `care_engine_mode` nelle opzioni dell’add-on, default **Operativo**. Rimosso l’override salvato dalla web UI che causava la divergenza shadow/active.
- In **Impostazioni → Motore di cura** compaiono la modalità effettiva, la spiegazione di shadow e operativo e l’indicazione di dove cambiarla; nessun selettore che possa divergere.
- Verifica: 212 test backend, 1000 chiavi i18n, build frontend.

## Rilascio 0.11.3 (19 novembre 2026)

- Editor pianta **web-first** con divulgazione progressiva: foto e riconoscimento Pl@ntNet, identità, ambiente, piano, annaffiatura e ultima annaffiatura sempre visibili.
- Cinque sezioni facoltative richiudibili con riepilogo (Posizione e profilo, Vaso e substrato, Frequenze e concimazione, Attività aggiuntive, Altre informazioni).
- Una sola barra Annulla/Salva sticky in fondo, safe area inclusa; rimossa la doppia barra superiore.
- Griglie a due colonne per i campi brevi, colonna singola sotto 360 px. Contenuto a 390 px: da ~4.038 px a ~1.392 px (2.975 px con tutte le sezioni aperte).
- Validazione: i campi obbligatori restano visibili; un controllo non valido in una sezione chiusa la apre e riceve il focus.
- Riquadri verde tenue (`--vc-mint-soft` / `--vc-mint-line`) per crescita, cronologia, linea del tempo, andamento, sezioni dell’editor e riconoscimento Pl@ntNet.
- Verifica: 320/390/430 px senza overflow, 212 test backend, 999 chiavi i18n, build frontend.

## Rilascio 0.11.2 (19 novembre 2026)

- Parità funzionale e strutturale con Verdant su collezione, prodotti, dettaglio, impostazioni, cure, misure e diario.
- Token visivi in `frontend/src/tokens.css`; icone piene, tipografia telefono proporzionata, Home/Cure/Cronologia riallineate.
- Riconoscimento Pl@ntNet dentro l’editor nuova pianta, senza conferme: il pulsante diventa verde dopo la foto, attende il risultato e compila i campi.
- Motore di cura operativo e pulizia foto non utilizzate.
- 212 test backend, 988 chiavi i18n, build frontend.

## Prossima versione (0.11.20)

- Luxmetro dalla fotocamera, campanella “Attive”/notifiche web se richieste.
- Collaudi rinviati: iPhone fisico/Companion, QR/NFC reale, Pl@ntNet reale, Gemini reale, ripristino su HA isolata, sensori e meteo reali, archivio molto grande.

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

## Grafici — fase 4, scheda pianta (17 novembre 2026)

- Nuovo “Andamento delle cure” nella scheda pianta, sotto Diario: dodici mesi di annaffiature e altre cure con barre CSS, legenda con conteggi, totale e mesi attivi.
- Dati dalla cronologia già caricata, senza richieste aggiuntive e senza Recharts; esclusi eventi eliminati e rinvii, mesi calcolati nel fuso dell’app.
- Tabella accessibile con mese, annaffiature, altre cure e totale; etichetta accessibile sul grafico e stato vuoto dedicato.
- Verifica: build, **777 chiavi i18n**, 180 test backend, layout 320/390/1280 px senza overflow, italiano e inglese, Lighthouse accessibilità 0.95 con i due rilievi preesistenti del riepilogo iOS.

## Grafici — fase 5, linea del tempo della pianta (17 novembre 2026)

- Nuova “Linea del tempo” nella scheda pianta, sotto Diario: cure e misure unite dal nuovo endpoint `/api/plants/{id}/timeline`, dalla più recente.
- Punti colorati per tipo di cura, misure con etichetta tradotta e valore con unità, controlli salute con lo stato, rinvii marcati; caricamento, stato vuoto ed errore con “Riprova”.
- La richiesta parte solo aprendo il Diario e non carica Recharts; nessuna modifica ai dati reali.
- Verifica: **796 chiavi i18n**, build, 180 test backend, layout 320/390/1280 px senza overflow, italiano e inglese, nessun errore in console.

## Grafici — fase 6, selettore 30/90/365 (17 novembre 2026)

- La pagina Analisi ha ora tre pulsanti (30 giorni, 90 giorni, 12 mesi) con `aria-pressed`; il periodo scelto guida la richiesta e il sottotitolo non è più fisso su 30 giorni.
- `/api/analytics` restituisce l’attività giornaliera dell’intero periodo: le barre si raggruppano in giorni a 30 giorni, settimane a 90 e mesi a 365, con descrizione, didascalia e colonna coerenti.
- Durante il cambio periodo i dati precedenti restano visibili con `aria-busy`; la richiesta in corso viene annullata.
- Verifica: **787 chiavi i18n**, 180 test backend aggiornati sul nuovo contratto, layout 320/390/1280 px senza overflow, italiano e inglese, reti `days=30/90/365`, Lighthouse accessibilità 0.96 con il solo contrasto preesistente del piè di pagina.
- Installata su Home Assistant il 17 novembre 2026 ricostruendo l’add-on 0.11.1 dai sorgenti aggiornati: 99 file verificati SHA256. In Ingress la Home mostra 18 piante al 100%, l’Analisi 495 cure/77 giornate/83% a 90 giorni e la scheda Orchidea 12 voci di linea del tempo. Nessun dato reale modificato e nessun backup creato.

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

- I piani importati mantengono gli intervalli finché non vengono ricalcolati esplicitamente. Il meteo automatico richiede attivazione esplicita per pianta. Le misure dei sensori non cambiano il calendario: alla 0.3.0 il Care Engine restava shadow, come previsto dal piano.
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

## Collezione — paginazione (17 novembre 2026)

- La pagina Piante mostra **12 piante per pagina**, con intervallo “1–12 di N” e pulsanti Precedenti/Successive; su telefono l’ordine è alfabetico, su desktop resta l’ordine della collezione.
- Ricerca, ambiente e filtro riportano alla prima pagina; se i risultati scendono sotto le 12 voci la paginazione sparisce e la pagina viene riallineata.
- Il cambio pagina riporta in cima al contenuto, rispettando `prefers-reduced-motion`.
- La paginazione è nascosta nella vista Ambienti del telefono; la Home continua a mostrare le prime 6 piante.
- Verifica: build e **797 chiavi i18n**, 180 test backend; archivio sintetico portato a 14 piante, pagine 12 + 2, ricerca “Monstera” con una sola scheda e nessuna paginazione, layout 390 e 1280 px senza overflow, italiano e inglese.
- Installata su Home Assistant il 17 novembre 2026 con la ricostruzione dell’add-on 0.11.1: in Ingress 12 schede “1–12 di 18” e 6 schede “13–18 di 18”, nessun dato reale modificato.

## Collaudi — stato al 17 novembre 2026

- **#5 archivio grande (parziale)** — benchmark sintetico esteso a **400 piante / 200.000 eventi** (quattro volte il precedente): risposta completa 49,5 MB in 2,05 s, collezione sintetica 561 kB in 1,05 s (−98,87%), pagina cronologia 18,5 kB in 0,68 s sul Mac di sviluppo. Comando: `scripts/benchmark_archive.py --plants 400 --events 500` (eventi per pianta). Non sostituisce la prova su un archivio reale molto grande.
- **#4 sensori e meteo (bloccato sulla configurazione)** — `exposed_entities` è vuoto nell’add-on, `/api/sensors` restituisce 0 letture e non esistono associazioni. In Home Assistant ci sono 90 entità con classi supportate, tra cui `sensor.dracena_moisture` (36%), `sensor.dracena_illuminance` (6 lx) e `sensor.dracena_conductivity` (74 µS/cm). Tutti i 18 piani adattivi hanno il meteo disattivato; l’ultimo calcolo è del 20 settembre 2026.
- **#2 QR/NFC (link verificato)** — etichetta di Ficus Elastica con URL stabile `https://sicoli.ovh/app/local_plantcare_web/plant/170F12A0-7D2E-489E-AF4A-116A108D6985`, senza token Ingress; senza sessione la pagina richiede l’accesso a Home Assistant. La scansione con la fotocamera resta da fare.
- **#1 iPhone fisico** e **#3 ripristino isolato** — richiedono dispositivo e istanza separata; procedure pronte, esito da registrare.

## Piano intelligente da telefono (17 novembre 2026)

- Nella scheda pianta da telefono il pulsante del piano apre ora **Configura/Ricalcola piano intelligente** anche per le piante in modalità Manuale; prima apriva solo la modifica manuale, rendendo irraggiungibile l’opzione meteo di Open-Meteo.
- Resta separata la matita della sezione Piano per modificare le frequenze manuali.
- Verifica: 390 px, modale con casella “Usa il meteo e aggiorna il piano ogni giorno”, campi località e clima; desktop invariato.

## Scheda pianta — aspetto allineato (17 novembre 2026)

- L’editor usa ora sezioni non richiudibili con intestazioni, righe etichetta/controllo, sottotitolo e Annulla/Salva in testa, interruttori a levetta; su telefono le righe tornano in colonna. Verificato a 1280 px senza overflow, **856 chiavi i18n**, build ok.

## Misure — sorgente e affidabilità (18 novembre 2026)

- `/api/plants/{id}/measurements` restituisce anche le **misure native** conservate nello stato di importazione, con `source`, `entity_id` e `reliability` originali; le righe già migrate nella tabella SQL non vengono duplicate.
- Le misure inserite a mano riportano sorgente “Inserita a mano” e affidabilità 100%; le righe importate senza metadati mostrano “Affidabilità non disponibile”.
- La tabella Misure mostra sorgente, affidabilità e il promemoria che una lettura non è una diagnosi.
- Verifica su archivio sintetico: misura manuale al 100% e misura nativa `sensor.monstera_moisture` all’87%, senza duplicati; layout 390 e 1280 px senza overflow. Build, **931 chiavi i18n**, **201 test backend** (4 nuovi sulle misure).

## Cure e calendario — rinvio e cronologia (18 novembre 2026)

- Le attività del giorno selezionato sono **raggruppate per tipo** con intestazione, come nel calendario nativo.
- Ogni riga programmata ha **Rinvia**: apre il modulo di registrazione già impostato sul rinvio, con data precompilata a domani; il salvataggio crea un evento `postponed` con `postponedUntil`. Restano disponibili registrazione, modifica e annullamento.
- La **cronologia** è raggruppata per giorno con conteggio, mostra la salute dell’evento e ha **Azzera filtri** quando pianta, tipo o date sono impostati.
- Verifica su archivio sintetico: rinvio reale di un’annaffiatura con evento `postponed` e `postponedUntil` al giorno successivo; cronologia raggruppata con quattro eventi nello stesso giorno; nessun overflow a 390 e 1280 px. Build, **926 chiavi i18n**, **197 test backend**.

## Impostazioni — località predefinita (18 novembre 2026)

- Nuova sezione **Località predefinita** in Impostazioni: ricerca con Open-Meteo (`GET /api/weather/locations`), elenco di risultati con area e paese, coordinate, salvataggio (`PUT /api/preferences/location`) e rimozione (`DELETE /api/preferences/location`). La scelta è conservata nello stato `location` e restituita anche da `/api/settings`.
- Il pianificatore intelligente propone automaticamente la località predefinita quando la pianta non ha ancora un piano (nome, latitudine e longitudine precompilati); la località del piano esistente resta prioritaria.
- Lo **stato del ricalcolo meteo** già presente in Impostazioni resta accanto alla località e segnala i piani da riprovare.
- Verifica su archivio sintetico: ricerca “Roma” con otto risultati, salvataggio di Roma (41.8919, 12.5113) e precompilazione del pianificatore per una pianta manuale; layout 390 e 1280 px senza overflow. Build, **923 chiavi i18n**, **197 test backend** (4 nuovi su località e geocodifica).

## Dettaglio pianta — spostamento e sicurezza (18 novembre 2026)

- **Sposta pianta** dalla scheda (pulsante nella sezione Ambiente e menu “Altre azioni” su telefono): ambiente con suggerimenti esistenti, esposizione, data e nota. L’endpoint `POST /api/plants/{id}/move` aggiorna la stanza, registra un evento “Spostamento” con la rotta (`Salotto → Studio · nota`) e, per il piano intelligente, ricalcola il piano con località e clima già salvati **senza chiamate meteo**; le revisioni manuali o AI restano preservate.
- La scheda **Sicurezza** mostra fonte, data, collegamento e il pulsante **Aggiorna** (o **Cerca dati di sicurezza**): `POST /api/plants/{id}/safety/refresh` interroga Perenual e salva `safetyProfile` con tossicità per persone e animali. Un dato assente non viene interpretato come assenza di rischio.
- I **consigli di cura** mostrano l’affidabilità del profilo luce della specie (`components.profileQuality`).
- Verifica su archivio sintetico: spostamento da Salotto a Studio con evento `Salotto → Studio · Prova spostamento`; piano intelligente aggiornato a “Pieno sole” con irrigazione da 8 a 6 giorni e nessuna rete; dialoghi senza overflow a 320, 390 e 1280 px. Build, **908 chiavi i18n**, **193 test backend** (8 nuovi su spostamento e sicurezza).

## Prodotti — registrazione utilizzo (18 novembre 2026)

- Le schede prodotto (telefono e griglia desktop) hanno **Registra utilizzo**: si sceglie la pianta, data e ora, dose e note; il web registra una **concimazione** per i fertilizzanti e un **trattamento** per le altre categorie, con prodotto collegato e dettaglio leggibile nello storico.
- **Filtro per categoria** anche nella griglia desktop, oltre a quello già presente nella vista telefono.
- L’editor prodotto ha **data di acquisto** e **scadenza** con interruttori, mostrate nella scheda del prodotto.
- Verifica su archivio sintetico: utilizzo registrato su Monstera (evento “Concima” con prodotto, dose e note, `lastFertilized` aggiornato); acquisto 15 marzo 2026 e scadenza 15 marzo 2028 salvati e riletti; filtro “Antiparassitario” con un solo prodotto coerente; nessun overflow a 390 e 1280 px. Build, **889 chiavi i18n**, 185 test backend.

## Cestino con ripristino (18 novembre 2026)

- **Backend**: soft delete sulla tabella `entities` (`deleted_at`), `GET /api/trash`, `POST /api/trash/{id}/restore`, `DELETE /api/trash/{id}` e `DELETE /api/trash`; pulizia automatica dopo 30 giorni all’avvio e all’apertura del cestino. Le piante nel cestino escono da collezione, calendario, analisi, storico e backup; al ripristino tornano con una nuova versione.
- **Interfaccia**: pulsante **Cestino** nella collezione, elenco con foto, ambiente e giorni rimanenti, **Ripristina** ed **Elimina definitivamente** con conferma; l’eliminazione dalla scheda ora sposta nel cestino e lo dice.
- **Editor pianta**: verificato a 320, 360, 390, 686 e 1280 px; `scrollWidth` uguale a `clientWidth` a ogni larghezza, scroll verticale regolare e `scrollbar-gutter: stable` sulla finestra di modifica, così la barra orizzontale non compare durante lo scorrimento.
- **Test**: 185 test backend (5 nuovi sul cestino: uscita dall’archivio, ripristino con versione, eliminazione definitiva, scadenza e svuotamento, backup senza piante nel cestino). Build, **871 chiavi i18n**.

## Token visivi e riconoscimento nell’editor (19 novembre 2026)

- Nuovo file `frontend/src/tokens.css` come fonte unica per colori, tipografia telefono, spazi, raggi, icone e target di tocco; i CSS esistenti usano gli stessi valori semantici. Documento: `docs/VISUAL_TOKENS.md`.
- Nell’editor **Nuova pianta / Modifica pianta** c’è ora **Riconosci con Pl@ntNet**: usa la foto scelta o quella già salvata, richiede consenso, mostra fino a cinque corrispondenze e compila **nome (se vuoto), specie, famiglia e categoria**. Il riconoscimento resta separato dallo strumento “Riconoscimento AI” per le foto non ancora associate.
- Verifica: blocco presente a 390 px senza overflow, pulsante disabilitato senza chiave Pl@ntNet e attivo quando il servizio è configurato. Build, **988 chiavi i18n**, **212 test backend**.

## Collaudi rinviati (19 novembre 2026)

- iPhone fisico / Companion e safe area.
- Scansione QR/NFC reale.
- Ripristino su istanza Home Assistant isolata.
- Sensori Home Assistant e Open-Meteo reali.
- Archivio reale molto grande.
- Luxmetro dalla fotocamera del telefono (da valutare).
- Prova AI reale: il provider Gemini è ora raggiungibile e funzionante; l’analisi va rieseguita quando richiesto.
- Foto e archivio reale sono già popolati.

## Confronto visivo con il simulatore iPhone (19 novembre 2026)

- Compilata e avviata **Verdant iOS** dal progetto `PlantCare2.0/VerdantMultiplatform` su **iPhone 17 Pro / iOS 26.5** con `xcodebuild` e `simctl`; screenshot nativo salvato e confrontato con il web a 430 px.
- Il simulatore aveva 4 piante ma 0 cure in scadenza, quindi le sezioni condizionali “oggi” e “Come evolve la tua collezione” non erano visibili; per lo stato popolato sono state usate le schermate native fornite dall’utente.
- Allineati al nativo: icone **piene** (goccia, foglia, calendario, casa, grafico, warning, ellissi), riquadri colorati delle metriche, righe pianta con pulsante blu, card azioni con foto grande, pulsante **Completa**, menu **⋯** e intestazioni di gruppo (“Annaffia”).
- Restano differenze funzionali consapevoli: la campanella “Attive” del nativo non esiste nel web (nessuna notifica push), e le foto demo sono segnaposto finché non si usano immagini reali.

## Motore di cura operativo (18 novembre 2026)

- La modalità si sceglie nella configurazione dell’add-on (`care_engine_mode`, default **Operativo**) e la web UI la mostra in sola lettura; non esiste più un override nel database.
- In modalità operativa, dopo una misura manuale o un campionamento dei sensori, il motore può **solo rinviare** l’annaffiatura quando il terreno è ancora umido e la misura è fresca e affidabile. Non anticipa mai una cura e non la registra.
- Regole di sicurezza: misura con affidabilità ≥ 65%, gate non `restricted`, confidenza ≥ 35% per umidità ≥ 70% (≥ 55% negli altri casi), un solo rinvio per ciclo di annaffiatura, massimo 14 giorni. Il rinvio è scritto in `nextWateringOverride`, con nota nel diario (`Aggiornamento piano`) e riepilogo `careEngineApplied` visibile nel piano.
- Verifica su archivio sintetico: terreno all’82% con annaffiatura prevista domani → rinvio al giorno successivo, diario aggiornato e nessun secondo rinvio con la stessa lettura; terreno al 18% non anticipa nulla; in shadow nessuna modifica. **215 test backend**. Dettagli delle tre modalità in [CARE_ENGINE.md](CARE_ENGINE.md).
- Su Home Assistant la modalità effettiva è quella dell’opzione dell’add-on; i sensori reali sono configurati e le letture attuali non superano la soglia di rinvio, quindi nessun calendario reale è stato modificato.

## Prova AI con provider reale (18 novembre 2026)

- Provider **Gemini** configurato su Home Assistant (`gemini-3.5-flash-lite`), 18 piante in modalità AI, `auto_apply_ai` disattivato. L’analisi giornaliera precedente aveva già girato con successo senza proposte.
- La prova manuale di oggi (`POST /api/ai/analyze`) è stata rifiutata da Gemini con **“non disponibile per la località della connessione Home Assistant”** (HTTP 422, codice `remote`). Non sono state create proposte né modificati piani; la chiave OpenAI non è configurata.
- La pipeline AI resta verificata con trasporto simulato. Aggiornamento successivo: il provider Gemini è tornato raggiungibile e configurato; la prova reale giornaliera resta rinviata e va ripetuta su richiesta.
- **Nota storica sulla risposta Gemini (18 novembre 2026)**: la richiesta grezza restituisce `400 FAILED_PRECONDITION — User location is not supported for the API use`. L’IP pubblico dell’istanza è `95.235.2.120` (Telecom Italia, AS3269, Puglia); più database geografici lo indicano in Italia e Scamalytics lo classifica a basso rischio. Non ci sono proxy/VPN, IPv6 non è disponibile e Cloudflare protegge solo l’ingresso di `sicoli.ovh`, non il traffico uscente verso Google. Il problema è quindi la **classificazione dell’IP pubblico da parte di Google**, coerente con il fatto che riavviare il router (nuovo IP) lo risolve temporaneamente e che succede anche ad altre integrazioni Google. Segnalazione consigliata: `https://support.google.com/websearch/workflow/9308722`. Workaround: nuovo IP dal router, IP statico/aziendale, oppure provider AI diverso (OpenAI).

## Archivio — pulizia fotografie (18 novembre 2026)

- Nuovo strumento in **Archivio e backup**: `GET /api/photos/orphans` elenca i file della cartella foto non più collegati a piante, prodotti, specie, raccomandazioni o proposte; `POST /api/photos/cleanup` elimina solo i nomi richiesti, ricontrollando i riferimenti.
- Le foto caricate nell’ultima ora sono **protette**, così un caricamento in corso non viene cancellato; le piante nel cestino continuano a mantenere le loro foto finché non vengono eliminate definitivamente.
- La UI mostra numero e dimensione delle foto non utilizzate, i file recenti protetti e richiede una seconda conferma prima dell’eliminazione.
- Verifica su archivio sintetico: due file orfani (uno vecchio, uno recente), report 1 eliminabile + 1 protetto, eliminazione del solo vecchio e rimozione della miniatura; riferimenti e file recenti intatti. **208 test backend** (3 nuovi), **948 chiavi i18n**, build ok.

## Dettaglio pianta — menu azioni nativo (18 novembre 2026)

- Su telefono il pulsante **⋯** apre un menu in stile nativo con **Modifica** e **Sposta pianta**, con icone, sfondo traslucido e angoli arrotondati; il vecchio selettore “Registra una cura” è stato rimosso dal menu, perché le azioni rapide sono già nell’hero.
- Il menu si chiude toccando fuori o con Esc; “Modifica” apre l’editor, “Sposta pianta” apre il modulo di spostamento.
- Verifica a 430 px: menu 300×132 px, due voci, ancorato in alto a destra, nessun overflow. Build e **956 chiavi i18n**.

## Collezione — azioni rapide sulle card (18 novembre 2026)

- Ogni card della collezione ha un menu **⋯** con **Registra annaffiatura**, **Modifica** e **Sposta nel cestino**, equivalente al menu contestuale e alle azioni swipe del nativo.
- “Registra annaffiatura” apre il modulo di cura già impostato; “Modifica” apre l’editor; il cestino chiede conferma e mantiene il ripristino entro 30 giorni.
- La card resta interamente cliccabile per aprire la scheda; il menu non annida pulsanti dentro il pulsante principale ed è accessibile da tastiera.
- Verifica su archivio sintetico a 686 px: tre voci presenti, modulo annaffiatura, editor e conferma cestino aperti correttamente; nessun overflow orizzontale. Build e **937 chiavi i18n**.

## Impaginazione della modifica pianta (18 novembre 2026)

- Il form segue ora l’ordine delle sezioni native: **Foto, Identità, Posizione, Profilo fisico, Vaso e substrato, Modalità del piano, Attività aggiuntive, Altre informazioni**.
- Ogni campo usa il modello nativo `EditorValueField`: **controllo in alto, etichetta caption sotto**, a tutta larghezza; le sezioni sono card con bordo e sfondo tenue. Il selettore file della foto è nascosto e l’intera area è cliccabile.
- La spiegazione della modalità (Manuale/Verdant/AI) è accanto al selettore del piano, non in fondo al form.
- La **scheda pianta desktop** usa ora la stessa struttura del telefono e del nativo: hero, griglia **“In sintesi”** a due colonne (acqua, concime, rotazione, potatura, rinvaso, luce, posizione, dal, altezza, vaso, più controllo e diario quando attivi) e pila di **card richiudibili**. Le schede a tab sono state rimosse; i filtri Piano/Sicurezza/Diario continuano a mostrare solo il contenuto pertinente.
- Verifica: 686 e 1280 px senza overflow, sezioni nell’ordine nativo, apertura card e filtri Piano/Sicurezza, salvataggio e rilettura della pianta con versione incrementata. Build, **933 chiavi i18n**, **205 test backend**.

## Modalità di piano nel form — Verdant (18 novembre 2026)

- L’editor espone ora le tre modalità native **Manuale / Verdant / AI**; prima “Verdant” (valore interno `Intelligente`) compariva solo sulle piante già in quella modalità.
- Scegliendo Verdant, il salvataggio calcola il piano con la **località predefinita** e il meteo Open-Meteo, aggiorna gli intervalli e registra il piano; se manca la località o il servizio non risponde, la pianta resta invariata e l’editor mostra un errore. Manuale conserva gli intervalli; AI resta gestita dalle proposte giornaliere.
- Il campo **Posizione reale** compare quando si sceglie Verdant e viene salvato nel piano.
- Verifica su archivio sintetico: Ficus manuale passato a Verdant, piano con località Roma, meteo attivo, irrigazione ricalcolata a 9 giorni; tre opzioni visibili a 1280 e 390 px senza overflow. Build, **932 chiavi i18n**, **205 test backend** (4 nuovi su selezione e fallimenti del piano).

## Pubblicazione su Home Assistant — C1–C6 (18 novembre 2026)

- Sorgenti allineati a `f07c105` copiati nell’add-on: **103 file verificati SHA256**, ricostruzione riuscita, add-on `started` alla versione **0.11.1** (nessun cambio di versione).
- Verifica in Ingress a 686 px sull’archivio reale: Impostazioni con **Località predefinita** e ricerca Open-Meteo “Lecce” (otto risultati, nessun salvataggio), **Sposta pianta** nella scheda, calendario con tre **Rinvia** e attività raggruppate, tabella Misure con `sensor.dracena_*` e “Affidabilità non disponibile”; nessun overflow orizzontale.
- Aggiornamento successivo `4201ee8` (modalità Verdant nel form): **104 file verificati SHA256**, rebuild riuscito e add-on avviato. In Ingress l’editor mostra le tre opzioni **Manuale / Verdant / AI**; nessun salvataggio sul dato reale, nessun overflow a 686 px.
- Aggiornamento successivo `817e349` (impaginazione nativa): **104 file verificati SHA256**, rebuild riuscito e add-on avviato. In Ingress a 686 px l’editor mostra le otto sezioni nell’ordine nativo, i campi con controllo sopra ed etichetta sotto, le tre modalità e la scheda pianta con hero, “In sintesi” e card richiudibili; nessun salvataggio sui dati reali e nessun overflow. Struttura desktop verificata a 1280 px in locale.
- Aggiornamento successivo `966fee9` (azioni rapide e pulizia foto): **105 file verificati SHA256**, rebuild riuscito e add-on avviato. In Ingress le card mostrano il menu con annaffiatura/modifica/cestino e lo strumento Archivio elenca **1 foto non utilizzata da 0,7 MB**, senza eliminarla.
- Aggiornamento successivo `a757c39` (motore di cura operativo): **107 file verificati SHA256**, rebuild riuscito e add-on avviato. In Ingress `/api/settings` e `/api/plants/{id}/care-engine` riportano **active**; la prova AI reale con Gemini è stata rifiutata per la località dell’istanza, senza proposte né modifiche ai piani.
- Correzione `abe6ee1`: la refactorizzazione delle card per il menu rapido aveva spostato la griglia a due colonne sul contenitore esterno, rendendo le righe della collezione troppo larghe e con testo spezzato su telefono. La griglia è ora su `.plant-card-main`; verificato a 430 px: card 396 px, colonne 76 px + 278 px, titolo “Avocado” su una riga e nessun overflow. **107 file** pubblicati, rebuild riuscito.
- Nessuna cura registrata, nessun rinvio confermato e nessun dato reale modificato durante le verifiche.

## Schermate — confronto con il nativo (17 novembre 2026)

- Confronto di dettaglio pianta, collezione, cure, prodotti, misure e impostazioni dai sorgenti Swift: [SCREENS_COMPARISON.md](SCREENS_COMPARISON.md).
- Lacune principali: **cestino con ripristino a 30 giorni** (oggi l’eliminazione è definitiva), filtro categoria e “registra utilizzo” nei prodotti, azione “Sposta pianta”, località predefinita nelle impostazioni.
- Le funzioni principali di calendario, cronologia, giro, misure e sensori risultano presenti; il confronto puntuale sul campo resta da fare.

## Home — allineamento al nativo (17 novembre 2026)

- Rimossa dalla Home l’anteprima “Le tue piante” con 6 schede: ripeteva in parte la collezione e non esiste nella Panoramica nativa; il collegamento alla collezione resta nella scheda Piante.
- Indicatori allineati a **Piante / Da curare / Ambienti**; scheda meteo in intestazione dal piano adattivo più recente; riga metriche con cure 30 giorni, giornate attive, regolarità e piante da osservare. Restano l’anello salute e il ritmo 14 giorni come approfondimento, l’attenzione per azione e il banner AI.
- Verifica: riga metriche 28/18/100%/2 sull’archivio sintetico; build, **850 chiavi i18n**, 180 test backend; Home senza elenco piante e senza overflow.

## Confronto con il nativo — modifica pianta (17 novembre 2026)

- Confronto campo per campo tra `PlantEditorView.swift` e il form web: **38 voci**, 17 presenti, 4 parziali, 17 assenti (posizione reale, metodo di coltivazione, altezza/volume vaso, qualità drenaggio, cachepot, sottovaso, substrato e proprietà, ritmo delle cure, ultima fertilizzazione, tipo/dose fertilizzante, identificazione nel form).
- I dati mancanti sono già nell’archivio reale (`plantingMethod`, `careFrequencyPreference`, `fertilizerDose`, `lastFertilized`, `fertilizerType`, `setup.container`): l’allineamento è quasi tutto interfaccia. Proposta in tre tranche in [PLANT_EDITOR_COMPARISON.md](PLANT_EDITOR_COMPARISON.md).

## Scheda pianta — allineamento al nativo (17 novembre 2026)

- Il form include ora posizione reale (dal piano), metodo di coltivazione, altezza, ritmo delle cure con ridimensionamento degli intervalli, ultima fertilizzazione, tipo e dose del fertilizzante, interruttori delle attività con valori predefiniti e valori iniziali per una nuova pianta (altezza 30, vaso 18 in terracotta, drenaggio attivo).
- Nuova sezione “Vaso e substrato”: qualità del drenaggio, altezza e volume del vaso, cachepot, sottovaso, substrato con nome e proprietà (ritenzione, drenaggio, aerazione). I valori viaggiano in `setup.container` e `setup.substrate`; materiale, diametro e fori restano sincronizzati con i campi esistenti.
- La scheda pianta mostra **Altezza** quando presente; la sintesi iOS mostrava già Posizione, Vaso e Altezza.
- Resta l’identificazione Pl@ntNet dentro il form (il web ha lo strumento separato).
- Verifica: salvataggio e rilettura su archivio sintetico di `setup` (vaso con qualità, altezza, volume, cachepot, sottovaso; substrato con tre proprietà), ritmo “Diradata” con acqua 7→8 giorni, attività con intervallo, ultima fertilizzazione e tipo. Build, **843 chiavi i18n**, 180 test backend.
