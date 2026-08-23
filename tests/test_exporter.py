import json, sqlite3
from datetime import datetime
from collector.db import init_db, connect, upsert_snapshot
from collector.exporter import export_public, validate_staging, publish_staging

def test_export_is_deidentified_and_atomic(tmp_path):
    db=tmp_path/'private.db'; init_db(db)
    with connect(db) as c:
        c.execute("INSERT INTO room_registry VALUES(?,?,?,?,?,?,?,?,?)",('room-a','PRIVATE-1','五角场校区','1号楼','1','101','2026-01-01','2026-01-01',1))
        upsert_snapshot(c,{'room_id':'room-a','slot':'2026-08-23T00:00:00+08:00','sampled_at':'2026-08-23T00:01:00+08:00','balance_value':10.3,'balance_unit':'unknown','price':None,'quality':'ok','run_id':'run'})
        upsert_snapshot(c,{'room_id':'room-a','slot':'2026-08-23T04:00:00+08:00','sampled_at':'2026-08-23T04:01:00+08:00','balance_value':6.3,'balance_unit':'unknown','price':None,'quality':'ok','run_id':'run'})
    target=tmp_path/'public'; stage=export_public(db,target); validate_staging(stage); publish_staging(stage,target)
    assert (target/'v1/manifest.json').exists()
    assert 'PRIVATE-1' not in (target/'v1/manifest.json').read_text()
    rooms=json.loads((target/'v1/registry/rooms.json').read_text())
    assert rooms[0]['consumed_today'] == 4.0
    assert rooms[0]['consumption_quality'] == 'ok'
