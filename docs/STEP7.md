# Step 7 — riconoscimento e strumenti nativi

## Incremento 0.5.0

In **Altro → Riconoscimento AI** seleziona o trascina una fotografia, indica la parte della pianta e avvia il riconoscimento. L’invio a Pl@ntNet richiede conferma nell’interfaccia. Il server usa lo stesso servizio del nativo, restituisce i primi cinque risultati con percentuale e non salva l’immagine di analisi. JPEG, PNG e WebP sono supportati; per HEIC occorre prima esportare JPEG. La richiesta è ridotta a 2.000 pixel e non contiene EXIF.

**Prepara scheda** apre l’editor con nome, specie, famiglia, categoria e confidenza. La fotografia entra nella cartella configurata soltanto quando si salva la pianta. Annullare la bozza non crea piante o copie fotografiche. Le frequenze richiedono controllo manuale; il piano intelligente può essere configurato dopo il salvataggio. Non vengono inventati dati climatici o date di cure.

In **Altro → Specie botaniche** è disponibile l’anagrafica delle specie importate, con famiglia, genere e sinonimi. Il filtro funziona anche sui sinonimi. Questa biblioteca locale non richiede connessione a servizi botanici.

**Consulta Perenual** è disponibile nei candidati, nella biblioteca e nell’editor della pianta. Invia soltanto il nome della specie al servizio. La risposta mostra la specie effettivamente trovata, fonte/data, acqua, luce, terreno, livello di cura e tossicità se disponibili. Corrispondenze approssimative e schede sintetiche sono indicate esplicitamente. Un dato di tossicità assente è sconosciuto, non «non tossica». La consultazione non modifica frequenze, profili del motore, storico o sicurezza della pianta.

## Configurazione

Nelle opzioni dell’add-on Home Assistant sono disponibili `plantnet_api_key` e `perenual_api_key`, facoltative e mascherate. Riavviare l’add-on dopo la configurazione. Il browser riceve solo lo stato configurato/non configurato. Gemini/OpenAI restano gli assistenti testuali esistenti.

Non sono state copiate automaticamente nuove credenziali da Verdant. Il collaudo dei nuovi servizi usa trasporti simulati, senza consumare quota di account reali.

## Verifica

95 test automatici passati. Nuovi scenari: richiesta multipart nativa, dimensioni/EXIF, consenso, credenziali assenti, organo/immagine non validi, dimensione massima, errori upstream senza credenziali, risposta vuota o malformata, corrispondenza Perenual, sinonimo Goeppertia/Calathea, fallback sintetico 403/429, baseline e arrotondamento irrigazione, dati tossicità sconosciuti, anagrafica locale e impostazioni pubbliche.

Browser locale isolato: selezione file, conferma invio, risposta simulata, scheda Perenual, bozza compilata, salvataggio con foto e apertura dettaglio. Mobile a 390 px: filtro sinonimo e assenza di overflow orizzontale. Nessun dato dimostrativo è stato trasferito su Home Assistant.

Build e smoke container ARM64 e AMD64 passati. I backup del test smoke sono creati solo nell’archivio temporaneo del container, senza rete o volumi operativi. Nessun backup Home Assistant creato.

## Parti successive dello step 7

Nell’incremento 0.5.0 restavano catalogo online completo, Open Plantbook, collegamento guidato dei profili botanici al pianificatore, album salute annotati e QR. Open Plantbook, album e QR sono stati aggiunti nella 0.7.0; catalogo online e collegamento guidato sono stati aggiunti nella 0.8.0. Il diario di crescita preesistente rimane disponibile.

## Incremento 0.6.0 — guide e controllo salute

**Altro → Guide di cura** offre nove guide operative di tre passi, con i testi nativi. Le stesse istruzioni sono espandibili prima di registrare una cura. Sono guide testuali, senza le sequenze fotografiche native.

La scheda della pianta contiene la sezione **Guida**: intervalli generali ideali/tollerabili di luce, temperatura e umidità, sei schede pratiche e ritmo stagionale indicativo. I dati derivano da categoria, esposizione, famiglia, vaso e piano salvati. Sono riferimenti generali nativi, non letture di sensori o un piano da applicare. Il grafico non cambia il calendario.

**Altro → Controllo salute**: scegli una pianta e uno o più sintomi. Il risultato segue le priorità native e offre il collegamento alla scheda. Nessuna cura viene registrata e nessun dato viene inviato a provider AI. Una combinazione selezionata produce un primo controllo, non una diagnosi definitiva.

103 test automatici; 63 combinazioni diagnostiche e 288 valori stagionali confrontati eseguendo Swift originale. Browser isolato: priorità di sintomi, apertura scheda/Guida, istruzioni nel modulo cura chiuso con Annulla e guida rinvaso. A 390 px nessun overflow orizzontale.

## Incremento 0.7.0

Scheda **Salute**: album fotografico con foglia sopra/sotto, fusto e terreno, annotazioni numerate e note. Il nuovo controllo mostra il confronto precedente. La conferma salva quattro foto e un singolo evento salute. Lo stato operativo è protetto da modifiche concorrenti; ripetere la stessa richiesta non duplica sessione o evento. Un errore dopo il caricamento di alcune immagini non crea una sessione parziale; i file non referenziati rimangono disponibili per la futura manutenzione dello step 8, senza cancellazioni automatiche.

**Etichette QR/NFC** in Altro e nella scheda della pianta: QR locale, download PNG, stampa e copia link. Sul telefono si usa la fotocamera del sistema; in PlantCare è possibile incollare etichette web o Verdant per trovare la pianta nella collezione. Nessuna nuova apertura pubblica o porta diretta. Il link HA richiede login. Il collaudo su telefono fisico resta da eseguire.

Open Plantbook usa Client ID e Secret nelle opzioni dell’add-on; prima fonte per la consultazione botanica, con Perenual alternativo. La scheda mostra soglie numeriche disponibili e provenienza. Dati mancanti non vengono presunti. Le credenziali Verdant esistenti sono disponibili per configurare i tre servizi, ma non vengono copiate nei sorgenti o negli archivi di rilascio.

Configurazione 0.7.0 completata su HA per Pl@ntNet, Open Plantbook e Perenual con le credenziali native esistenti, salvate soltanto nelle opzioni riservate. Tre servizi verificati dal Mac senza inviare foto; Open Plantbook verificato anche dall’add-on HA.

## Incremento 0.8.0 — catalogo e piano guidato

Catalogo iNaturalist con ricerca di specie, categorie curate come nel nativo e paginazione (20 risultati di ricerca, 12 per categoria). Cache in memoria di massimo 128 risposte per 15 minuti; nessuna copia delle immagini remote nell’archivio. Fotografie ammesse soltanto con licenza riconosciuta e attribuzione. In assenza di rete sono disponibili i nomi delle selezioni native, esplicitamente segnalati come offline.

Il collegamento al piano usa una proposta botanica conservata sul server per 30 minuti e vincolata alla versione della pianta. La consultazione non modifica le cure. Il profilo richiede selezione esplicita, conferma delle corrispondenze approssimative e frequenza valida; il piano mostra origine e specie prima dell’applicazione. Le regole native di conservazione delle revisioni manuali/AI restano attive. Nessuna modifica alle soglie fisiologiche importate o alle azioni dei sensori.

132 test passati e 4.096 piani equivalenti a Swift. Browser su archivio sintetico: categorie, ricerca, paginazione, bozza annullata, profilo simulato e applicazione del piano (7 → 17 giorni, concime 34). Layout a 390 px senza overflow. Corretto anche il contenitore foto prodotti a bianco puro. Installata e avviata su Home Assistant il 16 novembre 2026, senza backup; foto prodotti bianche verificate in Ingress.
