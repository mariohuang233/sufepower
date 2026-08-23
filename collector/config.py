from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAR = ROOT / "var"
PUBLIC = ROOT / "public-data"

@dataclass(frozen=True)
class Settings:
    token: str | None = os.getenv("SUFE_EMS_TOKEN")
    api_base: str = os.getenv("SUFE_EMS_API_BASE", "https://ems.sufe.edu.cn/ems/chargedmt/app/user/api")
    interval_seconds: float = float(os.getenv("SUFE_REQUEST_INTERVAL_SECONDS", "1"))
    requests_per_second: float = float(os.getenv("SUFE_REQUESTS_PER_SECOND", "10"))
    allow_high_rate: bool = os.getenv("SUFE_ALLOW_HIGH_RATE", "true").lower() == "true"
    outlier_threshold: float = float(os.getenv("SUFE_OUTLIER_THRESHOLD", "50"))
    publish_intraday_history: bool = os.getenv("PUBLISH_INTRADAY_HISTORY", "false").lower() == "true"

settings = Settings()

if settings.requests_per_second > 1 and not settings.allow_high_rate:
    raise RuntimeError("high request rate disabled; set SUFE_ALLOW_HIGH_RATE=true only with explicit operator authorization")
if settings.requests_per_second > 10:
    raise RuntimeError("request rate hard-capped at 10 QPS")
if settings.requests_per_second > 1:
    settings = Settings(interval_seconds=1 / settings.requests_per_second)

def ensure_private_dirs() -> None:
    for path in (VAR, VAR / "raw", VAR / "logs", PUBLIC / "v1"):
        path.mkdir(parents=True, exist_ok=True)
