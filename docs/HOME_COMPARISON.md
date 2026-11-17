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

## Proposta di allineamento

1. **Indicatori**: valutare Piante / Da curare / Ambienti al posto di Collezione / Da fare oggi / Questa settimana; il dato “Questa settimana” resta utile ma il nativo mostra i luoghi.
2. **Meteo**: aggiungere la scheda meteo in intestazione quando esiste una località o un piano con coordinate, riusando i dati già salvati.
3. **Analisi in Home**: decidere se mantenere l’anello salute (utile e già accessibile) accanto alle metriche native, ed eventualmente aggiungere regolarità acqua e cure negli ultimi 30 giorni.
4. **Attenzione**: valutare l’elenco per pianta come il nativo, invece delle singole azioni.
5. **Banner AI**: mantenerlo come aggiunta web o spostarlo in “Altro”.

Nessuna di queste proposte è implementata oltre alla rimozione dell’elenco piante.
