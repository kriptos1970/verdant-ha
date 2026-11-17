# Confronto con Verdant — Home (17 novembre 2026)

Confronto tra la schermata **Panoramica / Oggi** dell’app nativa e la Home web.

Fonti: `PlantCare2.0/VerdantMultiplatform/Sources/Verdant/DashboardView.swift` (667 righe), riferimento visivo `docs/screenshots/visual-audit/native-ios-overview.jpg`, e il blocco Home di `plantcare_web/frontend/src/main.tsx`.

## Struttura nativa

1. Intestazione: saluto, “Ecco come stanno le tue piante oggi.” e **scheda meteo** con temperatura e località (se disponibile).
2. Agenda della settimana.
3. Riquadro di sintesi della giornata con azione principale.
4. Tre indicatori: **Piante**, **Da curare**, **Luoghi**.
5. **Richiedono attenzione**: fino a 3 piante con cure urgenti.
6. **Come evolve la tua collezione**: quattro metriche (cure 30 giorni, giorni attivi, regolarità acqua, da osservare), grafico a barre degli ultimi 30 giorni, ciambella dei tipi di cura e fino a 6 piante da osservare.
7. **Nessun elenco generale delle piante.**

## Struttura web (dopo la modifica del 17 novembre 2026)

1. Agenda della settimana.
2. Riquadro “Il tuo giardino oggi” con azione principale.
3. Tre indicatori: **La collezione**, **Da fare oggi**, **Questa settimana**.
4. “Il tuo giardino in numeri”: anello salute, ritmo delle cure di 14 giorni, fino a 3 piante da controllare per motivo salute.
5. **Un’attenzione per oggi**: fino a 5 azioni in scadenza.
6. Banner AI quando ci sono proposte.
7. ~~“Le tue piante”: anteprima di 6 schede~~ — **rimossa**: ripeteva in parte la collezione e non esiste nel nativo.

## Differenze principali

| Area | Nativo | Web |
|---|---|---|
| Elenco piante in Home | assente | rimosso il 17 novembre 2026 |
| Meteo in intestazione | scheda con temperatura e località | assente |
| Indicatori | Piante, Da curare, Luoghi | Collezione, Da fare oggi, Questa settimana |
| Metriche analitiche | 4 metriche + barre 30 giorni + ciambella + piante da osservare | anello salute + ritmo 14 giorni + piante da controllare |
| Attività urgenti | per pianta (max 3) | per azione (max 5) |
| Banner AI | assente | presente quando ci sono proposte |
| Ordine | meteo, settimana, sintesi, indicatori, attenzione, analisi | settimana, sintesi, indicatori, analisi, attenzione, AI |

## Stato dopo l’allineamento del 17 novembre 2026

- **Indicatori**: allineati a **Piante / Da curare / Ambienti**.
- **Meteo**: scheda in intestazione con temperatura e località, presa dal piano adattivo più recente; compare solo se esiste almeno un piano (quindi non su collezioni nuove).
- **Analisi**: aggiunta la riga con **cure 30 giorni, giornate attive, regolarità, da osservare**; l’anello salute e il ritmo di 14 giorni restano come approfondimento web.
- **Attenzione**: resta l’elenco per azione, più utile per completare una cura; il nativo elenca le piante.
- **Banner AI**: resta in Home come aggiunta web.

Verifica della riga metriche: 28 cure/18 giornate/100%/2 da osservare sull’archivio sintetico, coerenti con `/api/analytics?days=30`.
