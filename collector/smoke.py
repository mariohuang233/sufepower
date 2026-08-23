from __future__ import annotations
from .adapter import rows, pick

def run(client, zone_id: str="40") -> dict:
    accounts=rows(client.get("/entityacct/list.do",params={"zoneid":zone_id}).json())
    if not accounts: return {"ok":False,"zone_id":str(zone_id),"accounts":0,"message":"区域列表为空"}
    account=accounts[0]; account_id=pick(account,"entityacctid","entityAcctId","acctid","acctId","id")
    if account_id is None: return {"ok":False,"zone_id":str(zone_id),"accounts":len(accounts),"message":"账户缺少可用详情 ID"}
    detail=client.get("/entityacct/info.do",params={"entityacctid":account_id}).json()
    devices=rows(detail.get("dev")) if isinstance(detail,dict) else []
    return {"ok":True,"zone_id":str(zone_id),"accounts":len(accounts),"detail_received":isinstance(detail,dict),"devices":len(devices),"balance_received":any(pick(d,"balance","amt","amount","surplus","surplusAmount") is not None for d in devices)}
