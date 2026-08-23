from __future__ import annotations
import json, random
from datetime import timedelta
from pathlib import Path
from .config import PUBLIC, ensure_private_dirs
from .ids import public_id
from .timeutils import daily_slot_for, iso, now_shanghai

def generate(root: Path = PUBLIC) -> Path:
    ensure_private_dirs(); random.seed(7); base = daily_slot_for(now_shanghai())
    campuses = [{"campus_id":"wujiaochang","name":"五角场校区"},{"campus_id":"zhongyuan","name":"中原校区"}]
    buildings=[]; rooms=[]; latest=[]; histories={}
    for ci, campus in enumerate(campuses):
        for bi in range(1,3):
            name=f"{ci+1}号楼" if bi == 1 else f"{ci+1}号楼南楼"
            bid=public_id(campus["name"],name); buildings.append({"building_id":bid,"campus_id":campus["campus_id"],"name":name})
            histories[bid]=[]
            for ri in range(1,7):
                room=f"{101+ri}"; rid=public_id(campus["name"],name,room); value=round(10+ri*1.7-ci*2,2)
                roomrow={"room_id":rid,"campus_id":campus["campus_id"],"building_id":bid,"floor":"1","name":room}
                rooms.append(roomrow); stale=(ri==6 and bi==2)
                latest.append({**roomrow,"balance_value":value,"balance_unit":"元","last_updated":iso(base-timedelta(days=1 if stale else 0)),"stale":stale,"quality":"stale" if stale else "ok"})
                points=[]
                for days in range(30,-1,-1):
                    at=base-timedelta(days=days)
                    points.append({"slot":iso(at),"sampled_at":iso(at),"balance_value":round(value+(30-days)*.18,2),"balance_unit":"元","quality":"ok"})
                histories[bid].extend([{**p,"room_id":rid} for p in points])
    out=root/"v1"; (out/"registry").mkdir(parents=True,exist_ok=True); (out/"latest"/"buildings").mkdir(parents=True,exist_ok=True); (out/"intraday"/"buildings").mkdir(parents=True,exist_ok=True)
    (out/"registry/campuses.json").write_text(json.dumps(campuses,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"registry/buildings.json").write_text(json.dumps(buildings,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"registry/rooms.json").write_text(json.dumps(rooms,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"daily"/"campuses").mkdir(parents=True,exist_ok=True); (out/"daily"/"buildings").mkdir(parents=True,exist_ok=True)
    for b in buildings:
        values=[x for x in latest if x["building_id"]==b["building_id"]]
        (out/f"latest/buildings/{b['building_id']}.json").write_text(json.dumps({"building":b,"rooms":values},ensure_ascii=False,indent=2),encoding="utf-8")
        (out/f"intraday/buildings/{b['building_id']}").mkdir(parents=True,exist_ok=True)
        (out/f"intraday/buildings/{b['building_id']}/{base:%Y-%m}.json").write_text(json.dumps(histories[b['building_id']],ensure_ascii=False),encoding="utf-8")
        daily=[p for p in histories[b['building_id']] if 'T23:' in p['slot']]
        (out/f"daily/buildings/{b['building_id']}.json").write_text(json.dumps(daily,ensure_ascii=False),encoding="utf-8")
    for campus in campuses:
        rows=[p for b in buildings if b['campus_id']==campus['campus_id'] for p in histories[b['building_id']] if 'T23:' in p['slot']]
        (out/f"daily/campuses/{campus['campus_id']}.json").write_text(json.dumps(rows,ensure_ascii=False),encoding="utf-8")
    overview={"generated_at":iso(now_shanghai()),"latest_slot":iso(base),"total_rooms":len(rooms),"successful_rooms":len(rooms)-1,"failed_rooms":1,"coverage":round((len(rooms)-1)/len(rooms),4),"status":"partial","campuses":campuses}
    (out/"latest/overview.json").write_text(json.dumps(overview,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest={"schema_version":"1.0.0","data_version":base.strftime("%Y%m%d%H"),"latest_slot":iso(base),"sampled_at":iso(base),"total_rooms":len(rooms),"successful_rooms":len(rooms)-1,"failed_rooms":1,"coverage":overview["coverage"],"status":"partial","oldest_intraday_date":(base-timedelta(days=30)).date().isoformat(),"generated_at":overview["generated_at"]}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    return out
