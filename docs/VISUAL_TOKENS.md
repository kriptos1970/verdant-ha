# Token visivi — PlantCare Web

Fonte unica: `plantcare_web/frontend/src/tokens.css`, importato dopo `style.css` e prima di `ios-layout.css`.

## Colori

| Token | Valore | Uso |
|---|---|---|
| `--vc-forest` | `#194330` | titoli, hero, testo primario forte |
| `--vc-moss` | `#406e4d` | azioni primarie, icone, accenti |
| `--vc-blue` | `#2f84dc` | acqua, metriche e pulsanti annaffiatura |
| `--vc-orange` | `#e08a2e` | avvisi e concimazione |
| `--vc-danger` | `#a33b32` | eliminazione e stati critici |
| `--vc-text` | `#17251d` | testo principale |
| `--vc-text-secondary` | `#737b74` | etichette e testo secondario |
| `--vc-line` | `#e5e9df` | bordi e separatori |
| `--vc-surface` | `#ffffff` | superfici |
| `--vc-mint` | `#e8f0e8` | sfondi tenui e icone |

## Tipografia telefono

| Token | Valore | Uso |
|---|---|---|
| `--vc-font-caption` | 12px | caption, meta |
| `--vc-font-small` | 13px | etichette, dettagli |
| `--vc-font-body` | 15px | corpo |
| `--vc-font-title` | 18px | titoli di card |
| `--vc-font-h2` | 20px | sezioni |
| `--vc-font-display` | 30px | titolo pagina |

## Spazi, raggi, icone

| Token | Valore |
|---|---|
| `--vc-space-1` … `--vc-space-5` | 4 / 8 / 12 / 16 / 20 px |
| `--vc-radius-xs` … `--vc-radius-xl` | 10 / 12 / 14 / 18 / 22 px |
| `--vc-icon-sm` … `--vc-icon-lg` | 18 / 22 / 26 px |
| `--vc-tap` | 44 px |

## Regole

- Le nuove schermate telefono usano i token, non valori esadecimali o px “a caso”.
- Le icone piene usano `IOSIcon`; le icone desktop possono restare lucide.
- Il pulsante primario è `--vc-moss`; l’acqua è `--vc-blue`; gli avvisi sono `--vc-orange`.
- I target di tocco restano almeno `--vc-tap` (44 px), anche se il controllo visivo è più piccolo.
- Le card usano `--vc-radius-lg`/`--vc-radius-xl`; i controlli `--vc-radius-sm`/`--vc-radius-md`.
- I testi secondari usano `--vc-text-secondary`; non usare grigi fuori token.
