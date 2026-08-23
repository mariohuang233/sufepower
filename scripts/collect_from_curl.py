"""Use a locally saved browser cURL request without exposing credentials to chat."""
from __future__ import annotations
import os, re, subprocess, sys
from pathlib import Path

def headers(text: str) -> dict[str,str]:
    result={}
    for match in re.finditer(r"(?:-H|--header)\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s\\]+))",text,re.I):
        raw=next(x for x in match.groups() if x is not None)
        if ":" in raw:
            key,value=raw.split(":",1); result[key.strip().lower()]=value.strip()
    return result

path=Path(sys.argv[1]) if len(sys.argv)>1 else None
if not path or not path.exists(): raise SystemExit("用法：python scripts/collect_from_curl.py C:\\本机临时目录\\request.txt [--smoke]")
text=path.read_text(encoding="utf-8-sig")
if re.search(r"(?:-X|--request)\s+(?:POST|PUT|PATCH|DELETE)",text,re.I): raise SystemExit("只允许 GET 请求，未执行")
if "ems.sufe.edu.cn" not in text: raise SystemExit("请求文件不是 EMS 域名，未执行")
h=headers(text); token=h.get("authorization",""); cookie=h.get("cookie","")
if token.lower().startswith("bearer "): token=token[7:].strip()
if not token: raise SystemExit("请求文件中没有 Authorization Bearer，未执行")
env=os.environ.copy(); env.update({"SUFE_EMS_TOKEN":token,"SUFE_EMS_COOKIE":cookie,"SUFE_EMS_REFERER":h.get("referer","")})
command="smoke" if "--smoke" in sys.argv[2:] else "collect"
args=[sys.executable,"-m","collector",command]
if command=="collect": args += ["--slot","now"]
try: raise SystemExit(subprocess.call(args,cwd=Path(__file__).resolve().parents[1],env=env))
finally:
    token=""; cookie=""; text=""; env.pop("SUFE_EMS_TOKEN",None); env.pop("SUFE_EMS_COOKIE",None); env.pop("SUFE_EMS_REFERER",None)
