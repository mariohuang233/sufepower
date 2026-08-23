from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from .config import PUBLIC, VAR, ROOT, ensure_private_dirs, settings
from .db import init_db
from .demo import generate
from .client import EMSClient, AuthError, BadRequestError
from .collect import Collector
from .timeutils import slot_for
from .exporter import export_public, publish_staging, validate_staging
from .quality import gate

def main():
    parser=argparse.ArgumentParser(prog="python -m collector"); sub=parser.add_subparsers(dest="command",required=True)
    for name in ("discover","collect","validate","export","publish","cleanup","demo","import-legacy","smoke"): sub.add_parser(name)
    sub.choices["smoke"].add_argument("--zone-id",default="40")
    sub.choices["import-legacy"].add_argument("source",nargs="?",default=str(ROOT/"data/crawl_all/rooms_complete.csv"))
    sub.choices["collect"].add_argument("--slot",default="now")
    sub.choices["publish"].add_argument("--dry-run",action="store_true")
    args=parser.parse_args(); ensure_private_dirs(); init_db(VAR/"sufeelec.db")
    if args.command=="demo": print(generate())
    elif args.command=="import-legacy":
        from .import_legacy import import_csv
        print(json.dumps(import_csv(Path(args.source)),ensure_ascii=False))
    elif args.command=="collect":
        try: client=EMSClient(settings.token,settings.api_base,settings.interval_seconds)
        except AuthError as exc: parser.error(str(exc))
        try: print(json.dumps(Collector(client).collect(slot_for()),ensure_ascii=False))
        except BadRequestError as exc: parser.error(str(exc))
        except Exception as exc: parser.error(f"采集请求失败：{exc}")
        finally: client.close()
    elif args.command=="smoke":
        from .smoke import run
        try: client=EMSClient(settings.token,settings.api_base,settings.interval_seconds)
        except AuthError as exc: parser.error(str(exc))
        try: print(json.dumps(run(client,args.zone_id),ensure_ascii=False))
        except Exception as exc: parser.error(f"smoke 请求失败：{exc}")
        finally: client.close()
    elif args.command=="validate":
        manifest=json.loads((PUBLIC/"v1/manifest.json").read_text(encoding="utf-8")); print(json.dumps({"status":manifest["status"],"coverage":manifest["coverage"],"gate":gate(manifest["coverage"])},ensure_ascii=False))
    elif args.command=="cleanup":
        import time
        cutoff=time.time()-7*86400
        for p in (VAR/"raw").glob("*"):
            if p.stat().st_mtime < cutoff: p.unlink()
    elif args.command in ("export","publish"):
        stage=export_public()
        try:
            validate_staging(stage)
            if args.command=="export" or not args.dry_run:
                publish_staging(stage); print(json.dumps({"published":True,"path":str(PUBLIC/"v1")},ensure_ascii=False))
            else:
                shutil.rmtree(stage.parent); print(json.dumps({"published":False,"validated":True},ensure_ascii=False))
        except Exception:
            shutil.rmtree(stage.parent,ignore_errors=True)
            raise
    else: print(f"{args.command}: scaffold ready; real collection requires SUFE_EMS_TOKEN and explicit operator run")

if __name__ == "__main__": main()
