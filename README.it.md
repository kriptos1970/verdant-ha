# PlantCare Web per Home Assistant

**Italiano** | [English](README.md)

Versione incrementale **0.10.3**. Add-on autonomo con React/TypeScript, FastAPI, SQLite e fotografie su filesystem. Nessuna sincronizzazione con le app Apple.

Codice sorgente: [github.com/kriptos1970/verdant-ha](https://github.com/kriptos1970/verdant-ha). Le versioni installabili sono pubblicate nelle GitHub Releases; la cartella locale `releases/` non è versionata. La direzione del progetto è in [ROADMAP.md](ROADMAP.md).

La matrice di riferimento è in [docs/REFERENCE.md](docs/REFERENCE.md); stato, verifiche e differenze dal nativo sono in [docs/STATUS.md](docs/STATUS.md).

## Installazione su Home Assistant OS

1. Copiare **la cartella `plantcare_web` completa** in `/addons/plantcare_web` tramite Samba o Terminal & SSH. Non copiare `.venv`, `node_modules` o archivi personali.
2. Nell’App store di Home Assistant aggiornare l’elenco degli add-on locali e installare **PlantCare Web**.
3. Configurare fuso orario, eventuali entità consentite e provider AI. L’AI è opzionale e disattivata per impostazione predefinita.
4. Avviare l’add-on e aprire **Interfaccia web**. È disponibile Ingress; non serve esporre porte.
5. In **Altro → Archivio e backup** caricare il backup esportato da PlantCare macOS. L’importazione avviene su archivio vuoto, dopo l’anteprima. Non altera gli archivi originali.

Il container viene costruito localmente durante l’installazione. Sono state verificate le build Docker ARM64 e AMD64. La 0.2.0 è stata installata su Home Assistant il 15 novembre 2026, verificando avvio e dashboard tramite Ingress; la 0.4.2 contiene ora la collezione reale importata e verificata nelle viste principali.

## Giro di cure e trattamenti

- **Oggi → Apri il giro di cura**, oppure **Cure → Giro di cure**: scegli l’ambiente e segui le attività di oggi, ordinate per stanza.
- **Completata** registra la cura; **Rimanda a domani** salva un rinvio nel fuso configurato; **Salta** non modifica l’archivio. La lista non si accorcia sotto l’indice durante il salvataggio.
- Quando previsto, conferma esplicitamente la concimazione insieme all’annaffiatura. I prodotti fogliari non vengono abbinati all’acqua.
- **Prodotti → Pianifica ciclo**: scegli pianta, primo intervento, intervallo, numero di applicazioni, eventuale termine, dose e note.
- Nella scheda **Trattamenti** puoi registrare un intervento, modificare, interrompere o riprendere un ciclo. L’interruzione conserva il diario.
- Modificare o eliminare una registrazione ricalcola il numero delle applicazioni. Le applicazioni importate senza registrazioni storiche rimangono conservate.
- **Cure → Calendario/Cronologia**: vista settimanale o mensile e filtri per ambiente, pianta, tipo e date. Le proiezioni mostrano la prossima attività in attesa, senza inventare eventi futuri.

Le cure già salvate restano nell’archivio se esci dal giro. La sessione del giro è temporanea, come nel nativo. Le attività di giorni precedenti restano nel calendario e non vengono reinserite automaticamente nel giro di oggi.

## Dati e fotografie

- Database e stato dell’app: `/data/plantcare.sqlite`, su disco locale dell’add-on.
- Foto predefinite: `/data/photos`.
- Miniature ricostruibili: `/data/thumbnails`.
- Per foto condivise: impostare `photo_directory: /share/plantcare/photos`. La cartella `/share` è montata in scrittura. Non spostare SQLite su una condivisione di rete.
- Il cambio del percorso **non sposta automaticamente** le foto: arrestare l’app, copiare la cartella conservando i nomi, cambiare l’opzione e riavviare. Conservare il percorso precedente fino alla verifica.
- Se si usa un NAS montato da Home Assistant, verificare che il mount sia disponibile prima di avviare l’app. La condivisione non equivale a un backup.
- Le foto nuove sono ridimensionate fino a 2400 px, convertite in JPEG, private dei metadati EXIF e deduplicate per contenuto. Le foto importate sono conservate senza ricompressione.
- Dimensione massima upload configurabile con `max_photo_mb` (20 MB predefiniti); foto di backup nativo fino a 20 MB ciascuna. Miniature da 480 px generate al primo accesso.
- Le misurazioni hanno una conservazione configurabile, predefinita di 365 giorni. Le cure e le foto non vengono cancellate automaticamente.

Quando le foto sono in `/share`, includere la cartella condivisa nel backup HA oppure eseguire un backup dedicato sul NAS. Salvare anche il database nello stesso punto temporale. SQLite resta la scelta attuale; MariaDB esterno è rimandato.

## Backup e ripristino

L’esportazione predefinita produce un **ZIP** con `data.json`, fotografie separate e manifest con checksum SHA256. I file vengono copiati su disco a blocchi, senza trasformare tutta la collezione fotografica in base64 nella RAM. Servono spazio temporaneo e spazio libero sufficienti. Gli archivi temporanei completati vengono eliminati dopo il download.

Importazione: ZIP web fino a 2 GB; JSON nativo con envelope v1–v3 fino a 150 MB. Il formato JSON storico può richiedere più RAM del peso del file; per gli archivi fotografici grandi usare ZIP e i backup Home Assistant. Il ripristino verifica tutti i checksum prima delle scritture nel database e non estrae percorsi arbitrari. I file già presenti non vengono sovrascritti.

Compatibilità JSON web: `GET api/backup?format=json`, consentita soltanto fino a 40 MB di foto.

## Sensori e AI

Impostare `exposed_entities` soltanto con le entità destinate alle piante. Sono accettate temperatura, umidità, luce, umidità del terreno e conducibilità. In **Altro → Sensori** associare una pianta o una stanza. Il token Supervisor rimane nel container.

Per l’AI impostare `ai_provider`, chiave corrispondente e, facoltativamente, `ai_model`. I valori predefiniti conservano quelli dei sorgenti Apple: `gemini-3.5-flash-lite` o `gpt-5-nano`. Se non disponibili nel proprio account, selezionare esplicitamente un modello valido. Nessuna sostituzione automatica di provider.

L’analisi periodica interessa solo le piante con modalità AI e produce proposte. L’applicazione automatica è disattivata, salvo `auto_apply_ai: true`. Le proposte basate su una scheda modificata vengono rifiutate. Le prove dei provider sono simulate; non sono state usate chiavi o eseguite chiamate a pagamento.

## Sviluppo locale

```sh
python3 -m venv .venv
.venv/bin/pip install -r plantcare_web/backend/requirements.lock pytest
npm ci --prefix plantcare_web/frontend
npm run build --prefix plantcare_web/frontend
PLANTCARE_DATA=.data .venv/bin/uvicorn plantcare_web.backend.main:app --host 127.0.0.1 --port 8099 --no-proxy-headers
```

Aprire `http://127.0.0.1:8099/`. In sviluppo non viene usato Ingress: il bind è solo loopback. Per sviluppo frontend con ricaricamento: `npm run dev --prefix plantcare_web/frontend` con backend avviato sulla porta 8099.

```sh
.venv/bin/python -m pytest plantcare_web/tests -q
.venv/bin/python scripts/verify_native.py
docker build -t plantcare-web:0.2.0 plantcare_web
```

`verify_native.py` confronta gli algoritmi Python con il codice Swift originale nella cartella sorella `PlantCare2.0`, senza modificarlo. Richiede Swift disponibile sul sistema.

## Pianificazione intelligente (0.3.0)

Dalla scheda della pianta aprire **Configura piano intelligente**: esposizione, località e clima manuale o meteo Open-Meteo opzionale. Il sistema mostra un’anteprima prima di cambiare il calendario. I piani importati non avviano richieste meteo automaticamente. Le osservazioni avanzate dei sensori restano consultive (modalità shadow).

La 0.3.0 è installata su Home Assistant e la dashboard Ingress è stata verificata in Safari.

Verifiche di equivalenza aggiuntive: `.venv/bin/python scripts/verify_adaptive.py` e `.venv/bin/python scripts/verify_care_engine.py`; eseguono il codice Swift originale dalla cartella adiacente PlantCare2.0, senza modificarlo.

## Assistente AI (0.4.0)

Consigli conservati nella scheda, selezione delle attività da applicare e anteprima del piano effettivo. Catalogo dei modelli da **Altro → Piano AI**; chiavi e provider nelle opzioni Home Assistant. Cache per richieste identiche e notifiche per le proposte giornaliere. I collaudi provider sono simulati: la prova con un account reale richiede la configurazione delle chiavi. Equivalenza delle regole di applicazione: `.venv/bin/python scripts/verify_ai.py`.

La 0.4.0 è installata su Home Assistant; caricamento della dashboard e versione verificati tramite Ingress. Nessun backup Home Assistant creato durante l’aggiornamento.

La correzione 0.4.1 è installata: catalogo Gemini verificato con la chiave di Verdant Server copiata su richiesta dell’utente. Gli errori dei servizi esterni ora mostrano una causa specifica senza esporre credenziali.

La **0.4.2** è installata su Home Assistant: importate le 18 piante Verdant, sette prodotti e 124 foto (375 MB nella cartella condivisa). Verificate collezione, diario, prodotti e calendario. Originali invariati e nessun backup creato. [Dettagli della migrazione](docs/IMPORT.md).

Collaudo Gemini reale completato sul Ficus: risposta e anteprima selettiva verificate, consiglio lasciato da applicare. Dalla 0.4.3 il contesto climatico indica la data del piano salvato e viene distinto esplicitamente dal meteo attuale. I consigli precedenti richiedono rigenerazione.

La **0.5.0** aggiunge in **Altro** il riconoscimento fotografico Pl@ntNet e la biblioteca delle specie importate. Dopo aver scelto un risultato, controlla la bozza prima di salvare. Le schede di coltivazione Perenual sono consultabili dai risultati, dal catalogo locale e dall’editor della pianta. Configura `plantnet_api_key` e `perenual_api_key` nelle opzioni dell’add-on, poi riavvialo. Le credenziali sono facoltative; il catalogo locale funziona senza chiavi. Nessun nuovo servizio cambia automaticamente il piano di cura.

La **0.6.0** aggiunge **Altro → Guide di cura**, **Altro → Controllo salute** e la scheda **Guida** di ogni pianta. Le guide e il primo controllo dei sintomi funzionano localmente, senza chiavi API e senza registrare cure. [Dettagli dello step 7](docs/STEP7.md).

La **0.6.1** corregge la visualizzazione delle fotografie dei prodotti già importate e aggiunge anteprima/caricamento nell’editor prodotto. Nessuna reimportazione necessaria.

La **0.7.0** raggruppa sfondo bianco, album salute con quattro foto annotate, etichette QR/NFC e consultazione Open Plantbook con Perenual alternativo. Le credenziali si configurano nelle opzioni Home Assistant; nessuna chiave entra nel QR.

## Catalogo e profili botanici — 0.8.0

In **Altro → Catalogo botanico** cerca una specie o consulta le quattro selezioni native. «Prepara scheda» apre una bozza da verificare. Le immagini remote con licenza non vengono duplicate nella cartella foto.

Nel piano intelligente, «Consulta riferimento botanico» cerca Open Plantbook con fallback Perenual. Seleziona esplicitamente il profilo e controlla l’anteprima prima di applicare il piano. Le corrispondenze approssimative richiedono conferma; i profili privi di una frequenza affidabile non vengono applicati. Le soglie dei sensori non vengono sovrascritte.

## Archivio e prestazioni — 0.9.0

La collezione carica il diario completo quando apri una pianta. In **Cure → Cronologia**, consulta 50 eventi per pagina usando i filtri abituali. Nel diario della pianta le cure e le storie di crescita hanno pagine separate. Nessun evento viene tagliato o rimosso. Verifiche e limiti in [docs/STEP8.md](docs/STEP8.md).

## Interfaccia iPhone — 0.10.0

Layout mobile riallineato a Verdant iOS: navigazione, lista Piante/Ambienti, scheda con riepilogo, strumenti e prodotti. Testi e foto più grandi; foto ingrandibili a tutta schermata. Il confronto e i limiti sono in [docs/IOS_LAYOUT.md](docs/IOS_LAYOUT.md). Il riallineamento desktop resta rimandato.

## Contribuire

Il progetto è aperto a contributi. Prima di aprire una pull request esegui i test backend e la build frontend:

```sh
.venv/bin/python -m pytest plantcare_web/tests -q
npm run build --prefix plantcare_web/frontend
```

La CI GitHub esegue gli stessi controlli a ogni push e pull request. Non includere credenziali, archivi personali o fotografie dell'archivio operativo nei commit.

## Licenza

Distribuito con licenza [MIT](LICENSE). Copyright © 2026 Maurizio Antonio Sicoli.

Verdant/PlantCare è un progetto indipendente: non è affiliato a Home Assistant, Pl@ntNet, Perenual, Open Plantbook, iNaturalist, Google o OpenAI. I marchi citati appartengono ai rispettivi proprietari.
