"""Rebuildable SQLite projection for chronologies; plant JSON stays authoritative."""


def _insert(source, event_source, where):
    return f"""
        INSERT INTO care_history_index(plant_id, position, event_id, event_date, kind, room)
        SELECT p.id, e.key, json_extract(e.value,'$.id'),
               julianday(json_extract(e.value,'$.date')),
               json_extract(e.value,'$.kind'), json_extract(p.payload,'$.room')
        FROM {source}json_each({event_source},'$.history') e
        WHERE {where}coalesce(json_extract(e.value,'$.deletedAt'),'')=''
    """


def ensure_history_index(db):
    def exists():
        return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='care_history_index'").fetchone()

    if exists():
        return
    # Create the projection, install its triggers and backfill old archives
    # together. The Store commits or rolls back the entire upgrade.
    db.execute('BEGIN IMMEDIATE')
    if exists():
        return
    db.execute("""
        CREATE TABLE care_history_index(
            plant_id TEXT NOT NULL, position INTEGER NOT NULL, event_id TEXT,
            event_date REAL, kind TEXT, room TEXT, PRIMARY KEY (plant_id, position)
        ) WITHOUT ROWID
    """)
    order = 'event_date DESC, plant_id, event_id, position'
    db.execute(f'CREATE INDEX care_history_by_date ON care_history_index({order})')
    db.execute(f'CREATE INDEX care_history_by_kind_room ON care_history_index(kind, room, {order})')
    db.execute(_insert('entities p, ', 'p.payload', "p.collection='plants' AND "))
    insert_new = _insert('(SELECT NEW.id AS id, NEW.payload AS payload) p, ', 'p.payload', '')
    db.execute(f"""
        CREATE TRIGGER care_history_insert AFTER INSERT ON entities
        WHEN NEW.collection='plants'
        BEGIN
            {insert_new};
        END
    """)
    db.execute(f"""
        CREATE TRIGGER care_history_update AFTER UPDATE OF payload ON entities
        WHEN NEW.collection='plants' AND (
            json_extract(OLD.payload,'$.history') IS NOT json_extract(NEW.payload,'$.history')
            OR json_extract(OLD.payload,'$.room') IS NOT json_extract(NEW.payload,'$.room')
        )
        BEGIN
            DELETE FROM care_history_index WHERE plant_id=OLD.id;
            {insert_new};
        END
    """)
    db.execute("""
        CREATE TRIGGER care_history_delete AFTER DELETE ON entities
        WHEN OLD.collection='plants'
        BEGIN
            DELETE FROM care_history_index WHERE plant_id=OLD.id;
        END
    """)
