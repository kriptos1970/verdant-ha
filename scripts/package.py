"""Create a small source package installable as a local Home Assistant add-on."""
from pathlib import Path
import zipfile
import json
import hashlib
root=Path(__file__).resolve().parents[1]
release=root/'releases';release.mkdir(exist_ok=True)
version=json.loads((root/'plantcare_web/frontend/package.json').read_text())['version']
target=release/f'plantcare-web-{version}.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root/'plantcare_web').rglob('*')):
        if not path.is_file() or set(path.parts)&{'node_modules','dist','__pycache__','.pytest_cache'} or path.suffix in {'.pyc','.tsbuildinfo'}:
            continue
        archive.write(path,path.relative_to(root))
    for name in ['README.md','README.it.md','LICENSE','ROADMAP.md','CONTRIBUTING.md','SECURITY.md','docs/README.md','docs/REFERENCE.md','docs/STATUS.md','docs/STEP7.md','docs/STEP8.md','docs/IOS_LAYOUT.md','docs/DEPLOYMENT.md','docs/IMPORT.md','scripts/preview_ios.py','scripts/verify_ios_summary.mjs','scripts/verify_product_dose.mjs','scripts/benchmark_archive.py','scripts/verify_native.py','scripts/verify_health_guides.py','scripts/verify_links.mjs','scripts/verify_ai.py','scripts/verify_adaptive.py','scripts/verify_care_engine.py','scripts/smoke_container.py','scripts/package.py','scripts/release_notes.py','.gitignore']:
        archive.write(root/name,name)
target.with_suffix('.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
print(target)
