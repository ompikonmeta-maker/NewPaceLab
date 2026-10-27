#!/usr/bin/env python3
"""NewPaceLab — dashboard marathon Taofik & Reza.

  python pacelab.py              sync semua atlet lalu buat dashboard
  python pacelab.py sync         hanya tarik data Garmin
  python pacelab.py build        hanya buat dist/dashboard.html dari data yang ada
  python pacelab.py check        laporkan field Garmin yang terbaca (tanpa nilai pribadi)
  python pacelab.py demo         dashboard dari data rekaan (tanpa key, tanpa internet)

Opsi: --who TAOFIK|REZA|ALL   --since YYYY-MM-DD   --config config.json
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pacelab.garmin import BASE, ApiError, AuthError, Client, load_key  # noqa: E402
from pacelab.sync import Syncer  # noqa: E402


def load_config(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for k in ("data_dir", "keys_dir", "output"):
        cfg[k] = str((Path(path).parent / cfg[k]).resolve())
    for a in cfg["athletes"]:
        a["program"] = str((Path(path).parent / a["program"]).resolve())
    return cfg


def pick_athletes(cfg, who):
    if who.upper() == "ALL":
        return cfg["athletes"]
    sel = [a for a in cfg["athletes"] if a["id"] == who.upper()]
    if not sel:
        sys.exit("Atlet '%s' tidak ada di config. Pilihan: %s" % (who, ", ".join(a["id"] for a in cfg["athletes"])))
    return sel


def cmd_sync(cfg, athletes, since, base=BASE, keys=None, delay=0.4):
    until = dt.date.today()
    ok = True
    for a in athletes:
        key = (keys or {}).get(a["id"]) or load_key(a["id"], cfg["keys_dir"])
        if not key:
            print("[x] %s: key tidak ada. Simpan di keys/%s.key atau env GARMIN_KEY_%s" % (a["name"], a["id"], a["id"]))
            ok = False
            continue
        print("[%s] sync %s .. %s" % (a["name"], since, until))
        client = Client(a["id"], key, base=base, cache_dir=str(Path(cfg["data_dir"]).parent / ".token_cache"), delay=delay)
        try:
            res = Syncer(client, Path(cfg["data_dir"]) / a["id"]).run(since, until)
        except AuthError as e:
            print("[x] %s" % e)
            ok = False
            continue
        except ApiError as e:
            print("[x] %s: %s" % (a["name"], e))
            ok = False
            continue
        print("    %d lari baru (total %d), %d hari wellness, %d request%s" % (
            res["new_runs"], res["runs"], res["wellness_days"], res["requests"],
            ("; tidak tersedia: " + ", ".join(sorted(set(res["unavailable"])))) if res["unavailable"] else ""))
    return ok


def cmd_check(cfg, athletes):
    from pacelab.check import report
    for a in athletes:
        print(report(Path(cfg["data_dir"]) / a["id"], a["name"]))


def cmd_build(cfg, athletes, today=None, out=None):
    from pacelab.build import build
    path = build(cfg, athletes, today or dt.date.today(), out or cfg["output"])
    print("[i] Dashboard: %s" % path)
    return path


def cmd_demo(cfg, athletes):
    sys.path.insert(0, str(ROOT / "tools"))
    from mock_garmin import make_server
    srv = make_server()
    demo = dict(cfg, data_dir=str(Path(cfg["data_dir"]).parent / "data-demo"))
    keys = {"TAOFIK": "demo-taofik", "REZA": "demo-reza"}
    cmd_sync(demo, athletes, dt.date.fromisoformat(cfg["since"]), base="http://127.0.0.1:%d" % srv.server_port,
             keys=keys, delay=0)
    srv.shutdown()
    srv.server_close()
    return cmd_build(demo, athletes, out=str(Path(cfg["output"]).with_name("dashboard-demo.html")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="all", choices=["all", "sync", "build", "check", "demo"])
    ap.add_argument("--who", default="ALL")
    ap.add_argument("--since", help="tanggal awal (default dari config)")
    ap.add_argument("--config", default=str(ROOT / "config.json"))
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    athletes = pick_athletes(cfg, args.who)
    since = dt.date.fromisoformat(args.since or cfg["since"])
    if args.command in ("all", "sync"):
        cmd_sync(cfg, athletes, since)
    if args.command == "check":
        cmd_check(cfg, athletes)
    if args.command in ("all", "build"):
        cmd_build(cfg, cfg["athletes"])
    if args.command == "demo":
        cmd_demo(cfg, cfg["athletes"])


if __name__ == "__main__":
    main()
