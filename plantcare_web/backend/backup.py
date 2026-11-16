"""Lossless native v1-v3 and web backup import, validated before any database write."""
import base64
import binascii
import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID
from pydantic import ValidationError
from .domain import iso, parse
from .models import Plant, Product, TreatmentInput
from .storage import Conflict

MAX_ARCHIVE = 150 * 1024 * 1024
DATE_KEYS = {'date','acquiredOn','lastWatered','lastFertilized','nextWateringOverride','nextFertilizingOverride','createdAt','updatedAt','deletedAt','postponedUntil','generatedAt','revisedAt','fetchedAt','downloadedAt','capturedAt','validFrom','validUntil','measuredAt','timestamp','startDate','endDate','cancelledAt','recordedAt','classifiedAt','assignedAt'}

def convert_native(value, key=None):
    if isinstance(value, dict):
        return {k:convert_native(v,k) for k,v in value.items()}
    if isinstance(value, list):
        return [convert_native(v,key) for v in value]
    if key in DATE_KEYS and isinstance(value,(float,int)) and not isinstance(value,bool):
        return iso(datetime(2001,1,1,tzinfo=timezone.utc)+timedelta(seconds=value))
    return value

def remap(value, mapping, key=None):
    if isinstance(value,dict):
        return {k:remap(v,mapping,k) for k,v in value.items()}
    if isinstance(value,list):
        return [remap(v,mapping,key) for v in value]
    if isinstance(value,str) and key in {'photoPath','photoPaths','path','localPath'}:
        return mapping.get(value,value)
    return value

def decode_archive(raw):
    if len(raw) > MAX_ARCHIVE:
        raise ValueError('Backup oltre il limite di 150 MB')
    envelope=json.loads(raw)
    if not isinstance(envelope,dict):
        raise ValueError('Archivio non valido')
    web=envelope.get('format') == 'plantcare-web'
    if envelope.get('version') not in ([1] if web else [1,2,3]):
        raise ValueError('Versione backup non supportata')
    payload_bytes=base64.b64decode(envelope['payload'], validate=True)
    checksum=hashlib.sha256(payload_bytes).hexdigest()
    if checksum != envelope.get('checksum'):
        raise ValueError('Checksum non corrispondente')
    payload=json.loads(payload_bytes)
    if not web:
        payload=convert_native(payload)
    collections=payload.get('collections',{}) if web else {k:payload.get(k,[]) or [] for k in ['plants','fertilizers','speciesBiologies','recommendations']}
    for name,model in [('plants',Plant),('fertilizers',Product)]:
        collections[name]=[model.model_validate(p).model_dump() for p in collections.get(name,[])]
    for plant in collections.get('plants',[]):
        for plan in plant.get('treatmentPlans') or []:
            TreatmentInput.model_validate(plan)
            if not isinstance(plan.get('productName'),str): raise ValueError('Nome prodotto del ciclo mancante')
    photos={}
    total=0
    for name,encoded in payload.get('photos',{}).items():
        data=base64.b64decode(encoded,validate=True)
        total+=len(data)
        if len(data)>20*1024*1024 or total>MAX_ARCHIVE:
            raise ValueError('Fotografie oltre i limiti del backup')
        photos[name]=data
    for collection, values in collections.items():
        if collection not in {'plants','fertilizers','speciesBiologies','recommendations','proposals'}:
            raise ValueError('Collezione sconosciuta')
        identifiers=[v['id'] for v in values]
        if len(identifiers)!=len(set(identifiers)):
            raise ValueError('Identificativi duplicati nel backup')
    missing=set()
    def scan(value,key=None):
        if isinstance(value,dict):
            if value.get('deletedAt'): return
            for k,v in value.items(): scan(v,k)
        elif isinstance(value,list):
            for v in value: scan(v,key)
        elif isinstance(value,str) and value and key in {'photoPath','photoPaths','path','localPath'} and value not in photos:
            missing.add(value)
    scan(collections)
    measurements=payload.get('measurements',[]) or []
    if not isinstance(measurements,list):
        raise ValueError('Misurazioni non valide')
    return {'checksum':checksum,'web':web,'collections':collections,'photos':photos,'measurements':measurements,'state':payload.get('state',{}) if web else {},'missingPhotos':sorted(missing)}

def resolve_existing_photos(archive, directory):
    """Reuse content-addressed files pre-staged in the configured photo directory."""
    from pathlib import Path
    for name in list(archive['missingPhotos']):
        if len(name)!=68 or not name.endswith('.jpg') or any(c not in '0123456789abcdef' for c in name[:-4]):
            continue
        path=Path(directory)/name
        if not path.is_file(): continue
        if hash_file(path)!=name[:-4]:
            raise ValueError('Una foto già presente nella cartella configurata non corrisponde al suo checksum.')
        archive['photos'][name]=path
    archive['missingPhotos']=[name for name in archive['missingPhotos'] if name not in archive['photos']]
    return archive


def summary(archive):
    return {'checksum':archive['checksum'],'format':'PlantCare Web' if archive['web'] else 'PlantCare nativo','counts':{k:len(v) for k,v in archive['collections'].items()},'photos':len(archive['photos']),'measurements':len(archive['measurements']),'missingPhotos':archive['missingPhotos']}

def import_archive(store, archive):
    with store.connection() as db:
        if db.execute('SELECT 1 FROM imports WHERE checksum=?',(archive['checksum'],)).fetchone():
            return {**summary(archive),'alreadyImported':True}
        if db.execute('SELECT 1 FROM entities LIMIT 1').fetchone() or db.execute('SELECT 1 FROM measurements LIMIT 1').fetchone():
            raise Conflict('Importazione disponibile soltanto su archivio vuoto.')
        # Content-addressed files cannot overwrite an existing photo; database changes are atomic.
        mapping={name:store.write_photo(data) for name,data in archive['photos'].items()}
        for collection, values in archive['collections'].items():
            for value in values:
                store.put(collection,remap(value,mapping),db=db)
        for key,value in archive['state'].items():
            if key in {'sensor-mappings','location','ai-status','last-ai-day','native-import-metadata','native-measurements','ai-model-selection'} or key.startswith('ai-advice-'):
                store.set_state(key,value,db)
        if not archive['web']:
            store.set_state('native-measurements',archive['measurements'],db)
        for m in archive['measurements']:
            # Native CareMeasurement fields and web SQL fields both accepted.
            plant=m.get('plant_id') or m.get('plantID')
            entity=m.get('entity_id') or m.get('sourceIdentifier') or m.get('sourceID') or 'native-import'
            kind=m.get('kind','unknown')
            measured=m.get('measured_at') or m.get('measuredAt') or m.get('date') or iso(datetime.now(timezone.utc))
            value=m.get('value')
            if isinstance(value,(int,float)):
                db.execute('INSERT INTO measurements(plant_id,entity_id,kind,value,unit,measured_at,source_at) VALUES (?,?,?,?,?,?,?)',(plant,entity,kind,value,m.get('unit'),measured,m.get('source_at')))
            else:
                # Preserve every unsupported native measurement without inventing a numeric conversion.
                continue
        store.set_state('native-import-metadata',{'missingPhotos':archive['missingPhotos']},db)
        db.execute('INSERT INTO imports VALUES (?,?)',(archive['checksum'],iso(datetime.now(timezone.utc))))
    return {**summary(archive),'alreadyImported':False}

# ZIP backups put photos alongside JSON rather than base64 inside JSON. Building and
# serving them is disk-backed, so memory does not grow with the photo collection.
def hash_file(path):
    digest=hashlib.sha256()
    with open(path,'rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''): digest.update(chunk)
    return digest.hexdigest()

def export_zip(store):
    import tempfile
    import zipfile
    import shutil
    from pathlib import Path
    directory=Path(tempfile.mkdtemp(prefix='backup-',dir=store.root))
    try:
        data=directory/'data.json'
        # SQLite read snapshot while serializing; photo content is immutable by hash.
        with store.connection() as db, data.open('w') as out:
            out.write('{"collections":{')
            for index,collection in enumerate(['plants','fertilizers','speciesBiologies','recommendations','proposals']):
                if index: out.write(',')
                out.write(json.dumps(collection)+':[')
                first=True
                for row in db.execute('SELECT payload FROM entities WHERE collection=? ORDER BY id',(collection,)):
                    if not first: out.write(',')
                    out.write(row['payload']);first=False
                out.write(']')
            out.write('},"state":')
            json.dump({r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM state')},out)
            out.write(',"measurements":[')
            first=True
            for row in db.execute('SELECT * FROM measurements'):
                if not first: out.write(',')
                json.dump(dict(row),out);first=False
            out.write(']}')
        files=sorted(store.photos.glob('*.jpg'))
        photo_size=sum(p.stat().st_size for p in files)
        if shutil.disk_usage(store.root).free < photo_size+data.stat().st_size+50*1024*1024:
            raise ValueError('Spazio insufficiente per preparare il backup completo. Usa il backup Home Assistant e quello della cartella foto.')
        hashes={'data.json':hash_file(data)}
        destination=directory/'plantcare-backup.zip'
        with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
            archive.write(data,'data.json')
            for path in files:
                name='photos/'+path.name
                archive.write(path,name)
                hashes[name]=hash_file(path)
            archive.writestr('manifest.json',json.dumps({'format':'plantcare-web-zip','version':1,'createdAt':iso(datetime.now(timezone.utc)),'files':hashes}))
        data.unlink()
        return destination
    except BaseException:
        shutil.rmtree(directory)
        raise

def decode_zip(path,staging):
    import zipfile
    from pathlib import Path
    from .storage import Store
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist()
        if len(infos)>100000 or sum(i.file_size for i in infos)>10*1024**3:
            raise ValueError('Backup ZIP oltre i limiti di sicurezza')
        names=[i.filename for i in infos]
        if len(names)!=len(set(names)) or 'manifest.json' not in names or 'data.json' not in names:
            raise ValueError('Backup ZIP incompleto o duplicato')
        if archive.getinfo('manifest.json').file_size>16*1024*1024 or archive.getinfo('data.json').file_size>MAX_ARCHIVE:
            raise ValueError('Metadati ZIP troppo grandi')
        manifest=json.loads(archive.read('manifest.json'))
        if manifest.get('format')!='plantcare-web-zip' or manifest.get('version')!=1:
            raise ValueError('Formato ZIP non supportato')
        hashes=manifest.get('files',{})
        if set(names)!=(set(hashes)|{'manifest.json'}):
            raise ValueError('Manifest ZIP non corrispondente')
        photos={}
        for name,digest in hashes.items():
            photo_name=name.removeprefix('photos/')
            if name!='data.json' and (not name.startswith('photos/') or len(photo_name)!=68 or not photo_name.endswith('.jpg') or any(c not in '0123456789abcdef' for c in photo_name[:-4])):
                raise ValueError('Percorso ZIP non valido')
            if name!='data.json' and archive.getinfo(name).file_size>100*1024*1024:
                raise ValueError('Fotografia ZIP troppo grande')
            destination=Path(staging)/('data.json' if name=='data.json' else photo_name)
            with archive.open(name) as source,destination.open('wb') as target:
                import shutil
                shutil.copyfileobj(source,target,length=1024*1024)
            if hash_file(destination)!=digest:
                raise ValueError('Checksum ZIP non corrispondente')
            if name!='data.json': photos[photo_name]=destination
        raw=(Path(staging)/'data.json').read_bytes()
        # Use the same metadata validation as JSON without embedding photo bytes.
        envelope={'format':'plantcare-web','version':1,'checksum':hashlib.sha256(raw).hexdigest(),'payload':base64.b64encode(raw).decode()}
        result=decode_archive(json.dumps(envelope).encode())
        result['checksum']=hash_file(path)
        result['photos']=photos
        result['missingPhotos']=[p for p in result['missingPhotos'] if p not in photos]
        return result
