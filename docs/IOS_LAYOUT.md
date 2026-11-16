# Confronto e riallineamento a Verdant iOS — 16 novembre 2026

Priorità dell’utente: prima il layout attuale di Verdant su iOS; desktop e altri step rimandati. La revisione è installata su Home Assistant nella release 0.10.0. Sfondo bianco conservato come richiesto.

## Riferimenti osservati

Build dell’app Swift originale per simulatore, senza modificare i sorgenti, in `/private/tmp/plantcare-native-visual-build`. Esecuzione su iPhone 17 Pro / iOS 26.5, con le quattro piante dimostrative native (Olivia, Pico, Nora, Basil), senza configurare server o chiavi. Non avviato l’archivio macOS personale.

Schermate native acquisite: panoramica, piante, scheda Olivia, calendario, strumenti. Screenshot originali completi in `screenshots/visual-audit/native-ios-*.jpg`. Riferimenti desktop preesistenti conservati; nessun riallineamento desktop eseguito in questo incremento.

## Modifiche mobile

| Schermata | Riferimento nativo | Revisione web |
|---|---|---|
| Navigazione | Titolo grande, pulsante aggiunta, cinque tab flottanti | Titoli iOS, aggiunta compatta con nome accessibile, tab flottanti con area di tocco ampia |
| Panoramica | Saluto, settimana scorrevole, riepilogo verde e statistiche | Stessa gerarchia; testi e giorni ingranditi; scorrimento interno della settimana |
| Piante | Lista con immagine, nome, specie e ambiente; scelta Piante/Ambienti | Righe con immagini 76 × 86 px, nome 19 px, specie 15 px, ambienti navigabili e ricerca |
| Scheda | Foto ampia con titolo e cinque azioni; In sintesi; sezioni | Hero con titolo sovrapposto, Acqua/Concime/Salute/Luce/QR, otto dati di riepilogo, accessi alle sezioni e menu per le altre cure |
| Cure | Titolo, selettore Calendario/Cronologia, mese e giorni, stato vuoto | Titolo e selettori leggibili, pulsante Vista mensile con testo, settimana scorrevole, stato vuoto più ampio |
| Strumenti | Gruppi Scopri/Assistenza e righe descrittive | Gruppi e righe; apertura dello strumento in una pagina con ritorno a Strumenti; ordine di lettura coerente |
| Prodotti | Elenco con foto da 76 px e dettaglio separato (FertilizerViews.swift) | Ricerca/categoria, elenco, dettaglio con foto da 280 px e azioni esistenti; sfondo foto bianco |
| Moduli | Testi e controlli touch nativi | Campi 17 px, colonna singola, pulsanti principali da almeno 44 px; zoom browser non disabilitato |

Il dettaglio «Luce» apre le misure disponibili nella web app. Non è stata introdotta una misura tramite fotocamera. Non è stato inventato un indice numerico di salute: il riepilogo usa soltanto i dati già presenti. Le sezioni web si aprono come sottopagine, mentre il nativo usa anche pannelli espandibili. Icone, vetro e controlli SwiftUI non sono identici ai componenti HTML. I gruppi riportano gli strumenti già implementati; non aggiungono funzioni mancanti del nativo.

## Verifiche

- Build TypeScript/Vite passata e 140 test backend passati; nessun cambiamento al motore AI o alle regole di cura.
- Browser a 320, 390, 402 e 430 punti: scheda senza scorrimento orizzontale; corretta la larghezza minima della foto sui telefoni stretti.
- Piante/Ambienti, scelta stanza, scheda, riepilogo, apertura del piano, QR, menu di tutte le cure e modulo Acqua verificati. Modulo chiuso con Annulla: nessuna cura registrata.
- Guida di cura aperta dal gruppo Assistenza; lista degli strumenti nascosta durante la consultazione e ritorno disponibile.
- Fotografia di un prodotto nativo verificata soltanto nella collezione locale di anteprima: immagine caricata, dettaglio 280 px, proporzioni conservate e sfondo bianco. Nessuna modifica alla collezione personale.
- Cambiamenti di stile limitati a larghezze fino a 760 px. Le nuove parti iOS sono nascoste sulle altre dimensioni.

## Anteprima

`ios-preview.html` contiene il riferimento nativo e un’anteprima interattiva web da 402 punti. Il riferimento è ritagliato soltanto tramite CSS, lasciando intatto lo screenshot originale. Include la barra di stato del simulatore; la web app vive nel contenitore Home Assistant e non disegna una barra di stato iOS fittizia.

Il server di anteprima usa un archivio separato in `/private/tmp/plantcare-visual-preview`. L’anteprima rimane separata dalla collezione Home Assistant. Nessun backup, migrazione DB o modifica al motore.

## Rifiniture 0.10.0

Lista Piante ordinata alfabeticamente solo su mobile. Foto di piante e prodotti ingrandibili in un visualizzatore a tutta schermata, con chiusura e collegamento all’originale. Verificati entrambi con fotografie reali copiate soltanto nell’archivio temporaneo di prova: foto caricata, dialogo visibile e dimensioni 390 × 844 px. Prodotti e scheda verificati a 320/390/402/430 px, senza scorrimento orizzontale. Modulo fotografico disponibile anche quando il dettaglio prodotto nasconde il resto della pagina. Script ripetibile di collaudo: `scripts/preview_ios.py`, archivio temporaneo e credenziali assenti.

## Distribuzione e collaudo Home Assistant

0.10.0 installata e in esecuzione il 16 novembre 2026. 55 file sorgente trasferiti e verificati tramite SHA256; build e smoke ARM64/AMD64 passati. Pacchetto sorgente circa 246 KB, integro e senza fotografie o credenziali native. Opzione backup disattivata durante l’aggiornamento.

Safari responsive, 390 × 844: panoramica e collezione reale (18 piante), elenco prodotti, dettaglio Fosforo e fotografia reale nel nuovo visualizzatore a tutta schermata verificati. Visualizzatore chiuso correttamente; Safari riportato alla visualizzazione normale. Screenshot in `screenshots/0.10.0/`. Nessuna cura o piano reale modificato. Il collaudo Companion/iPhone fisico resta distinto dalla prova responsive WebKit.

## Rifinitura richiesta dopo la 0.10.0

Barra inferiore abbassata di 8 px: rimosso il margine aggiuntivo, conservando `env(safe-area-inset-bottom)`. Altezza, etichette e aree di tocco conservate. Correzione locale da raggruppare nella prossima release, senza un’installazione separata.

### Icone iOS — 0.10.1

Sostituite le icone a contorno con SVG originali a sagoma piena nella barra principale, nelle cinque azioni della pianta, nelle cure di liste e cronologia e nei principali indicatori del riepilogo. Il riepilogo usa fondi circolari colorati per distinguere le categorie. Il desktop conserva Lucide. Non sono inclusi font o asset SF Symbols: la somiglianza riguarda peso e significato, non una copia esatta dei glifi Apple. Restano da uniformare le icone degli strumenti e delle azioni secondarie.

Build TypeScript/Vite riuscita; anteprima locale verificata usando il Python del virtualenv. Verifica su iPhone fisico distinta dalla prova responsive.

## 0.10.1 — conferma di tutte le cure

Guida rapida aperta come nel nativo, con le nove sequenze fotografiche originali, tre passaggi numerati e icone per ciascun passaggio. Gli asset originali (circa 19 MB) sono codificati in WebP a 960 px: 461.854 byte totali, condivisi tra guide e finestre, senza duplicarli nell’archivio delle piante. Titolo Conferma attività, sottotitolo cura/pianta, data e pulsante Completa; modifica eventi mantiene Salva modifiche. Il controllo salute offre gli stessi sintomi, aree e campi liberi del nativo; i dettagli sono concatenati nella nota secondo CompleteCareSheet.completedNote. Nei progressi è possibile selezionare lo stato della pianta. Le note degli eventi già registrati restano modificabili senza ricomporle o duplicare i dettagli.

Verifiche: 140 pytest; 63 combinazioni diagnosi, 288 valori stagionali e testi delle nove guide confrontati con Swift; note controllate per ordine, separatori e campi vuoti. Build container ARM64/AMD64 riuscite. Anteprima isolata a 390×844: acqua, concime, rotazione, rinvaso, potatura, controllo salute, progressi e trattamento; immagini caricate, nessuna registrazione su archivio reale.

0.10.1 installata su Home Assistant il 16 novembre 2026 con backup disattivato. Verificate in Ingress Safari responsive (390×844) le finestre Annaffia, Concima e Controlla salute su Orchidea Phalaenopsis; fotografie e campi caricati correttamente. Nessuna cura confermata, nessun piano o credenziale cambiato. Safari ripristinato alla visualizzazione normale. Screenshot in `screenshots/0.10.1/`.

## 0.10.2 — riepilogo e scheda iOS

Il riepilogo legge `_schedule`, non le azioni operative raggruppate in `_actions`: conserva così la voce Concimazione anche quando acqua e concime condividono una singola azione. La modalità Frequenze legge gli intervalli salvati; le diciture Scadenze sono quelle native (Tra 1 giorno, Scaduta da N giorni, Non prevista). Mostra anche controllo e diario se configurati, altezza e vaso. Nessun valore di salute stimato o dato inventato. Il pulsante accessibile del riepilogo funziona con tocco, Enter e Space; il tocco delle tessere alterna la rappresentazione come nel nativo.

Foto a rapporto .98, sovrapposizione scura meno verde, valori del riepilogo a 17 px con etichette a 14 px e spazi delle tessere più vicini al nativo. Intestazione compatta con ritorno a chevron e comando piano per modalità: manuale apre modifica, intelligente apre configurazione, AI apre il pannello esistente per le proposte (non avvia una generazione). Il pannello AI web resta distinto dal foglio di configurazione nativo.

`in-ha` viene applicata solo con impostazione Ingress del server e finestra incorporata. La barra non aggiunge un secondo safe-area inset all’interno del contenitore HA; fuori da Ingress continua a usare env(safe-area-inset-bottom). Il comportamento fisico del Companion richiede verifica sul dispositivo: il collaudo responsive non emula gli inset reali dell’iPhone. L’intestazione esterna di HA resta gestita da HA.

Verifiche locali: `node scripts/verify_ios_summary.mjs` copre concime raggruppato, scadenza rinviata, intervalli mancanti, frequenze e diciture; build TypeScript/Vite riuscita. Anteprima con `--paired-care` e archivio temporaneo: acqua e concime Tra 2 giorni, controllo Tra 7 giorni, diario Tra 14 giorni; cambio rappresentazione con Enter. Larghezze 320/390/430 px senza overflow orizzontale e tab di almeno 54 px.

0.10.2 installata e in esecuzione su HA il 16 novembre 2026 con backup disattivato. Verificata la scheda Avocado del confronto utente in Safari responsive 390×844: Annaffiatura e Concimazione Tra 2 giorni; Frequenze Ogni 7 giorni / Ogni 21 giorni. Altezza 30 cm e vaso Plastica · 18 cm letti dai dati esistenti. Barra visibile al bordo inferiore del riquadro Ingress. Nessuna cura o piano modificato; 18 piante conservate, Safari ripristinato. Screenshot in `screenshots/0.10.2/`; prova su Companion fisico ancora da confermare. Pacchetto circa 0,72 MB con gli stessi asset condivisi della 0.10.1.

## 0.10.3 — sezioni espandibili

Le sezioni della pianta si aprono nella scheda, conservando foto e riepilogo nel documento, con intestazione a icona bianca su cerchio colorato e chevron. Una sezione aperta alla volta: il corpo condiviso viene montato una sola volta, evitando moduli, listener, ID e richieste duplicate. Questo rimane distinto dal nativo, che consente più disclosure indipendenti. Le azioni rapide e il comando AI scorrono alla sezione richiesta. Supportati Enter, Space, aria-expanded e regioni nominate; lo scorrimento rispetta prefers-reduced-motion.

Cronologia e crescita sono separate su iOS; il desktop continua a mostrare entrambe nel Diario. Prodotto assegnato con foto e dose esplicita calcolata secondo FertilizerProduct.explicitDosage: frazioni, range, volume di diluizione conservato e arrotondamento ties-to-even. Il fallback Intl è verificato separatamente. Note mostrate solo se presenti. Profilo e cura include la consultazione botanica esistente: apertura del pannello non scarica profili né modifica il calendario. Le osservazioni richiamano il Care Engine esistente solo all’apertura della sezione; nessuna generazione AI automatica.

Aggiunte icone SVG originali piene per sezioni, strumenti e cure restanti. Nessun font o asset Apple distribuito. Le nove guide illustrate restano condivise e non vengono duplicate.

Verifiche: 140 pytest, riepilogo Node e 40 dosaggi confrontati con il metodo Swift originale, ripetuti con fallback Intl. Browser isolato: tutte le sezioni aperte e chiuse, prodotto con mezza dose 5–10 ml per 1 litro, diario separato dalla cronologia, note e tastiera. Prodotto a 320/390/430 senza overflow; Diario desktop a 1440 con entrambi i gruppi. Nessun salvataggio su archivio reale.

Restano nel confronto nativo: grafico della timeline, indice salute calcolato dal motore nativo (non introdurre valori stimati), confronto completo dei moduli album/crescita e luxmetro tramite fotocamera. La prova nel Companion fisico rimane distinta dalla verifica responsive in Safari.

0.10.3 installata e in esecuzione su Home Assistant il 16 novembre 2026, senza backup. Collaudo Ingress Safari responsive 390×844 su Avocado: prodotto Compo con foto reale e dose 10 ml per litro d’acqua, diario crescita 6 aggiornamenti e cronologia separata 23 attività. Nessuna cura confermata o modifica del piano; collezione ancora a 18 piante. Screenshot `screenshots/0.10.3/home-assistant-assigned-product.jpg`. Nessuna nuova immagine aggiunta all’archivio operativo: il componente usa le foto esistenti.
