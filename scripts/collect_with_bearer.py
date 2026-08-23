"""Run one collection with a bearer value entered privately at the console."""
from __future__ import annotations
import getpass, os, subprocess, sys

value=getpass.getpass("粘贴 Authorization Bearer 值（输入不会显示）：").strip()
if value.lower().startswith("bearer "):
    value=value[7:].strip()
if not value or any(ch.isspace() for ch in value):
    raise SystemExit("Bearer 值为空或包含空白，请只粘贴同一行的凭据值")
cookie=getpass.getpass("粘贴 Cookie 值（可选，输入不会显示）：").strip()
referer=input("Referer（可直接回车使用默认地址）：").strip() or "https://ems.sufe.edu.cn/ems/chargedmt/app/user/zone/zone/1"
env=os.environ.copy(); env["SUFE_EMS_TOKEN"]=value; env["SUFE_EMS_COOKIE"]=cookie; env["SUFE_EMS_REFERER"]=referer
try:
    raise SystemExit(subprocess.call([sys.executable,"-m","collector","collect","--slot","now"],env=env))
finally:
    value=""; cookie=""; referer=""; env.pop("SUFE_EMS_TOKEN",None); env.pop("SUFE_EMS_COOKIE",None); env.pop("SUFE_EMS_REFERER",None)
