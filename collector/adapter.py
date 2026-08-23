"""Normalize known EMS response shapes into private collector records.

The adapter deliberately keeps internal identifiers in memory/SQLite only. It
does not return raw response bodies to the publication layer.
"""
from __future__ import annotations
import re
from .ids import public_id

def rows(body) -> list[dict]:
    if isinstance(body, list): return [x for x in body if isinstance(x, dict)]
    if isinstance(body, dict):
        for key in ("data", "list", "rows", "records", "result", "items", "content"):
            value=body.get(key)
            found=rows(value)
            if found: return found
    return []

def pick(obj: dict, *keys):
    for key in keys:
        if obj.get(key) not in (None, ""): return obj[key]
    return None

def number(value):
    if value in (None, ""): return None
    if isinstance(value, (int,float)): return float(value)
    match=re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group()) if match else None

def room_parts(account: dict, campus_hint: str = "未知校区", building_hint: str = "未知楼栋") -> dict:
    campus=str(pick(account,"campus","campusName","zoneName","zone","areaName") or campus_hint)
    building=str(pick(account,"building","buildingName","bldName","buildName") or building_hint)
    room=str(pick(account,"room","roomNo","roomName","doorNo","houseno","houseNo") or "未知房间")
    floor=str(pick(account,"floor","floorNo","floorName") or (room[:1] if room[:1].isdigit() else "未知楼层"))
    return {"campus":campus,"building":building,"room":room,"floor":floor,"room_id":public_id(campus,building,room)}

def normalize_device(account: dict, device: dict, campus_hint: str = "未知校区", building_hint: str = "未知楼栋") -> dict:
    parts=room_parts(account,campus_hint,building_hint)
    private_id=str(pick(device,"devno","devNo","deviceNo","deviceId","id") or pick(account,"entityacctid","entityAcctId","acctid","id") or "")
    balance=number(pick(device,"balance","amt","amount","surplus","surplusAmount"))
    price=number(pick(device,"price","priceValue","pricetxt","unitPrice"))
    unit=str(pick(device,"balanceUnit","unit","energyUnit") or "unknown")
    return {**parts,"private_device_id":private_id,"balance_value":balance,"balance_unit":unit,"price":price}
