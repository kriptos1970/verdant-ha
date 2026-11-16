# PlantCare Web

Apri l’interfaccia da Home Assistant. Inizia con una pianta o importa il backup nativo da **Altro → Archivio e backup**.

## Opzioni

- `timezone`: fuso orario del calendario.
- `photo_directory`: `/data/photos` predefinito; `/share/plantcare/photos` per cartella condivisa. Il cambio non trasferisce le immagini automaticamente.
- `max_photo_mb`: dimensione massima delle nuove foto; predefinita 20 MB.
- `measurement_retention_days`: conservazione delle misurazioni, predefinita 365 giorni.
- `exposed_entities`: lista di sensori Home Assistant ammessi. Tutte le altre entità sono escluse.
- `poll_interval_minutes`: frequenza campionamento, predefinita 15 minuti.
- `ai_provider`: `none`, `gemini`, `openai`.
- `ai_model`: modello esplicito; vuoto conserva il riferimento del nativo.
- `gemini_api_key`, `openai_api_key`: chiavi solo lato server.
- `ai_update_time`: ora locale dell’analisi giornaliera.
- `auto_apply_ai`: applicazione automatica; disabilitata di default.

I cataloghi botanici saranno disponibili in un prossimo incremento.

## Backup

Con foto in `/data` il backup dell’add-on deve includere dati e foto. Con foto in `/share` salvare anche la cartella condivisa. L’esportazione ZIP dell’app include entrambi con checksum; richiede spazio temporaneo nel volume dell’add-on.

La versione 0.3.0 aggiunge pianificatore intelligente e consigli basati sui sensori. Questa rimane una versione incrementale: consultare STATUS.md nella documentazione del progetto per le funzioni non ancora trasferite.

## Piano intelligente

Dalla scheda della pianta scegliere **Configura piano intelligente**. Indicare esposizione, località e coordinate; usare un clima manuale oppure abilitare il meteo Open-Meteo. Le coordinate vengono inviate a Open-Meteo solo se si seleziona questa opzione. L’anteprima mostra intervalli e motivazioni; **Applica piano** applica esattamente l’anteprima, che scade dopo 30 minuti o dopo una modifica della scheda.

Il meteo abilitato ricalcola il piano una volta al giorno, al primo campionamento disponibile. In caso di errore gli intervalli precedenti restano conservati. I piani importati non attivano automaticamente richieste meteo. È possibile tornare a Manuale dall’editor della pianta.

Le annaffiature completate consentono l’apprendimento prudente del piano intelligente. Le revisioni manuali e AI restano protette. Le osservazioni del Care Engine sono consultive: non modificano il calendario, non attivano pompe e non equivalgono a una diagnosi. I profili botanici avanzati vengono letti dall’archivio nativo importato; senza profili affidabili il motore richiede ulteriori dati.

Per i sensori autorizzati nelle opzioni, configurare l’associazione a pianta o stanza da **Altro → Sensori**. La validità di una misura HA dipende dalla data originale dell’osservazione: un campionamento ripetuto non la rende più recente né aumenta la confidenza.

## Assistente AI (0.4.0)

Configurare `ai_provider` e la relativa chiave nelle opzioni dell’add-on; i valori predefiniti dei modelli restano quelli del nativo. Da **Altro → Piano AI → Modello dell’assistente** è possibile caricare i modelli disponibili al proprio account e selezionarne uno. La scelta web vale per il provider corrente e viene superata se si modifica `ai_model` nelle opzioni dell’add-on. Il catalogo non garantisce che ogni modello supporti lo schema strutturato: un errore di compatibilità lascia il piano invariato.

Nella scheda della pianta, aprire **AI**, scrivere una domanda e scegliere **Chiedi consiglio**. La domanda e il contesto testuale vengono inviati al provider configurato, con possibile consumo di credito API. Le fotografie non vengono inviate. Il risultato resta nella scheda; una richiesta identica con lo stesso contesto/provider/modello riusa il risultato.

Selezionare le attività desiderate e controllare **Il piano dopo l’applicazione**: questa anteprima considera anche la modalità Manuale/Intelligente/AI e l’allineamento acqua/concime del nativo. Le indicazioni testuali vengono aggiunte alle note. Se la scheda cambia dopo l’analisi occorre un nuovo consiglio. La ripetizione della stessa conferma non crea un secondo evento.

Le analisi giornaliere riguardano le piante in modalità AI. L’applicazione automatica rimane disattivata di default; le proposte generano una notifica persistente in Home Assistant. L’eventuale errore della notifica compare nello stato AI e non fa perdere le proposte.

Le prove di sviluppo usano risposte simulate, senza chiavi reali: il collaudo con il proprio account provider resta da eseguire dopo la configurazione.

Se **Carica modelli disponibili** è disabilitato, controllare che `ai_provider` sia `gemini` o `openai`, con la chiave nel campo corrispondente; salvare e riavviare. `ai_model` deve contenere il nome di un modello specifico, oppure restare vuoto: il nome del provider va in `ai_provider`. Dalla 0.4.1 gli errori distinguono chiave non valida, autorizzazioni, quota e problemi di connessione. Non incollare le chiavi nella chat.

## Importazione con fotografie condivise (0.4.2)

Per collezioni grandi è possibile predisporre nella cartella `photo_directory` le fotografie JPEG denominate con il proprio SHA256 (`64 caratteri esadecimali.jpg`), quindi importare il piccolo ZIP dei metadati con i riferimenti corrispondenti. L’anteprima verifica ogni file esistente prima di considerarlo disponibile; un contenuto modificato viene rifiutato. Le foto restano separate dal database e non sono duplicate durante l’importazione. I riferimenti già eliminati nel diario non generano avvisi di foto attive mancanti.
