from __future__ import annotations
import json, uuid
from datetime import datetime
from pathlib import Path
from .adapter import normalize_device, rows, pick
from .config import ROOT, VAR, settings
from .db import connect, init_db, upsert_snapshot
from .ids import public_id
from .timeutils import iso, now_shanghai, slot_for

class Collector:
    def __init__(self, client, db_path=VAR/"sufeelec.db"):
        self.client=client; self.db_path=db_path; init_db(db_path)

    def _zones(self) -> list[dict]:
        """Load the private zone registry, discovering it on ephemeral runners."""
        zone_file=ROOT/"data"/"zone_list.json"
        try: zones=json.loads(zone_file.read_text(encoding="utf-8"))
        except (OSError,ValueError): zones=[]
        if not isinstance(zones,list) or not zones:
            # GitHub-hosted runners are ephemeral and intentionally do not
            # receive ignored/private data files. Discover the read-only zone
            # tree from EMS instead of falling back to an unscoped account list.
            discovered=rows(self.client.get("/zone/list.do").json())
            zones=[]
            for zone in discovered:
                zone_id=pick(zone,"zoneid","zoneId","id")
                if zone_id is None: continue
                zones.append({
                    "zoneid":str(zone_id),
                    "parentid":pick(zone,"parentid","parentId","parentZoneId","pid"),
                    "zonename":str(pick(zone,"zonename","zoneName","name","title") or zone_id),
                })
        if not zones:
            raise RuntimeError("EMS zone discovery returned no zones; refusing unscoped collection")
        return zones

    def _account_rows(self) -> list[dict]:
        """Use zone-scoped read-only requests for the complete collection."""
        zones=self._zones()
        parent_ids={str(z.get("parentid")) for z in zones if isinstance(z,dict)}
        leaves=[z for z in zones if isinstance(z,dict) and str(z.get("zoneid")) not in parent_ids]
        def zone_path(zone_id):
            by_id={str(z.get("zoneid")):z for z in zones if isinstance(z,dict)}; names=[]; current=by_id.get(str(zone_id)); seen=set()
            while current and str(current.get("zoneid")) not in seen:
                seen.add(str(current.get("zoneid"))); names.append(str(current.get("zonename", ""))); current=by_id.get(str(current.get("parentid")))
            return list(reversed(names))
        found=[]
        for zone in leaves:
            zone_id=pick(zone,"zoneid","zoneId","id")
            if zone_id is None: continue
            names=zone_path(zone_id); accounts=rows(self.client.get("/entityacct/list.do",params={"zoneid":zone_id}).json())
            for account in accounts:
                item=dict(account); item["_campus_hint"]=names[1] if len(names)>1 else "未知校区"; item["_building_hint"]=names[2] if len(names)>2 else "未知楼栋"; item["_floor_hint"]=names[3] if len(names)>3 else str(zone.get("zonename", "未知楼层")); found.append(item)
        return found

    def collect(self, slot=None) -> dict:
        slot=slot or slot_for(); slot_text=iso(slot); run_id=str(uuid.uuid4()); started=iso(now_shanghai())
        with connect(self.db_path) as conn:
            conn.execute("INSERT INTO collection_runs(run_id,slot,started_at,status) VALUES(?,?,?,?)",(run_id,slot_text,started,"running"))
        total=success=failed=0; errors={}
        try:
            account_rows=self._account_rows()
            total=len(account_rows)
            for account in account_rows:
                try:
                    account_id=pick(account,"entityacctid","entityAcctId","acctid","acctId","id")
                    detail=account
                    if account_id is not None:
                        body=self.client.get("/entityacct/info.do",params={"entityacctid":account_id}).json()
                        if isinstance(body,dict): detail={**account,**body}
                    devices=rows(detail.get("dev")) if isinstance(detail,dict) else []
                    if not devices:
                        devices=[detail]
                    for device in devices:
                        record=normalize_device(detail,device,detail.get("_campus_hint","未知校区"),detail.get("_building_hint","未知楼栋"))
                        if detail.get("_floor_hint") and record.get("floor")=="未知楼层": record["floor"]=detail["_floor_hint"]
                        if not record["private_device_id"] or record["balance_value"] is None: raise ValueError("missing device id or balance")
                        with connect(self.db_path) as conn:
                            now=iso(now_shanghai())
                            conn.execute("""INSERT INTO room_registry(room_id,private_device_id,campus,building,floor,room,discovered_at,last_confirmed_at,active)
                            VALUES(?,?,?,?,?,?,?,?,1) ON CONFLICT(room_id) DO UPDATE SET private_device_id=excluded.private_device_id,campus=excluded.campus,building=excluded.building,floor=excluded.floor,room=excluded.room,last_confirmed_at=excluded.last_confirmed_at,active=1""",(record["room_id"],record["private_device_id"],record["campus"],record["building"],record["floor"],record["room"],now,now))
                            upsert_snapshot(conn,{"room_id":record["room_id"],"slot":slot_text,"sampled_at":now,"balance_value":record["balance_value"],"balance_unit":record["balance_unit"],"price":record["price"],"quality":"ok","run_id":run_id})
                        success += 1
                except Exception as exc:
                    failed += 1; errors[type(exc).__name__]=errors.get(type(exc).__name__,0)+1
            total=max(total,success+failed)
            status="healthy" if total and success/total>=.98 else "partial" if total and success/total>=.9 else "blocked"
            with connect(self.db_path) as conn:
                conn.execute("UPDATE collection_runs SET ended_at=?,status=?,total_rooms=?,successful_rooms=?,failed_rooms=?,coverage=?,error_counts=? WHERE run_id=?",(iso(now_shanghai()),status,total,success,failed,success/total if total else 0,json.dumps(errors),run_id))
            return {"run_id":run_id,"slot":slot_text,"status":status,"total":total,"successful":success,"failed":failed,"coverage":success/total if total else 0,"errors":errors}
        except Exception as exc:
            with connect(self.db_path) as conn:
                conn.execute("UPDATE collection_runs SET ended_at=?,status=?,error_counts=? WHERE run_id=?",(iso(now_shanghai()),"failed",json.dumps({type(exc).__name__:1}),run_id))
            raise
