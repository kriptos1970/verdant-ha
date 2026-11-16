import hashlib
import pytest
from plantcare_web.backend.backup import resolve_existing_photos, remap


def test_import_reuses_pre_staged_photos_by_verified_hash(tmp_path):
    data=b'image-content';name=hashlib.sha256(data).hexdigest()+'.jpg'
    (tmp_path/name).write_bytes(data)
    archive={'photos':{},'missingPhotos':[name,'not-present.jpg']}
    resolve_existing_photos(archive,tmp_path)
    assert archive['photos'][name]==tmp_path/name
    assert archive['missingPhotos']==['not-present.jpg']


def test_import_rejects_changed_shared_photo_before_writes(tmp_path):
    name=hashlib.sha256(b'original').hexdigest()+'.jpg'
    (tmp_path/name).write_bytes(b'changed')
    archive={'photos':{},'missingPhotos':[name]}
    with pytest.raises(ValueError,match='checksum'):resolve_existing_photos(archive,tmp_path)
    assert archive['photos']=={}


def test_existing_photos_never_resolve_paths_outside_configured_directory(tmp_path):
    archive={'photos':{},'missingPhotos':['../photo.jpg','/etc/passwd','https://example.com/photo.jpg']}
    resolve_existing_photos(archive,tmp_path)
    assert len(archive['missingPhotos'])==3 and archive['photos']=={}


def test_import_api_uses_shared_photos_and_ignores_deleted_photo_references(tmp_path,monkeypatch):
    import io,json,base64
    from PIL import Image
    from fastapi.testclient import TestClient
    from plantcare_web.backend import main
    from plantcare_web.backend.storage import Store
    from plantcare_web.backend.models import Plant
    store=Store(tmp_path/'data',tmp_path/'shared')
    monkeypatch.setattr(main,'store',store);monkeypatch.setattr(main.settings,'ingress',False)
    output=io.BytesIO();Image.new('RGB',(10,10),'green').save(output,format='JPEG')
    data=output.getvalue();name=hashlib.sha256(data).hexdigest()+'.jpg';(store.photos/name).write_bytes(data)
    plant=Plant(name='Monstera',photoPath=name,photoMemories=[dict(localPath='deleted.jpg',deletedAt='2026-01-01T00:00:00Z')]).model_dump()
    payload=json.dumps({'plants':[plant],'fertilizers':[],'photos':{}}).encode()
    raw=json.dumps(dict(version=3,payload=base64.b64encode(payload).decode(),checksum=hashlib.sha256(payload).hexdigest())).encode()
    client=TestClient(main.app,headers={'X-PlantCare-Request':'1'})
    preview=client.post('/api/import/preview',files={'file':('collection.json',raw,'application/json')})
    assert preview.status_code==200,preview.text
    assert preview.json()['photos']==1 and preview.json()['missingPhotos']==[]
    assert not store.list('plants')
    committed=client.post('/api/import',files={'file':('collection.json',raw,'application/json')})
    assert committed.status_code==200,committed.text
    assert store.list('plants')[0][0]['photoPath']==name
    assert (store.photos/name).read_bytes()==data
