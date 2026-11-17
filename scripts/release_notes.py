"""Write the GitHub release body from the add-on changelog and package checksum."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
version = re.search(r'^version:\s*"([^"]+)"', (root / 'plantcare_web/config.yaml').read_text(), re.M).group(1)
changelog = (root / 'plantcare_web/CHANGELOG.md').read_text()
section = re.search(rf'^# {re.escape(version)}\b.*?(?=^# |\Z)', changelog, re.M | re.S)
if not section:
    sys.exit(f'No changelog section found for version {version}')
notes = section.group(0).strip()
notes = notes.split('\n', 1)[1].strip() if notes.startswith('#') else notes

checksum_file = root / 'releases' / f'plantcare-web-{version}.sha256'
if not checksum_file.exists():
    sys.exit(f'Missing checksum file: {checksum_file}')
checksum = checksum_file.read_text().split()[0]

print(f"""{notes}

## Installazione su Home Assistant

1. Scarica `plantcare-web-{version}.zip` ed estrailo.
2. Copia la cartella `plantcare_web` in `/addons/plantcare_web` (Samba o Terminal & SSH). Non copiare `.venv`, `node_modules` o archivi personali.
3. Nell'App store di Home Assistant aggiorna gli add-on locali, installa **PlantCare Web** e avvialo. L'interfaccia è disponibile tramite Ingress.

Configura fuso orario, sensori ed eventuali provider AI nelle opzioni dell'add-on. L'AI è facoltativa e disattivata per impostazione predefinita.

## Integrità

`plantcare-web-{version}.zip` — SHA256 `{checksum}`

## Note

Rilascio generato dal tag `{version}`. Il codice è distribuito con licenza MIT; vedi `LICENSE`.""")
