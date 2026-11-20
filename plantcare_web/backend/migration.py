"""One-time database import used when moving to a new add-on slug.

The source snapshot is produced by Home Assistant from a cold add-on backup;
the request file makes the import explicit, so an ordinary empty install never
picks up unrelated data. The snapshot is left in place for rollback.
"""
import logging
import os
import shutil
from pathlib import Path

LOG = logging.getLogger(__name__)
SQLITE_HEADER = b"SQLite format 3\x00"


def import_shared_database(data_directory, source_directory=None):
    source = Path(source_directory or os.getenv(
        "PLANTCARE_MIGRATE_DIR", "/share/plantcare/migrate"))
    request = source / "import-request"
    snapshot = source / "plantcare.sqlite"
    data = Path(data_directory)
    target = data / "plantcare.sqlite"
    if target.exists() or not request.is_file() or not snapshot.is_file():
        return None
    data.mkdir(parents=True, exist_ok=True)
    temporary = data / "plantcare.sqlite.importing"
    shutil.copyfile(snapshot, temporary)
    with temporary.open("rb") as handle:
        if handle.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
            temporary.unlink()
            raise RuntimeError("Il database di migrazione non è un file SQLite valido.")
    os.replace(temporary, target)
    request.unlink()
    LOG.info("Imported the shared Verdant database into %s", target)
    return target
