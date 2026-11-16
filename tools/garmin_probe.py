#!/usr/bin/env python3
"""Garmin Personal API probe.

Checks which data your Personal API key actually returns, and writes:
  probe_output/report.md      - summary table (status, record count, fields)
  probe_output/report.json    - same, machine-readable
  probe_output/raw/*.json     - raw response per endpoint (your own data, stays local)

Python 3.9+ standard library only. No pip install needed.

Usage:
  set GARMIN_API_KEY=xxxxx            (Windows cmd)   or let the script prompt you
  python garmin_probe.py
  python garmin_probe.py --date 2026-10-25 --days 7
"""
import argparse
import datetime as dt
import getpass
import json
import os
import sys
import time
import http.client
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://personal.connectapi.garmin.com"
TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"

# (name, path template). {date}, {start}, {end}, {name} (displayName), {id} (latest activity)
# Paths mirror the Garmin Connect web API; the Personal API answers only an allowlisted subset,
# so a 404 here means "not available to personal keys", not a bug.
ENDPOINTS = [
    ("activities.list", "/activitylist-service/activities/search/activities?start=0&limit=10"),
    ("profile.social", "/userprofile-service/socialProfile"),
    ("profile.settings", "/userprofile-service/userprofile/user-settings"),
    ("devices", "/device-service/deviceregistration/devices"),
    # Paths from Garmin's official client (garmin/connect-personal-api-python)
    ("daily.summaries_v2", "/usersummary-service/v2/dailysummaries?startDate={start}&endDate={end}"),
    ("sleep.daily", "/sleep-service/sleep/dailySleep?date={date}"),
    ("sleep.summaries_range", "/sleep-service/sleep/dailySleepSummariesByDate?startDate={start}&endDate={end}"),
    ("spo2.acclimation", "/wellness-service/wellness/daily/spo2acclimation/{date}"),
    ("weight.range_v2", "/weight-service/weight/range/{start}/{end}?includeAll=true"),
    ("activities.runs", "/activitylist-service/activities/search/activities?start=0&limit=10"
                        "&startDate={start}&endDate={end}&activityType=running"),
    # Garmin Connect web paths (may 404 on the personal host)
    ("daily.summary", "/usersummary-service/usersummary/daily/{name}?calendarDate={date}"),
    ("daily.steps_range", "/usersummary-service/stats/steps/daily/{start}/{end}"),
    ("daily.stress_range", "/usersummary-service/stats/stress/daily/{start}/{end}"),
    ("daily.intensity_range", "/usersummary-service/stats/im/daily/{start}/{end}"),
    ("heart_rate", "/wellness-service/wellness/dailyHeartRate/{name}?date={date}"),
    ("stress", "/wellness-service/wellness/dailyStress/{date}"),
    ("body_battery", "/wellness-service/wellness/bodyBattery/reports/daily?startDate={start}&endDate={end}"),
    ("sleep", "/wellness-service/wellness/dailySleepData/{name}?date={date}&nonSleepBufferMinutes=60"),
    ("sleep.v2", "/sleep-service/sleep/dailySleepData?date={date}&nonSleepBufferMinutes=60"),
    ("hrv", "/hrv-service/hrv/{date}"),
    ("hrv.range", "/hrv-service/hrv/daily/{start}/{end}"),
    ("spo2", "/wellness-service/wellness/daily/spo2/{date}"),
    ("respiration", "/wellness-service/wellness/daily/respiration/{date}"),
    ("weight.range", "/weight-service/weight/dateRange?startDate={start}&endDate={end}"),
    ("vo2max.range", "/metrics-service/metrics/maxmet/daily/{start}/{end}"),
    ("training_readiness", "/metrics-service/metrics/trainingreadiness/{date}"),
    ("training_status", "/metrics-service/metrics/trainingstatus/aggregated/{date}"),
    ("fitness_age", "/fitnessage-service/fitnessage/{date}"),
    ("personal_records", "/personalrecord-service/personalrecord/prs/{name}"),
    ("activity.summary", "/activity-service/activity/{id}"),
    ("activity.details", "/activity-service/activity/{id}/details"),
    ("activity.splits", "/activity-service/activity/{id}/splits"),
    ("activity.fit", "/download-service/files/activity/{id}"),
]


class Client:
    def __init__(self, base, token, delay):
        self.base = base.rstrip("/")
        self.token = token
        self.delay = delay

    def get(self, path, timeout=30):
        req = urllib.request.Request(self.base + path, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json, */*",
            "User-Agent": "garmin-probe/1.0",
        })
        time.sleep(self.delay)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.headers.get("Content-Type", ""), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type", ""), e.read()
        except (OSError, http.client.HTTPException) as e:  # timeout, reset, DNS, TLS
            return "error", "", f"{type(e).__name__}: {e}".encode()


def get_token(base, key):
    req = urllib.request.Request(base.rstrip("/") + TOKEN_PATH, data=b"", method="POST",
                                 headers={"Authorization": "ApiKey " + key,
                                          "User-Agent": "garmin-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"[x] Gagal ambil token: HTTP {e.code} {e.read()[:300]!r}\n"
                 "    Cek key belum expired / tersalin lengkap.")
    text = body.decode("utf-8", "replace").strip()
    try:
        data = json.loads(text)
    except ValueError:
        return text  # plain-text token
    if isinstance(data, str):
        return data
    for k in ("accessToken", "access_token", "token"):
        if data.get(k):
            print(f"[i] Token OK (field '{k}', response keys: {sorted(data)})")
            return data[k]
    sys.exit(f"[x] Format token tidak dikenal, keys: {sorted(data)}")


def describe(body):
    """Return (record_count, field_names) for a JSON body."""
    try:
        data = json.loads(body)
    except ValueError:
        return None, []
    if isinstance(data, list):
        first = next((x for x in data if isinstance(x, dict)), {})
        return len(data), sorted(first)
    if isinstance(data, dict):
        return 1, sorted(data)
    return 1, []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", help="tanggal uji YYYY-MM-DD (default: kemarin)")
    ap.add_argument("--days", type=int, default=7, help="panjang range untuk endpoint *_range (default 7)")
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--out", default="probe_output")
    ap.add_argument("--delay", type=float, default=0.5, help="jeda antar request, detik")
    args = ap.parse_args()

    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today() - dt.timedelta(days=1)
    start = day - dt.timedelta(days=args.days - 1)
    key = os.environ.get("GARMIN_API_KEY") or getpass.getpass("Garmin Personal API key: ").strip()
    if not key:
        sys.exit("[x] Key kosong.")

    out = Path(args.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    client = Client(args.base, get_token(args.base, key), args.delay)

    ctx = {"date": day.isoformat(), "start": start.isoformat(), "end": day.isoformat(),
           "name": "", "id": ""}
    results = []
    try:
        for name, tmpl in ENDPOINTS:
            needs = [k for k in ("name", "id") if "{" + k + "}" in tmpl]
            if any(not ctx[k] for k in needs):
                results.append({"name": name, "path": tmpl, "status": "skip",
                                "note": "butuh " + "/".join(needs) + " (endpoint sebelumnya gagal)"})
                print(f"  -    {name}: skip")
                continue
            path = tmpl.format(**{k: urllib.parse.quote(str(v)) for k, v in ctx.items()})
            status, ctype, body = client.get(path, timeout=180 if "download-service" in tmpl else 30)
            row = {"name": name, "path": tmpl, "status": status, "bytes": len(body)}
            if status == 200:
                if "json" in ctype or body[:1] in (b"{", b"["):
                    count, fields = describe(body)
                    row.update(records=count, fields=fields)
                    (out / "raw" / f"{name}.json").write_bytes(body)
                    data = json.loads(body) if count is not None else None
                    if name == "profile.social" and isinstance(data, dict):
                        ctx["name"] = data.get("displayName") or data.get("userName") or ""
                    if name == "activities.list" and isinstance(data, list) and data:
                        ctx["id"] = str(data[0].get("activityId", ""))
                        ctx["name"] = ctx["name"] or data[0].get("ownerDisplayName") or ""
                else:
                    ext = ".zip" if "zip" in ctype or body[:2] == b"PK" else ".bin"
                    (out / "raw" / f"{name}{ext}").write_bytes(body)
                    row.update(note=f"file {ctype or 'binary'}")
            else:
                row["note"] = body[:150].decode("utf-8", "replace")
            results.append(row)
            mark = "OK " if status == 200 else "ERR"
            print(f"  {mark} {name}: {status} ({len(body)} B)")
    except KeyboardInterrupt:
        print("\n[!] Dihentikan, laporan sebagian tetap ditulis.")

    ok = [r for r in results if r["status"] == 200]
    (out / "report.json").write_text(json.dumps(
        {"date": ctx["date"], "range": [ctx["start"], ctx["end"]], "results": results}, indent=2))
    lines = [f"# Garmin Personal API probe — {dt.datetime.now():%Y-%m-%d %H:%M}",
             "", f"Tanggal uji: {ctx['date']} · range {ctx['start']} → {ctx['end']}",
             f"Tersedia: **{len(ok)} / {len(results)}** endpoint", "",
             "| Endpoint | Status | Records | Fields (contoh) / catatan |", "|---|---|---|---|"]
    for r in results:
        info = ", ".join(r.get("fields", [])[:12]) or r.get("note", "")
        info = info.replace("|", "/").replace("\n", " ")
        lines.append(f"| `{r['name']}` | {r['status']} | {r.get('records', '')} | {info} |")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[i] {len(ok)}/{len(results)} endpoint OK. Laporan: {out / 'report.md'}")


if __name__ == "__main__":
    main()
