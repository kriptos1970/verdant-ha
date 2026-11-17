"""Check that direct backend pins match the reproducible lock used by Docker and CI."""
from pathlib import Path
import re
import sys

backend = Path(__file__).resolve().parents[1] / 'plantcare_web/backend'


def pins(path):
    result = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        match = re.match(r'^([A-Za-z0-9_.-]+)==([^\s;]+)', line)
        if match:
            name = re.sub(r'[-_.]+', '-', match.group(1)).lower()
            result[name] = match.group(2)
    return result


direct = pins(backend / 'requirements.txt')
locked = pins(backend / 'requirements.lock')
mismatches = [(name, version, locked.get(name)) for name, version in sorted(direct.items()) if locked.get(name) != version]
if mismatches:
    print('Direct backend pins do not match requirements.lock:')
    for name, version, current in mismatches:
        print(f'  {name}: requirements.txt={version}, requirements.lock={current or "missing"}')
    print('Update both files together and rerun this check.')
    sys.exit(1)
print(f'OK: {len(direct)} direct backend pins match requirements.lock')
