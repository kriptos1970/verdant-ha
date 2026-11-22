"""Write the GitHub release body from the add-on changelog and package checksum.

The body is English first, with the Italian changelog kept below for the Italian
users. When ``plantcare_web/CHANGELOG.en.md`` has a section for the version, that
translation is used instead of the Italian text.
"""

from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
version = re.search(r'^version:\s*"([^"]+)"', (root / 'plantcare_web/config.yaml').read_text(), re.M).group(1)


def section_of(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text()
    match = re.search(rf'^# {re.escape(version)}\b.*?(?=^# |\Z)', text, re.M | re.S)
    if not match:
        return None
    body = match.group(0).strip()
    return body.split('\n', 1)[1].strip() if body.startswith('#') else body


italian = section_of(root / 'plantcare_web/CHANGELOG.md')
if not italian:
    sys.exit(f'No changelog section found for version {version}')
english = section_of(root / 'plantcare_web/CHANGELOG.en.md')

checksum_file = root / 'releases' / f'plantcare-web-{version}.sha256'
if not checksum_file.exists():
    sys.exit(f'Missing checksum file: {checksum_file}')
checksum = checksum_file.read_text().split()[0]

changes = english or italian
extra = '' if english is None or english == italian else f'\n\n<details>\n<summary>Modifiche in italiano</summary>\n\n{italian}\n\n</details>'

print(f"""## Changes

{changes}{extra}

## Install on Home Assistant

1. Open **Settings → Add-ons → Add-on store**, then the **⋮** menu → **Repositories**.
2. Add `https://github.com/kriptos1970/verdant-ha` and refresh the store.
3. Install **Verdant**, start it and open the **Web UI** (Ingress, no port exposed).

Home Assistant picks up the new version from `plantcare_web/config.yaml` in the repository.

### Offline or development install

1. Download `plantcare-web-{version}.zip` from this release and extract it.
2. Copy the `plantcare_web` folder to `/addons/plantcare_web` on the Home Assistant host.
3. Refresh the local add-ons in the app store, install **Verdant** and start it.

## Integrity

`plantcare-web-{version}.zip` — SHA256 `{checksum}`

## Notes

Release built from tag `{version}`. MIT licensed; see `LICENSE`.""")
