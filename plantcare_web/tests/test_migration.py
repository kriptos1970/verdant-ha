from plantcare_web.backend.migration import import_shared_database

SNAPSHOT = b"SQLite format 3\x00" + b"0" * 128


def prepare(tmp_path):
    source = tmp_path / "share"
    source.mkdir()
    (source / "plantcare.sqlite").write_bytes(SNAPSHOT)
    (source / "import-request").write_text("1", encoding="utf-8")
    return source, tmp_path / "data"


def test_import_requires_a_request(tmp_path):
    source, data = prepare(tmp_path)
    (source / "import-request").unlink()
    assert import_shared_database(data, source) is None
    assert not (data / "plantcare.sqlite").exists()


def test_import_copies_once_and_keeps_the_snapshot(tmp_path):
    source, data = prepare(tmp_path)
    target = import_shared_database(data, source)
    assert target == data / "plantcare.sqlite"
    assert target.read_bytes() == SNAPSHOT
    assert not (source / "import-request").exists()
    assert (source / "plantcare.sqlite").exists()
    assert import_shared_database(data, source) is None
