from datetime import datetime
from collector.adapter import normalize_device
from collector.collect import Collector
from collector.db import connect

class Response:
    def __init__(self, body): self.body=body
    def json(self): return self.body

class FakeClient:
    def __init__(self): self.calls=[]
    def get(self,path,**kwargs):
        self.calls.append(path)
        if path=="/zone/list.do": return Response([{"zoneid":40,"parentid":None,"zonename":"测试楼层"}])
        if path=="/entityacct/list.do": return Response([{"entityacctid":7,"campusName":"五角场校区","buildingName":"1号楼","houseno":"101"}])
        if path=="/entityacct/info.do": return Response({"dev":[{"devno":"PRIVATE-7","balance":"6.37","pricetxt":"0.64 元/度"}]})
        raise AssertionError(path)

def test_collect_normalizes_and_upserts_idempotently(tmp_path):
    db=tmp_path/"private.db"; client=FakeClient(); collector=Collector(client,db)
    slot=datetime(2026,8,23,4,0)
    first=collector.collect(slot); second=collector.collect(slot)
    assert first["successful"]>=1 and second["successful"]>=1
    with connect(db) as conn:
        assert conn.execute("select count(*) from room_registry").fetchone()[0]==1
        assert conn.execute("select count(*) from snapshots").fetchone()[0]==1
        row=conn.execute("select balance_value,balance_unit from snapshots").fetchone()
        assert row[0]==6.37 and row[1]=="元"
