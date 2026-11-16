# Importazione della collezione Verdant — 15 novembre 2026

Origine: archivio SwiftData `VerdantLocal.store` dell’app macOS, aperto con SQLite in sola lettura e transazione coerente. Nessuna modifica alla collezione originale e nessun backup Home Assistant creato.

## Collezione importata

- 18 piante, 7 prodotti, 20 profili botanici.
- 731 eventi di cura: 730 attivi e una registrazione eliminata preservata come tombstone.
- 158 misurazioni con provenienza originale.
- Ambienti: Balcone, Mezza ombra · balcone, Pianerottolo.
- 149 riferimenti fotografici attivi, tutti risolti; 124 file distinti dopo deduplicazione SHA256.
- 375120804 byte di immagini per `/share/plantcare/photos`.
- 9 fotografie PNG/HEIC convertite in JPEG per il web, senza modificare gli originali; tutti i JPEG verificati con Pillow.
- Tre riferimenti a immagini già eliminate nel diario nativo non vengono ripristinati.
- ZIP di soli metadati: 113143 byte; fotografie trasferite separatamente tramite Samba.
- SHA256 del file di importazione: `20c4f32ced494d58c2aa6939b10d4ef99c9b075b94a993710097dde811b9d2c9`.

La prova locale in archivio temporaneo ha validato importazione e proiezione delle scadenze di tutte le piante. Nessuna richiesta di generazione AI avviata: la giornata corrente è marcata già analizzata per non ripetere l’analisi nativa durante il collaudo della migrazione. Modalità delle piante e programmazione successiva conservate.

## Stato operativo

Importazione completata nell’archivio operativo Home Assistant con la versione 0.4.2. Anteprima: 18 piante, 7 prodotti, 20 specie, 124 fotografie e nessun avviso di immagini mancanti. Foto nella cartella condivisa `/share/plantcare/photos`, riutilizzate senza duplicarle. 74 test, build e smoke ARM64/AMD64 passati.

Verifica in Safari tramite Ingress: collezione e fotografie caricate; scheda Ficus con piano nativo, diario e cronologia; sette prodotti con dosi/frequenze; calendario della settimana successiva con attività importate. Nessuna cura registrata o richiesta di generazione AI eseguita durante la verifica.

[Collezione importata](screenshots/0.4.2/imported-collection.jpg).

File temporanei di migrazione e prova locale in `/private/tmp/plantcare-import-20261115`, esclusi dal pacchetto di distribuzione e dai sorgenti.

Verifica fotografie prodotti (0.6.1): tutti e sette i riferimenti importati corrispondono a file presenti e integri SHA256. Il difetto era nella visualizzazione delle schede, che mostrava solo l’icona generica. Corretta l’interfaccia senza ripetere l’importazione.
