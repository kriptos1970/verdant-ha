# Grafici e analisi — fasi 1–6

Prima fase del riallineamento a Verdant iOS/macOS: dati e calcoli, senza ancora toccare l’interfaccia. Tutto è in sola lettura.

## Indice salute

`backend/health.py` è il porting di `Plant.healthAssessment` in `Models.swift`.

- Base 92, normalizzata tra 20 e 100.
- Annaffiatura in ritardo: 8 punti al giorno, massimo 30.
- Concimazione in ritardo: 2 punti al giorno, massimo 12.
- Ultima osservazione (crescita, album salute o evento con stato): eccellente +6, buona 0, in difficoltà −20, malata −35; peso 1 entro 45 giorni, 0,5 fino a 120, poi 0.
- Controllo salute arretrato: 2 + giorni di ritardo, massimo 10.
- Aggiornamento progressi arretrato: 2 + giorni di ritardo, massimo 8.
- Almeno tre misure luce: −4 se lo stato è `veryLow` o `monitorDirectSun`.
- Etichette: `good` da 85, `watch` da 70, `attention` sotto 70.

`domain.plant_view` espone `_health` con `score`, `labelCode`, `tipCode` e `tipParams`. `labelFallback` e `tipFallback` servono ai client che non usano i cataloghi i18n. I codici sono gli stessi delle chiavi `health.label.*` e `health.tip.*` nei cataloghi italiano e inglese.

## Analytics

`GET /api/analytics?days=30` — sono ammessi 30, 90 o 365 giorni.

```json
{
  "days": 30,
  "periodStart": "2026-10-18T12:00:00Z",
  "generatedAt": "2026-11-17T12:00:00Z",
  "plantCount": 18,
  "completedEvents": 42,
  "activeDays": 19,
  "timelinessPercent": 86,
  "dailyActivity": [{"date": "2026-10-19", "count": 0}],
  "careMix": [{"kind": "Annaffia", "count": 20}],
  "rooms": [{"room": "Salotto", "plants": 6, "overdue": 1}],
  "health": {"excellent": 2, "good": 8, "struggling": 1, "sick": 0, "unrated": 7},
  "plantsAtRisk": [
    {"id": "…", "name": "Ficus", "room": "Salotto", "photoPath": "….jpg",
     "daysUntilWatering": -3, "reason": {"code": "watering", "days": 3}, "score": -3}
  ]
}
```

- Gli eventi cancellati e i rinvii non contano.
- `dailyActivity` copre tutto il periodo (`days` giorni) e include i giorni a zero.
- La regolarità confronta ogni intervallo d’acqua registrato con `wateringInterval + 1`, come il nativo.
- L’ultimo stato per l’analisi considera diario di crescita ed eventi, non l’album salute, come `CollectionAnalyticsView`.
- `plantsAtRisk` è ordinata per urgenza e limitata a otto voci; il frontend può mostrarla intera o ridotta.

## Timeline

`GET /api/plants/{id}/timeline?limit=8` unisce eventi attivi e misure, ordinati dal più recente. Le misure native già presenti nel database non vengono duplicate. Gli eventi usano il tipo di cura nel formato italiano dell’API; le misure usano i codici già esposti da `/measurements`.

## Verifica sull’archivio reale (17 novembre 2026)

Lettura in sola lettura delle 18 piante e 732 eventi dell’archivio personale, senza modificare l’istanza.

| Periodo | Cure completate | Giorni attivi | Regolarità acqua |
|---|---:|---:|---:|
| 30 giorni | 103 | 20 | 71% |
| 90 giorni | 495 | 77 | 83% |
| 365 giorni | 677 | 129 | 85% |

- Tipi di cura a 30 giorni: 49 annaffiature, 21 aggiornamenti progressi, 16 rotazioni, 15 concimazioni, 2 aggiornamenti piano.
- Ambienti: Pianerottolo 10 piante, Balcone 5, Mezza ombra · balcone 3; nessuna annaffiatura scaduta.
- Ultimo stato registrato: 13 eccellenti, 5 buone, nessuna pianta in difficoltà o malata, nessuna senza valutazione.
- Indice salute: 13 piante a 98, 5 a 92; tutte `good`.
- Le date di prossima acqua e concime coincidono con `_schedule` della 0.11.1 per tutte le 18 piante.
- Con questo archivio il pannello “Piante da osservare” sarà vuoto: è il risultato corretto, non un errore.

## Verifica

- I casi di `HealthScoreTests.swift` sono riprodotti in `tests/test_health.py`.
- `tests/test_analytics.py` copre periodi, rinvii, cancellazioni, regolarità, ambienti, stato salute, rischio, timeline e contratto HTTP.
- Benchmark locale su 100 piante e 50.000 eventi: analisi in circa 52 ms, indice salute per 100 piante in circa 24 ms, scheda completa per 100 piante in circa 208 ms.

## Fase 2 — componenti grafici (17 novembre 2026)

La pagina Analisi usa ora i dati della fase 1. Recharts resta fuori dal chunk principale e viene caricato solo quando il pannello si avvicina alla vista.

### Architettura

- `chart-kit.tsx` — shell leggera senza Recharts: palette condivisa, `useReducedMotion`, `DeferredSection` con `IntersectionObserver` (`rootMargin` 360 px), `ChartPanel`, `ChartEmpty`, `ChartSkeleton` e `ChartDataTable`.
- `charts.tsx` — unico modulo che importa Recharts 3.11.0: barre dell’attività giornaliera, ciambella dei tipi di cura, barre impilate degli ambienti. Viene caricato con `React.lazy`.
- `health-ring.tsx` — anello del punteggio in SVG puro, senza Recharts, quindi subito disponibile. Mostra la quota di piante valutate in salute (eccellenti + buone).
- `analytics.ts` — tipi del contratto `/api/analytics` e hook `useAnalytics(30)` con annullamento della richiesta precedente.
- `analytics-page.tsx` — pagina eager: titolo, quattro indicatori, anello salute, stati vuoti e caricamento, poi i grafici lazy.

### Caricamento

- La pagina Piante non importa Recharts: `charts.tsx` è un chunk separato (`charts-*.js`, circa 456 kB, 130 kB gzip) richiesto solo entrando in Analisi e solo quando la sezione è vicina alla vista.
- La shell eager (pagina, anello, tabelle) aggiunge circa 13 kB al chunk principale.
- Il grafico non viene montato finché `IntersectionObserver` non lo rileva; su telefono il pannello resta sotto la piega e il chunk non parte prima dello scorrimento.

### Accessibilità e movimento

- Ogni grafico Recharts ha `accessibilityLayer`, `title` e `desc`; l’SVG è raggiungibile da tastiera e ha un nome accessibile.
- Ogni pannello espone i dati in una tabella HTML apribile con “Mostra i dati in tabella”, con `caption`, intestazioni `th scope="col"` e valori numerici allineati. I dati non dipendono dal solo colore: legenda con etichette e conteggi, tabella completa.
- Con `prefers-reduced-motion: reduce` le animazioni Recharts sono disattivate (`isAnimationActive={false}`) e lo shimmer degli scheletri è spento via CSS.
- Gli stati vuoti distinguono collezione vuota, periodo senza cure e ambiente senza piante; il caricamento usa scheletri con `role="status"`.

### Verifica

- Build TypeScript/Vite e controllo i18n: **746 chiavi** italiano/inglese allineate.
- **180 test backend** invariati.
- Controllo visivo su pagina sintetica di 6 piante e 28 cure: 320, 390, 430 e 1280 px, nessun overflow orizzontale; su telefono indicatori 2×2, pannelli a colonna singola e tabelle scorrevoli.
- Rete verificata: il chunk `charts-*.js` non viene richiesto nella pagina Piante; viene richiesto in Analisi solo dopo lo scorrimento fino al pannello.
- La pagina completa 30/90/365 giorni e i grafici di tendenza della singola pianta restano nelle fasi 4 e 6.

## Fase 3 — Home (17 novembre 2026)

La pagina Oggi mette in evidenza lo stato della collezione senza appesantire l’avvio: solo SVG e CSS condivisi, nessun grafico Recharts.

### Contenuto

- `home-insights.tsx`, inserito dopo gli indicatori e prima di “Un’attenzione per oggi”.
- **Salute della collezione** — anello `HealthRing` con la quota di piante valutate in salute, legenda In salute / Da osservare / Non valutate e conteggi.
- **Ritmo delle cure** — ultimi 14 giorni di attività come barre CSS, totale delle cure e giornate attive, con tabella dati apribile.
- **Da controllare** — al massimo tre piante con motivo salute (`sick` o `struggling`), ambiente, stato tradotto e apertura della scheda. Le piante in ritardo solo per annaffiatura restano nel pannello cure, per non duplicare la lista.

### Caricamento e stati

- Il blocco vive in `DeferredSection`: `/api/analytics?days=30` parte solo quando la sezione si avvicina alla vista, con 320 px di anticipo.
- La Home non importa `charts.tsx`: in rete il chunk `charts-*.js` non viene richiesto, né all’avvio né scorrendo.
- Caricamento con scheletri, errore con “Riprova”, stato vuoto della salute quando nessuna pianta è valutata; con collezione vuota il blocco non compare.
- Le chiavi di salute sono condivise con la pagina Analisi tramite `HEALTH_LABEL_KEYS` in `health-ring.tsx`.

### Accessibilità

- Anello e barre hanno un nome accessibile che riporta percentuale, cure e giornate attive; le barre hanno una tabella con `caption` e intestazioni.
- Ogni riga “Da controllare” è un pulsante il cui nome accessibile include nome e stato visibili.
- Colore mai unico portatore di informazione: legenda con etichette, conteggi e tabella. Nessuna animazione, quindi `prefers-reduced-motion` è rispettato per costruzione.

### Verifica

- Build TypeScript/Vite e i18n: **763 chiavi** italiano/inglese allineate (17 nuove per la Home).
- **180 test backend** invariati.
- Archivio sintetico di 6 piante e 28 cure: 60% di salute, 22 cure in 14 giorni su 12 giornate attive, 2 piante da controllare.
- Layout 320, 390, 430 e 1280 px senza overflow orizzontale; una colonna sotto 760 px, due colonne sopra.
- Stati verificati in italiano e inglese: caricamento, errore con “Riprova”, nessuna pianta valutata, collezione vuota.
- Rete: `charts-*.js` assente sulla Home e presente solo in Analisi; `/api/analytics` risponde 200, nessun errore in console.
- Lighthouse sulla Home: accessibilità 0.96, best practice e SEO 1. I due rilievi restano preesistenti (contrasto del piè di pagina/statistiche e nomi accessibili dei giorni del calendario).

## Fase 4 — Andamento nella scheda pianta (17 novembre 2026)

La scheda della singola pianta mostra l’attività di cura degli ultimi dodici mesi, senza introdurre un motore grafico.

### Contenuto

- `plant-trend.tsx`: dodici colonne mensili con annaffiature e altre cure impilate, legenda con i conteggi, totale e mesi attivi.
- I dati arrivano dalla cronologia già presente nella scheda (`plant.history`): nessuna richiesta aggiuntiva e nessun valore stimato.
- Sono esclusi gli eventi eliminati e i rinvii; i mesi sono calcolati nel fuso dell’app, così una cura a tarda sera resta nel giorno giusto.
- Posizione: scheda pianta → Diario, in cima. Su iOS la stessa sezione si chiama “Andamento e cronologia”, quindi il grafico precede storie di crescita e cronologia delle cure.

### Accessibilità e stati

- Le barre hanno `role="img"` con un’etichetta che riporta cure totali e mesi attivi; la legenda riporta i valori, non solo i colori.
- Tabella dati con `caption` e colonne Mese / Annaffiature / Altre cure / Totale, apribile da “Mostra i dati in tabella”.
- Stato vuoto esplicito quando non ci sono cure negli ultimi dodici mesi.
- Nessuna animazione e nessun chunk aggiuntivo: la scheda pianta non carica Recharts.

### Verifica

- Build TypeScript/Vite e i18n: **777 chiavi** italiano/inglese allineate (14 nuove).
- **180 test backend** invariati.
- Scheda della Monstera sull’archivio sintetico: 6 cure in 2 mesi attivi, 2 annaffiature e 4 altre cure, 12 colonne e 12 righe di tabella.
- Layout 320, 390 e 1280 px senza overflow orizzontale; tabella contenuta e leggibile a 320 px.
- Italiano e inglese verificati, compreso lo stato vuoto; nessun errore in console.
- Lighthouse sulla scheda con il grafico: accessibilità 0.95, best practice e SEO 1; i due rilievi restano i preesistenti elementi del riepilogo iOS.

## Fase 6 — selettore 30/90/365 nella pagina Analisi (17 novembre 2026)

La pagina Analisi copre ora i tre periodi previsti dal contratto, con grafici leggibili anche sulle finestre lunghe.

### Selettore

- Tre pulsanti (30 giorni, 90 giorni, 12 mesi) in un gruppo con nome accessibile “Periodo delle analisi” e stato `aria-pressed`; su telefono occupano tutta la larghezza con bersagli da 40 px.
- Il periodo scelto guida `useAnalytics(period)`: la richiesta precedente viene annullata, i dati restano visibili durante il caricamento e il contenitore espone `aria-busy`.
- Il sottotitolo non nomina più 30 giorni: descrive il periodo scelto.

### Grafici nel periodo

- `dailyActivity` copre ora l’intero periodo (30, 90 o 365 giorni), non più un massimo di 60; il payload resta di pochi kilobyte.
- Le barre si raggruppano nel client: giorni a 30 giorni, settimane (lunedì come inizio) a 90, mesi a 365. Titolo e descrizione, didascalia della tabella e intestazione di colonna cambiano di conseguenza.
- Il tooltip della settimana usa “Settimana del {data}”, quello del mese il nome del mese con l’anno.
- Gli altri pannelli (tipi di cura, ambienti, salute) usano già i dati del periodo; nessuna richiesta aggiuntiva.

### Verifica

- Build e i18n: **787 chiavi** allineate (11 nuove, una rimossa).
- **180 test backend**; il test del selettore ora verifica 30, 90 e 365 punti giornalieri.
- Archivio sintetico di 6 piante e 28 cure: 30 giorni → 30 barre giornaliere; 90 giorni → 14 settimane (4, 6, 15, 3 cure nelle ultime quattro); 365 giorni → 13 mesi con 25 cure a novembre 2026.
- Rete: richieste `/api/analytics?days=30`, `days=90` e `days=365` al cambio periodo; nessun errore in console.
- Layout 320, 390 e 1280 px senza overflow; italiano e inglese verificati, comprese le etichette del selettore.
- Lighthouse sulla pagina Analisi: accessibilità 0.96, best practice e SEO 1; unico rilievo il contrasto preesistente del piè di pagina.

## Fase 5 — Linea del tempo della pianta (17 novembre 2026)

La scheda pianta mostra ora anche le misure accanto alle cure, usando l’endpoint costruito nella fase 1.

### Contenuto

- `plant-timeline.tsx` legge `/api/plants/{id}/timeline?limit=12`: eventi di cura e misure uniti, dal più recente.
- La linea è nella scheda pianta → Diario, subito dopo il grafico dei dodici mesi e prima di storie di crescita e cronologia.
- Ogni voce ha un punto colorato per tipo di cura (o verde salvia per le misure), la data breve, l’etichetta e il valore con unità per le misure; i controlli salute mostrano lo stato e i rinvii sono marcati.
- Le etichette delle misure sono tradotte (umidità del terreno e dell’aria, temperatura, luce, conducibilità) e i valori usano il formato numerico locale.
- La richiesta parte all’apertura del Diario, con caricamento, stato vuoto e errore con “Riprova”; nessun motore grafico aggiuntivo.

### Verifica

- Build e i18n: **796 chiavi** allineate (9 nuove).
- Archivio sintetico con due misure inserite solo nella copia di prova: 8 voci in linea, comprese “Umidità del terreno 42 %” e “Temperatura 21,5 °C”, con controllo salute “Eccellente”.
- Layout 320, 390 e 1280 px senza overflow; italiano e inglese; stato vuoto ed errore con “Riprova” verificati.
- Rete: una richiesta `timeline?limit=12` per apertura, nessun chunk `charts-*.js` sulla scheda, nessun errore in console.
