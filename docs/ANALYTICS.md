# Grafici e analisi — fasi 1–2

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
- `dailyActivity` è sempre lunga `min(days, 60)` e include i giorni a zero.
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
