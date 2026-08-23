import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from collector.ids import public_id
from collector.quality import estimate, gate, coverage
from collector.timeutils import slot_for

def test_public_id_is_stable_and_distinct():
    assert public_id('五角场校区','1号楼','101') == public_id('五角场校区','1号楼','101')
    assert public_id('五角场校区','1号楼','101') != public_id('五角场校区','1号楼','102')

def test_slot_is_shanghai_four_hour_boundary():
    value=datetime(2026,8,23,5,23,tzinfo=timezone(timedelta(hours=8)))
    assert slot_for(value).hour == 4 and slot_for(value).minute == 0

def test_consumption_quality_rules():
    prev={'balance_value':10,'balance_unit':'kWh'}
    assert estimate(prev, {'balance_value':8,'balance_unit':'kWh'}) == (2,'ok')
    assert estimate(prev, {'balance_value':12,'balance_unit':'kWh'})[1] == 'recharge_suspected'
    assert estimate(prev, {'balance_value':8,'balance_unit':'元'})[1] == 'unit_changed'
    assert estimate(prev, {'balance_value':-50,'balance_unit':'kWh'})[1] == 'outlier'

def test_quality_gate():
    assert coverage(98,100)==.98 and gate(.98)=='healthy'
    assert gate(.95)=='partial' and gate(.89)=='blocked'

def test_demo_has_no_forbidden_fields(tmp_path):
    from collector.demo import generate
    out=generate(tmp_path); text=' '.join(p.read_text(encoding='utf-8') for p in out.rglob('*.json'))
    for forbidden in ('entityacctid','acctno','devno','Authorization','Cookie','Token'):
        assert forbidden not in text
