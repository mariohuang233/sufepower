from __future__ import annotations
import os

token=os.getenv("SUFE_EMS_TOKEN")
if not token or not token.strip():
    raise SystemExit("SUFE_EMS_TOKEN 未设置；请在采集 runner 的受限环境中配置，不要写入命令行或提交到 Git")
value=token.strip()
if len(value)<8:
    raise SystemExit("SUFE_EMS_TOKEN 看起来过短；请确认使用的是完整授权 Token")
if any(ch.isspace() for ch in value):
    raise SystemExit("SUFE_EMS_TOKEN 包含空白字符；请重新配置，不会输出 Token 内容")
print(f"SUFE_EMS_TOKEN 已设置，长度 {len(value)}，内容未显示")
