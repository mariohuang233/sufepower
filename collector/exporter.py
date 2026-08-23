from __future__ import annotations
import json, os, shutil, tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from .config import PUBLIC, VAR
from .db import connect
from .timeutils import iso, now_shanghai

FORBIDDEN=("entityacctid","acctno","devno","Authorization","Cookie","Token","手机号","用户名")

def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")

def _consumption_index(snapshots: list[dict]) -> tuple[dict[tuple[str, str], dict], dict[tuple[str, str], dict], str | None]:
    """Estimate room consumption from adjacent balance snapshots.

    A balance increase is treated as recharge, a large jump or long gap is
    excluded, and only valid same-unit drops are counted. The result is keyed
    by snapshot and by (room, local day), so every public dimension can reuse
    the same calculation.
    """
    by_room: dict[str, list[dict]] = defaultdict(list)
    for point in snapshots:
        by_room[point["room_id"]].append(point)
    point_index: dict[tuple[str, str], dict] = {}
    daily: dict[tuple[str, str], dict] = {}
    latest_day = max((str(point["sampled_at"])[:10] for point in snapshots), default=None)
    for room_id, points in by_room.items():
        points.sort(key=lambda point: point["sampled_at"])
        for index, point in enumerate(points):
            current = point.get("balance_value")
            result = {"consumed": None, "quality": "insufficient_history"}
            if index:
                previous = points[index - 1]
                before = previous.get("balance_value")
                try:
                    gap_hours = (datetime.fromisoformat(point["sampled_at"]) - datetime.fromisoformat(previous["sampled_at"])).total_seconds() / 3600
                except (TypeError, ValueError):
                    gap_hours = 999
                if before is None or current is None:
                    result["quality"] = "missing"
                elif previous.get("balance_unit") != point.get("balance_unit"):
                    result["quality"] = "unit_changed"
                elif gap_hours > 8:
                    result["quality"] = "gap"
                elif before < 0 or current < 0:
                    result["quality"] = "outlier"
                else:
                    delta = round(before - current, 4)
                    if delta < 0:
                        result["quality"] = "recharge_suspected"
                    elif delta > 50:
                        result["quality"] = "outlier"
                    else:
                        result = {"consumed": delta, "quality": "ok"}
            point_index[(room_id, point["slot"])] = result
            day = str(point["sampled_at"])[:10]
            key = (room_id, day)
            row = daily.setdefault(key, {"consumed": 0.0, "recharged": 0.0, "valid_drops": 0, "end_balance": current, "sampled_at": point["sampled_at"], "balance_unit": point.get("balance_unit", "unknown"), "quality": "insufficient_history"})
            row["end_balance"] = current
            row["sampled_at"] = point["sampled_at"]
            if result["quality"] == "ok":
                row["consumed"] += result["consumed"] or 0
                row["valid_drops"] += 1
                row["quality"] = "ok"
            elif result["quality"] == "recharge_suspected" and index:
                row["recharged"] += max(0, (current or 0) - (points[index - 1].get("balance_value") or 0))
    return point_index, daily, latest_day

def export_public(db_path: Path=VAR/"sufeelec.db", target: Path=PUBLIC) -> Path:
    """Build a complete public view in a staging directory; no private IDs leave this function."""
    with connect(db_path) as conn:
        registry=[dict(x) for x in conn.execute("SELECT room_id,campus,building,floor,room,last_confirmed_at FROM room_registry WHERE active=1 ORDER BY campus,building,room")]
        snapshots=[dict(x) for x in conn.execute("SELECT s.* FROM snapshots s JOIN room_registry r ON r.room_id=s.room_id WHERE r.active=1 ORDER BY s.sampled_at")]
    campuses=[]; campus_ids={}; buildings=[]; building_ids={}
    for row in registry:
        if row["campus"] not in campus_ids:
            cid="campus-"+str(len(campus_ids)+1); campus_ids[row["campus"]]=cid; campuses.append({"campus_id":cid,"name":row["campus"]})
        key=(row["campus"],row["building"])
        if key not in building_ids:
            bid="building-"+str(len(building_ids)+1); building_ids[key]=bid; buildings.append({"building_id":bid,"campus_id":campus_ids[row["campus"]],"name":row["building"]})
    point_index, daily_index, report_day = _consumption_index(snapshots)
    latest={}
    for snap in snapshots: latest[snap["room_id"]]=snap
    rooms=[]
    for row in registry:
        snap=latest.get(row["room_id"]); daily=daily_index.get((row["room_id"], report_day or ""), {})
        rooms.append({"room_id":row["room_id"],"campus_id":campus_ids[row["campus"]],"building_id":building_ids[(row["campus"],row["building"])],"floor":row["floor"],"name":row["room"],"balance_value":snap["balance_value"] if snap else None,"balance_unit":snap["balance_unit"] if snap else "unknown","last_updated":snap["sampled_at"] if snap else row["last_confirmed_at"],"stale":snap is None,"quality":snap["quality"] if snap else "missing","consumed_today":round(daily["consumed"],4) if daily.get("quality")=="ok" else None,"consumption_quality":daily.get("quality","insufficient_history")})
    successful=sum(1 for x in rooms if not x["stale"]); total=len(rooms); cov=successful/total if total else 0; status="healthy" if cov>=.98 else "partial" if cov>=.9 else "blocked"
    latest_slot=max((x["slot"] for x in snapshots),default=None); generated=iso(now_shanghai())
    stage=Path(tempfile.mkdtemp(prefix="sufeelec-public-",dir=str(target.parent)))/"v1"; stage.mkdir(parents=True)
    _write(stage/"registry/campuses.json",campuses); _write(stage/"registry/buildings.json",buildings); _write(stage/"registry/rooms.json",rooms)
    room_building={x["room_id"]:x["building_id"] for x in rooms}
    for building in buildings:
        _write(stage/f"latest/buildings/{building['building_id']}.json",{"building":building,"rooms":[x for x in rooms if x["building_id"]==building["building_id"]]})
    # Publish only sanitized historical measurements; no private registry columns are copied.
    history_by_building={}
    for snap in snapshots:
        bid=room_building.get(snap["room_id"])
        if not bid: continue
        history_by_building.setdefault(bid,[]).append({"room_id":snap["room_id"],"slot":snap["slot"],"sampled_at":snap["sampled_at"],"balance_value":snap["balance_value"],"balance_unit":snap["balance_unit"],"quality":snap["quality"]})
    for bid, history in history_by_building.items():
        months={str(x["slot"])[:7] for x in history}
        for month in months: _write(stage/f"intraday/buildings/{bid}/{month}.json",[x for x in history if str(x["slot"]).startswith(month)])
        # One last valid slot per room and natural day is the daily series source.
        daily={}
        for point in history:
            day=str(point["sampled_at"])[:10]; key=(point["room_id"],day)
            if point["balance_value"] is not None and (key not in daily or point["sampled_at"]>daily[key]["sampled_at"]):
                daily[key]={**point,"consumed":daily_index.get(key,{}).get("consumed") if daily_index.get(key,{}).get("quality")=="ok" else None,"recharged":daily_index.get(key,{}).get("recharged",0),"consumption_quality":daily_index.get(key,{}).get("quality","insufficient_history")}
        _write(stage/f"daily/buildings/{bid}.json",list(daily.values()))
    for campus in campuses:
        bids={x["building_id"] for x in buildings if x["campus_id"]==campus["campus_id"]}; points=[p for bid in bids for p in history_by_building.get(bid,[])]
        _write(stage/f"daily/campuses/{campus['campus_id']}.json",points)
    _write(stage/"latest/overview.json",{"generated_at":generated,"latest_slot":latest_slot,"total_rooms":total,"successful_rooms":successful,"failed_rooms":total-successful,"coverage":round(cov,4),"status":status,"campuses":campuses})
    oldest=min((str(x["sampled_at"])[:10] for x in snapshots),default=None)
    _write(stage/"manifest.json",{"schema_version":"1.0.0","data_version":generated.replace("-","").replace(":","")[:12],"latest_slot":latest_slot,"sampled_at":generated,"total_rooms":total,"successful_rooms":successful,"failed_rooms":total-successful,"coverage":round(cov,4),"status":status,"oldest_intraday_date":oldest,"generated_at":generated})
    return stage

def validate_staging(stage: Path) -> None:
    text=" ".join(p.read_text(encoding="utf-8") for p in stage.rglob("*.json"))
    for word in FORBIDDEN:
        if word in text: raise ValueError(f"forbidden public field detected: {word}")
    manifest=json.loads((stage/"manifest.json").read_text(encoding="utf-8"))
    if manifest["status"]=="blocked": raise ValueError("coverage below 90%; publication blocked")

def publish_staging(stage: Path, target: Path=PUBLIC) -> None:
    validate_staging(stage); target.mkdir(parents=True,exist_ok=True); final=target/"v1"; backup=target/".v1.previous"
    if backup.exists(): shutil.rmtree(backup)
    if final.exists(): final.rename(backup)
    try: stage.rename(final)
    except Exception:
        if final.exists(): shutil.rmtree(final)
        if backup.exists(): backup.rename(final)
        raise
    if backup.exists(): shutil.rmtree(backup)
