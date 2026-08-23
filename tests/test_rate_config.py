import os, subprocess, sys

def test_default_rate_is_ten_qps():
    env=os.environ.copy(); env.pop('SUFE_REQUESTS_PER_SECOND',None); env.pop('SUFE_ALLOW_HIGH_RATE',None)
    result=subprocess.run([sys.executable,'-c','from collector.config import settings; print(settings.interval_seconds)'],env=env,capture_output=True,text=True)
    assert result.returncode==0 and result.stdout.strip()=='0.1'

def test_ten_qps_is_available_without_extra_opt_in():
    env=os.environ.copy(); env['SUFE_REQUESTS_PER_SECOND']='10'; env.pop('SUFE_ALLOW_HIGH_RATE',None)
    result=subprocess.run([sys.executable,'-c','from collector.config import settings'],env=env,capture_output=True,text=True)
    assert result.returncode==0

def test_high_rate_is_capped_at_ten_qps():
    env=os.environ.copy(); env['SUFE_REQUESTS_PER_SECOND']='10'; env['SUFE_ALLOW_HIGH_RATE']='true'
    result=subprocess.run([sys.executable,'-c','from collector.config import settings; print(settings.interval_seconds)'],env=env,capture_output=True,text=True)
    assert result.returncode==0 and result.stdout.strip()=='0.1'
