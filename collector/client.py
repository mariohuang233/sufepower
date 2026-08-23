from __future__ import annotations
import os, random, time
import requests

class AuthError(RuntimeError): pass
class RateLimitError(RuntimeError): pass
class BadRequestError(RuntimeError): pass

class EMSClient:
    READ_ONLY_PATHS={"/zone/list.do","/entityacct/list.do","/entityacct/info.do","/dev/info.do"}
    def __init__(self, token: str|None, base_url: str, interval: float=1, transport=None):
        if not token or not token.strip(): raise AuthError("SUFE_EMS_TOKEN is missing; collection stopped before any request")
        self._token=token.strip(); self.base_url=base_url.rstrip("/"); self.interval=max(0.1,interval); self._last_request=0.0
        self.http=requests.Session(); self.http.headers.update({"Authorization":f"Bearer {self._token}","Accept":"application/json, text/plain, */*","User-Agent":"SUFEElecRoomExport/1.0 (read-only; rate-limited)","X-Requested-With":"XMLHttpRequest"})
        if os.getenv("SUFE_EMS_COOKIE"): self.http.headers["Cookie"]=os.environ["SUFE_EMS_COOKIE"]
        if os.getenv("SUFE_EMS_REFERER"): self.http.headers["Referer"]=os.environ["SUFE_EMS_REFERER"]

    def get(self,path: str,**kwargs):
        if path not in self.READ_ONLY_PATHS: raise ValueError("only allowlisted read-only GET endpoints are permitted")
        wait=self.interval-(time.monotonic()-self._last_request)
        if wait>0: time.sleep(wait)
        self._last_request=time.monotonic()
        for attempt in range(3):
            try:
                response=self.http.get(self.base_url+path,timeout=30,**kwargs)
                if response.status_code in (401,403): raise AuthError(f"EMS authentication rejected with HTTP {response.status_code}")
                if response.status_code==429: raise RateLimitError("EMS rate limit received; collection stopped")
                if response.status_code==400:
                    summary=response.text[:500]
                    for key in ("Authorization","authorization","Cookie","cookie","token","Token"): summary=summary.replace(key,"[REDACTED]")
                    raise BadRequestError(f"EMS HTTP 400 response summary: {summary}")
                if response.status_code>=500:
                    if attempt==2: raise RuntimeError(f"EMS server error HTTP {response.status_code}")
                    time.sleep((2**attempt)+random.random()); continue
                response.raise_for_status(); return response
            except (requests.ConnectionError,requests.Timeout):
                if attempt==2: raise
                time.sleep((2**attempt)+random.random())

    def close(self): self.http.close()

def redact(text: str) -> str:
    return text.replace("Authorization","[REDACTED]").replace("Bearer ","Bearer [REDACTED]")
