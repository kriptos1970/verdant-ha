import base64
import hashlib
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from .domain import iso, now, parse
from .care_kinds import canonical_plant, legacy_plant

class Conflict(Exception):
    pass

class Store:
    def __init__(self, directory, photo_directory=None):
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True)
        self.photos = Path(photo_directory) if photo_directory else self.root / 'photos'
        self.thumbnails = self.root / 'thumbnails'
        self.thumbnails.mkdir(exist_ok=True)
        self.photos.mkdir(parents=True,exist_ok=True)
        self.lock = threading.RLock()
        with self.connection() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS entities(collection TEXT, id TEXT, payload TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(collection,id));
            CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS measurements(id INTEGER PRIMARY KEY, plant_id TEXT, entity_id TEXT, kind TEXT, value REAL, unit TEXT, measured_at TEXT, source_at TEXT);
            CREATE INDEX IF NOT EXISTS measurements_plant ON measurements(plant_id, measured_at);
            CREATE TABLE IF NOT EXISTS imports(checksum TEXT PRIMARY KEY, imported_at TEXT);
            PRAGMA user_version=1;
            ''')

    @contextmanager
    def connection(self):
        with self.lock:
            db = sqlite3.connect(self.root / 'plantcare.sqlite', timeout=30)
            db.row_factory = sqlite3.Row
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                db.close()

    def list(self, collection, db=None):
        if db is None:
            with self.connection() as conn:
                return self.list(collection, conn)
        return [(canonical_plant(json.loads(r['payload'])) if collection == 'plants' else json.loads(r['payload']), r['version']) for r in db.execute('SELECT payload,version FROM entities WHERE collection=? ORDER BY id', (collection,))]

    def get(self, collection, identifier, db=None):
        if db is None:
            with self.connection() as conn:
                return self.get(collection, identifier, conn)
        row = db.execute('SELECT payload,version FROM entities WHERE collection=? AND id=?', (collection, identifier)).fetchone()
        if row is None:
            raise KeyError(identifier)
        payload = json.loads(row['payload'])
        return (canonical_plant(payload) if collection == 'plants' else payload), row['version']

    def put(self, collection, payload, expected=None, db=None):
        if db is None:
            with self.connection() as conn:
                return self.put(collection, payload, expected, conn)
        if collection == 'plants':
            payload = canonical_plant(payload)
        identifier = payload['id']
        row = db.execute('SELECT version FROM entities WHERE collection=? AND id=?', (collection, identifier)).fetchone()
        if row and expected != row['version']:
            raise Conflict('La scheda è cambiata. Ricarica prima di salvare.')
        if not row and expected is not None:
            raise Conflict('Elemento non più disponibile.')
        version = row['version'] + 1 if row else 1
        clean = {k:v for k,v in payload.items() if not k.startswith('_')}
        db.execute('INSERT INTO entities VALUES (?,?,?,?) ON CONFLICT(collection,id) DO UPDATE SET payload=excluded.payload,version=excluded.version', (collection,identifier,json.dumps(clean,ensure_ascii=False,allow_nan=False),version))
        return clean, version

    def delete(self, collection, identifier, expected):
        with self.connection() as db:
            _, version = self.get(collection, identifier, db)
            if expected != version:
                raise Conflict('La scheda è cambiata. Ricarica prima di eliminare.')
            db.execute('DELETE FROM entities WHERE collection=? AND id=?', (collection,identifier))
            if collection == 'plants':
                db.execute('DELETE FROM state WHERE key IN (?,?)',('ai-advice-'+identifier,'adaptive-preview-'+identifier))
                db.execute('DELETE FROM state WHERE key=?',('botanical-preview-'+identifier,))
                mappings = self.state('sensor-mappings', [], db)
                self.set_state('sensor-mappings', [m for m in mappings if m.get('plantID') != identifier], db)
                db.execute('DELETE FROM measurements WHERE plant_id=?', (identifier,))

    def state(self, key, default=None, db=None):
        if db is None:
            with self.connection() as conn:
                return self.state(key, default, conn)
        row = db.execute('SELECT value FROM state WHERE key=?', (key,)).fetchone()
        return json.loads(row['value']) if row else default

    def set_state(self, key, value, db=None):
        if db is None:
            with self.connection() as conn:
                return self.set_state(key,value,conn)
        db.execute('INSERT INTO state VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key,json.dumps(value,allow_nan=False)))

    def write_photo(self, content):
        if isinstance(content,Path):
            from .backup import hash_file
            import shutil
            digest=hash_file(content)
            destination=self.photos/(digest+'.jpg')
            if not destination.exists():
                tmp=self.photos/(str(uuid4())+'.tmp')
                shutil.copyfile(content,tmp)
                os.replace(tmp,destination)
            return destination.name
        digest = hashlib.sha256(content).hexdigest()
        destination = self.photos / (digest + '.jpg')
        if not destination.exists():
            tmp = self.photos / (str(uuid4()) + '.tmp')
            tmp.write_bytes(content)
            os.replace(tmp, destination)
        return destination.name

    def export(self):
        if sum(p.stat().st_size for p in self.photos.glob('*.jpg'))>40*1024*1024:
            raise ValueError('Usa il backup ZIP per archivi fotografici oltre 40 MB.')
        with self.connection() as db:
            payload = {'createdAt': iso(now()), 'collections': {c:[legacy_plant(p) if c == 'plants' else p for p,_ in self.list(c, db)] for c in ['plants','fertilizers','speciesBiologies','recommendations','proposals']}, 'state': {r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM state')}, 'measurements': [dict(r) for r in db.execute('SELECT * FROM measurements')], 'photos': {p.name:base64.b64encode(p.read_bytes()).decode() for p in self.photos.glob('*.jpg')}}
        raw = json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',', ':')).encode()
        return {'format':'plantcare-web','version':1,'checksum':hashlib.sha256(raw).hexdigest(),'payload':base64.b64encode(raw).decode()}
