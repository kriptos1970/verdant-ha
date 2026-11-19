# Motore di cura — Manuale, Verdant e AI

Ultimo aggiornamento: 19 novembre 2026 · versione 0.11.7

Il “motore di cura” comprende **due livelli indipendenti**:

1. **Piano della singola pianta** (`carePlanMode`): **Manuale**, **Intelligente / Verdant** oppure **AI**. Decide come nascono e come si aggiornano gli intervalli di annaffiatura e concimazione.
2. **Motore operativo globale** (`care_engine_mode`, opzione dell’add-on): **Solo osservazione (shadow)** oppure **Operativo**. Decide se una raccomandazione basata sui sensori può spostare una scadenza.

Non sono la stessa cosa. Una pianta Manuale può ricevere un rinvio automatico dal motore operativo quando questo è attivo; una pianta Verdant non lo riceve se il motore è in shadow.

## Confronto rapido

| | **Manuale** | **Verdant (Intelligente)** | **AI** |
|---|---|---|---|
| Intervalli | quelli impostati dall’utente | calcolati dal pianificatore | proposti dal provider |
| Meteo e stagione | no | sì, ricalcolo giornaliero | come contesto della proposta |
| Apprendimento dalle cure | no | sì, ±1 giorno per volta | no, decide il modello |
| Località predefinita | non necessaria | obbligatoria | non necessaria |
| Quando cambia | solo se si modificano gli intervalli | creazione, ricalcolo, spostamento, refresh giornaliero, annaffiatura completata | analisi giornaliera o manuale, poi applicazione della proposta |
| Controllo | totale | automatico ma prudente | proposta con anteprima |
| Rinvii manuali | sì | sì | sì |
| Motore operativo | sì, se attivo | sì, se attivo | sì, se attivo |

---

## Manuale

- Gli intervalli sono **esattamente** quelli impostati: `wateringInterval` e `fertilizingInterval` vengono usati dal calendario senza meteo, stagione o apprendimento.
- Il **Ritmo delle cure** (Molto frequente → Molto diradata) non è un’auto-regolazione: nell’editor riscala subito gli intervalli correnti (×0,7–1,3) nel momento in cui si cambia la voce. È una scorciatoia dell’utente, non un ricalcolo del motore.
- Il motivo mostrato è “Intervallo manuale scelto da te”.
- Un **rinvio** sposta solo quella scadenza e non modifica l’intervallo.
- In modalità operativa, anche una pianta Manuale può ricevere il **rinvio automatico per terreno umido**. Se si vuole un controllo completamente manuale, il motore operativo va lasciato in shadow nella configurazione dell’add-on.

## Verdant (Intelligente)

### Come nasce il piano

Alla creazione, al passaggio a Verdant o al ricalcolo:

1. viene richiesta la **località predefinita** (latitudine e longitudine);
2. vengono letti da Open-Meteo temperatura media dei prossimi 7 giorni, umidità relativa e pioggia prevista;
3. il pianificatore parte da specie, famiglia e, se presente, scheda botanica salvata;
4. applica la **Posizione reale** (Pieno sole, Balcone riparato, Ombra, Mezza ombra, Patio, Pianerottolo, Interno luminoso, Interno poco luminoso);
5. corregge per temperatura, umidità e pioggia (solo per posizioni esterne);
6. applica la **stagione** in base al mese e all’emisfero (latitudine);
7. applica le soglie di sicurezza, soprattutto per succulente e piante ad alta riserva idrica;
8. allinea la concimazione a un multiplo dell’annaffiatura.

Fattori principali:

| Fattore | Effetto |
|---|---|
| Posizione | da ×0,75 (Pieno sole) a ×1,55 (Ombra per succulente) |
| Temperatura ≥ 30 °C | ×0,80 |
| Temperatura ≥ 25 °C | ×0,90 |
| Temperatura < 12 °C | ×1,25 |
| Umidità < 40% | ×0,95 |
| Umidità > 75% | ×1,10 |
| Pioggia > 15 mm, solo all’aperto | ×1,15 |
| Crescita attiva | ×0,95 |
| Riposo vegetativo | ×1,20 e concimazione diradata |
| Transizione | ×1,00 |

L’annaffiatura viene limitata tra 2 e 35 giorni (12–60 per le succulente, con minimo dipendente dalla posizione); la concimazione è sempre un multiplo dell’intervallo d’acqua.

### Apprendimento dalle cure

Dopo almeno **3 annaffiature completate** e **2 intervalli**:

- si considerano le ultime 7 annaffiature completate;
- si calcola la mediana dei giorni tra un’annaffiatura e la successiva;
- il valore viene contenuto entro ±30% rispetto alla base Verdant;
- l’intervallo corrente si muove di **±1 giorno** verso quel valore;
- la confidenza cresce con il numero di intervalli osservati.

L’apprendimento si applica:

- quando si registra un’annaffiatura completata, se la pianta è in Verdant e il piano non è stato bloccato da una modifica manuale o da una revisione AI;
- durante il refresh giornaliero.

Non si applica alla **concimazione**: viene solo riallineata all’intervallo d’acqua. I **rinvii non addestrano** il motore: contano solo le annaffiature completate.

### Quando si ricalcola

| Momento | Comportamento |
|---|---|
| Creazione o passaggio a Verdant | Calcolo immediato con località e meteo |
| “Ricalcola piano” | Anteprima, poi applicazione |
| Spostamento della pianta | Ricalcolo immediato con l’ultimo clima salvato |
| Una volta al giorno | Primo ciclo dello scheduler dopo la mezzanotte locale, al massimo una volta per pianta al giorno |
| Annaffiatura completata | Aggiornamento immediato dell’apprendimento |

Il refresh automatico giornaliero avviene solo se la pianta è in **Verdant** o **AI**, ha già un piano e il piano ha il **meteo attivo**. Se nell’editor Verdant si disattiva “Usa il meteo”, il piano non viene più ricalcolato da solo.

Se gli intervalli vengono modificati a mano, il piano passa a `Modifica manuale`: il refresh continua ad aggiornare stagione e clima, ma **non tocca più i numeri scelti**. Una revisione AI su un piano Verdant viene conservata finché la motivazione ha evidenza; per le piante in modalità AI il refresh conserva comunque gli intervalli AI.

### Cosa non usa

Il pianificatore usa **Posizione reale**, non il campo **Esposizione** (Luce bassa/indiretta/intensa/sole diretto). L’esposizione serve solo come ripiego per la soglia minima delle succulente. Due piante con la stessa posizione e esposizione diversa ottengono quindi lo stesso piano.

## AI

- L’analisi giornaliera considera **solo le piante in modalità AI**.
- Parte una volta al giorno all’orario `ai_update_time` (predefinito **03:00**) oppure su richiesta con “Analizza ora”.
- Il provider riceve: intervalli correnti, base Verdant, ritmo delle cure scelto, ambiente, luce, stagione e clima salvato, ultime cure, prodotto fertilizzante e dati del vaso.
- Le proposte sono validate:
  - devono dichiarare sufficiente evidenza e una motivazione concreta;
  - l’annaffiatura resta entro **±25%** della base Verdant, rispettando la soglia minima della specie;
  - la concimazione viene allineata a un multiplo dell’annaffiatura;
  - una proposta uguale agli intervalli correnti viene scartata.
- Con `auto_apply_ai` disattivato (comportamento predefinito), le proposte **aspettano l’approvazione** in “Piano AI”. Applicandole, gli intervalli e il piano vengono aggiornati con revisione AI e una voce in cronologia.
- Per le piante in modalità AI il refresh giornaliero **conserva** gli intervalli AI. Una revisione AI su un piano Verdant viene conservata finché la motivazione ha evidenza; senza evidenza il piano può tornare alla base Verdant/apprendimento.

L’assistente AI della scheda pianta è separato: risponde a una domanda e non ricalcola il piano.

## Motore operativo (shadow / operativo)

È indipendente dalle tre modalità e si configura **solo** con l’opzione `care_engine_mode` dell’add-on:

- **shadow**: calcola i consigli e li mostra, ma non modifica le scadenze;
- **operativo**: può **solo rinviare** l’annaffiatura, mai anticiparla e mai registrare una cura.

Il rinvio automatico scatta dopo una misura manuale o un campionamento dei sensori quando:

- la misura di umidità del terreno è fresca (massimo 12 ore) e affidabile (≥ 65%);
- il terreno è ancora umido oltre la soglia;
- la confidenza della raccomandazione è sufficiente (≥ 35% per umidità ≥ 70%, ≥ 55% negli altri casi);
- il nuovo orario è almeno 12 ore dopo la scadenza corrente;
- non è già stato applicato un rinvio nello stesso ciclo.

Il rinvio è limitato a **14 giorni**, viene scritto in `nextWateringOverride` e lascia una voce “Aggiornamento piano” nel diario. Con la stessa lettura non viene applicato due volte. Il rinvio manuale di una cura completata azzera l’override.

Il motore operativo **non controlla** la modalità del piano: se è attivo, può rinviare anche una pianta Manuale.

## Rinvii e ritardi: non sono la stessa cosa

- **Rinvio**: un evento con stato `postponed` e una data `postponedUntil`. Sposta solo quella scadenza; non cambia l’intervallo e non entra nell’apprendimento.
- **Ritardo**: un’annaffiatura completata dopo la scadenza senza un rinvio registrato. È una cura completata a tutti gli effetti e contribuisce agli intervalli osservati; non viene trattato come un rinvio.
- Un rinvio viene considerato solo se è più recente dell’ultima annaffiatura completata.
- Quando si completa un’annaffiatura con la concimazione in scadenza, l’app può registrare anche la concimazione. Se non viene inclusa, la concimazione viene rinviata alla prossima annaffiatura.

## Tempi di ricalcolo e parametri

| Cosa | Quando |
|---|---|
| Piano Verdant | Creazione/passaggio, “Ricalcola piano”, spostamento, refresh giornaliero, annaffiatura completata |
| Refresh Verdant giornaliero | Primo ciclo dopo la mezzanotte locale; massimo una volta al giorno per pianta; solo con meteo attivo |
| Analisi AI | Ogni giorno dopo `ai_update_time` (03:00) oppure “Analizza ora” |
| Motore operativo | Dopo un campionamento sensori con nuove misure o una misura manuale |
| Calendario e salute | Calcolati in lettura; non riscrivono il piano |

Parametri dell’add-on:

| Parametro | Default | Effetto |
|---|---|---|
| `timezone` | `Europe/Rome` | Mezzanotte, orario AI, calendario |
| `poll_interval_minutes` | 15 | Frequenza dello scheduler: sensori, refresh Verdant, controllo orario AI |
| `ai_update_time` | `03:00` | Ora minima dell’analisi AI giornaliera |
| `care_engine_mode` | `active` | Shadow o operativo; unica fonte, la web UI è in sola lettura |
| `auto_apply_ai` | `false` | Applica automaticamente le proposte AI |

La **località predefinita** non è un’opzione dell’add-on: si imposta in **Impostazioni → Località predefinita** e viene salvata nel database dell’app.

## Limiti attuali

- L’apprendimento si muove di **±1 giorno** e non è ancora modulato dal grado di esperienza o dai rinvii.
- L’analisi AI giornaliera riceve le ultime cure come tipo e data; **non** riceve un elenco strutturato dei rinvii né il nome della località. L’assistente della scheda pianta, invece, vede la località del piano.
- Il pianificatore usa la Posizione reale, non il campo Esposizione.
- La modalità Manuale non è stagionale e non usa il meteo.
- Il motore operativo richiede sensori configurati e la modalità operativa; senza misure fresche non fa nulla.
- Non ci sono notifiche push: le proposte AI e i rinvii compaiono nell’app.

## Riferimenti nel codice

- `backend/adaptive.py`: pianificatore, fattori, apprendimento, refresh giornaliero.
- `backend/domain.py`: intervalli, rinvii, `schedule`, `learning`, `stable_water`.
- `backend/care.py`: registrazione delle cure, rinvii, concimazione abbinata.
- `backend/care_operational.py`: rinvio automatico su terreno umido.
- `backend/care_engine.py`: raccomandazioni e fattori dei sensori.
- `backend/ai.py` e `backend/ai_support.py`: analisi giornaliera, proposte e assistente.
- `backend/settings.py`: opzioni dell’add-on.
