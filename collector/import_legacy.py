from __future__ import annotations
import csv, re
from pathlib import Path
from .config import VAR
from .db import connect, init_db, upsert_snapshot
from .ids import public_id
from .timeutils import SHANGHAI, iso, slot_for
from datetime import datetime

def num(value):
    m=re.search(r"-?\d+(?:\.\d+)?",str(value or "")); return float(m.group()) if m else None

def import_csv(source: Path, db_path: Path=VAR/"sufeelec.db") -> dict:
    init_db(db_path); rows=[]; seen=set()
    with source.open(encoding="utf-8-sig",newline="") as fh:
        for row in csv.DictReader(fh):
            campus=row.get("campus","").strip(); building=row.get("building","").strip(); room=row.get("houseno","").strip()
            if not campus or not building or not room: continue
            rid=public_id(campus,building,room); key=(rid,row.get("fetched_at","")[:13])
            if key in seen: continue
            seen.add(key); rows.append((rid,row))
    if not rows: return {"total":0,"imported":0}
    slot=slot_for(datetime.fromisoformat(rows[0][1]["fetched_at"]).replace(tzinfo=SHANGHAI)); run_id="legacy-"+slot.strftime("%Y%m%d%H")
    with connect(db_path) as conn:
        conn.execute("INSERT OR REPLACE INTO collection_runs(run_id,slot,started_at,ended_at,status,total_rooms,successful_rooms,failed_rooms,coverage,error_counts) VALUES(?,?,?,?,?,?,?,?,?,?)",(run_id,iso(slot),iso(slot),iso(slot),"healthy",len(rows),len(rows),0,1,"{}"))
        for rid,row in rows:
            now=row.get("fetched_at") or iso(slot); sampled=datetime.fromisoformat(now).replace(tzinfo=SHANGHAI); slot_text=iso(slot_for(sampled))
            conn.execute("""INSERT INTO room_registry(room_id,private_device_id,campus,building,floor,room,discovered_at,last_confirmed_at,active) VALUES(?,?,?,?,?,?,?,?,1)
            ON CONFLICT(room_id) DO UPDATE SET private_device_id=excluded.private_device_id,campus=excluded.campus,building=excluded.building,floor=excluded.floor,room=excluded.room,last_confirmed_at=excluded.last_confirmed_at,active=1""",(rid,row.get("devno",""),row.get("campus",""),row.get("building",""),row.get("floor",""),row.get("houseno",""),now,now))
            upsert_snapshot(conn,{"room_id":rid,"slot":slot_text,"sampled_at":now,"balance_value":num(row.get("balance")),"balance_unit":"unknown","price":num(row.get("price")),"quality":"ok","run_id":run_id})
    return {"total":len(rows),"imported":len(rows),"run_id":run_id}
