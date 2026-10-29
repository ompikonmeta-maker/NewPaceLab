"""Incremental download of one athlete's runs and wellness into data/<ID>/.

  runs.json        normalized run summaries
  streams/<id>.json   {"t","d","hr","cad","el","v"} per run (from activity details, else from the FIT file)
  laps/<id>.json      {"laps": [...], "session": {...}} as recorded on the watch (from the FIT file)
  wellness.json    {"YYYY-MM-DD": {"sleep_s","sleep_score","hrv","hrv_status","bb","rhr","weight"}}
  state.json       what is already downloaded

Only endpoints the probe confirmed (HTTP 200 on personal keys) are used.
Field names are read defensively; `pacelab.py check` reports what was found.
"""
import datetime as dt
import json
import re
import struct
import zipfile
from pathlib import Path

from . import fit
from .garmin import ApiError

ACT_LIST = "/activitylist-service/activities/search/activities"
ACT_DETAILS = "/activity-service/activity/%s/details"
# where Garmin Connect keeps the laps of an activity; whether personal keys may read them is checked by `inspect`
ACT_SUMMARY = "/activity-service/activity/%s"
FIT_DOWNLOAD = "/download-service/files/activity/%s"   # zip with the original FIT from the watch (laps included)
LAP_PATHS = [("splits", "/activity-service/activity/%s/splits"), ("typedsplits", "/activity-service/activity/%s/typedsplits"),
             ("split_summaries", "/activity-service/activity/%s/split_summaries")]
SLEEP = "/sleep-service/sleep/dailySleepSummariesByDate"
HRV = "/hrv-service/hrv/daily/%s/%s"
BB = "/wellness-service/wellness/bodyBattery/reports/daily"
DAILY = "/usersummary-service/v2/dailysummaries"
WEIGHT = "/weight-service/weight/range/%s/%s"

# max days per call reported by the community; longer ranges give HTTP 400
CHUNK = {"sleep": 28, "hrv": 180, "bb": 28, "daily": 28, "weight": 180}
REFETCH_DAYS = 3  # late-arriving sleep/HRV for the last nights
SCHEMA = 3  # bump when wellness parsing changes: the full history is re-read once
STREAM_V = 2
FIT_V = 1         # bump to download every run's FIT file once more  # bump when per-second parsing changes: every stream is downloaded once more (2: cadence, elevation)
RHR_KEY = re.compile(r"resting_?heart_?rate(_?value)?$|^rhr$", re.I)
DATE_KEY = re.compile(r"^\d{4}-\d{2}-\d{2}")


# ------------------------------------------------------------------ helpers

def _read(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    tmp.replace(p)


def pick(obj, *paths):
    """First non-null value among dotted paths ('a.b.c')."""
    for path in paths:
        cur = obj
        for k in path.split("."):
            cur = cur.get(k) if isinstance(cur, dict) else None
            if cur is None:
                break
        if cur is not None:
            return cur
    return None


def find_all(obj, key):
    """Every value stored under `key` anywhere in a nested structure, with its parent dict."""
    if isinstance(obj, dict):
        if key in obj:
            yield obj
        for v in obj.values():
            yield from find_all(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_all(v, key)


def chunks(start, end, days):
    cur = start
    while cur <= end:
        stop = min(end, cur + dt.timedelta(days=days - 1))
        yield cur, stop
        cur = stop + dt.timedelta(days=1)


def rhr_by_date(obj, date=None, out=None):
    """{date: resting HR} from any nesting: lists of day records, dicts keyed
    by date, or a value under restingHeartRate / restingHeartRateValue / rhr."""
    out = {} if out is None else out
    if isinstance(obj, dict):
        date = str(obj.get("calendarDate") or obj.get("summaryDate") or obj.get("date") or date or "")[:10] or None
        for k, v in obj.items():
            if RHR_KEY.search(str(k)) and isinstance(v, (int, float)) and not isinstance(v, bool) and 25 < v < 120:
                if date:
                    out.setdefault(date, v)
            elif isinstance(v, (dict, list)):
                rhr_by_date(v, k[:10] if DATE_KEY.match(str(k)) else date, out)
    elif isinstance(obj, list):
        for v in obj:
            rhr_by_date(v, date, out)
    return out


def key_tree(obj, prefix="", depth=0, out=None):
    """Field paths and value types only (no values), for `pacelab.py inspect`."""
    out = [] if out is None else out
    if depth > 5:
        return out
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:60]:
            name = "<tanggal>" if DATE_KEY.match(str(k)) else str(k)
            path = prefix + "." + name if prefix else name
            if isinstance(v, (dict, list)):
                key_tree(v, path, depth + 1, out)
            elif path not in [p for p, _ in out]:
                out.append((path, type(v).__name__))
    elif isinstance(obj, list) and obj:
        key_tree(obj[0], prefix + "[]", depth + 1, out)
    return out


# ------------------------------------------------------------------ normalize

# activity-list field -> short key in runs.json "g" (all optional; units as Garmin sends them)
GARMIN_FIELDS = [
    ("moving_s", "movingDuration"), ("elapsed_s", "elapsedDuration"), ("hr_max", "maxHR"),
    ("cad", "averageRunningCadenceInStepsPerMinute"), ("cad_max", "maxRunningCadenceInStepsPerMinute"),
    ("speed", "averageSpeed"), ("speed_max", "maxSpeed"), ("gain_m", "elevationGain"), ("loss_m", "elevationLoss"),
    ("stride_cm", "avgStrideLength"), ("gct_ms", "avgGroundContactTime"), ("vo_cm", "avgVerticalOscillation"),
    ("vr_pct", "avgVerticalRatio"), ("power", "avgPower"), ("power_max", "maxPower"), ("power_norm", "normPower"),
    ("te_aer", "aerobicTrainingEffect"), ("te_ana", "anaerobicTrainingEffect"), ("te_label", "trainingEffectLabel"),
    ("load", "activityTrainingLoad"), ("lt_bpm", "lactateThresholdBpm"), ("kcal", "calories"), ("steps", "steps"),
    ("temp_min", "minTemperature"), ("temp_max", "maxTemperature"), ("laps", "lapCount"), ("pr", "isPR"),
    ("water_ml", "waterEstimated")]


def norm_run(a):
    dist = pick(a, "distance") or 0
    return {
        "id": a.get("activityId"),
        "date": str(pick(a, "startTimeLocal") or "")[:10],
        "start": pick(a, "startTimeLocal"),
        "name": a.get("activityName"),
        "type": pick(a, "activityType.typeKey"),
        "km": round(dist / 1000.0, 3),
        "sec": round(pick(a, "duration", "movingDuration", "elapsedDuration") or 0, 1),
        "avg_hr": pick(a, "averageHR"),
        # everything else Garmin already summarises for the run, kept as Garmin reports it
        "g": {k: v for k, v in ((k, a.get(f)) for k, f in GARMIN_FIELDS) if v is not None},
    }


def norm_stream(details):
    """activity details -> {"t": seconds, "d": metres, "hr": bpm} or None."""
    desc = details.get("metricDescriptors") or []
    idx = {m.get("key"): m.get("metricsIndex") for m in desc}
    rows = [r.get("metrics") for r in details.get("activityDetailMetrics") or [] if r.get("metrics")]
    if not rows or "sumDistance" not in idx:
        return None
    ti = next((idx[k] for k in ("sumDuration", "sumElapsedDuration", "directTimestamp") if k in idx), None)
    if ti is None:
        return None
    ts_ms = ti == idx.get("directTimestamp") and "sumDuration" not in idx and "sumElapsedDuration" not in idx
    hi = idx.get("directHeartRate")
    ci = next((idx[k] for k in ("directDoubleCadence", "directRunCadence") if k in idx), None)
    ei = next((idx[k] for k in ("directElevation", "directCorrectedElevation") if k in idx), None)
    t, d, hr, cad, el = [], [], [], [], []
    val = lambda r, i: r[i] if i is not None and i < len(r) else None
    t0 = None
    for r in rows:
        tv, dv = r[ti], r[idx["sumDistance"]]
        if tv is None or dv is None:
            continue
        if ts_ms:
            t0 = tv if t0 is None else t0
            tv = (tv - t0) / 1000.0
        if t and (tv < t[-1] or dv < d[-1]):
            continue  # keep the stream monotonic
        t.append(round(tv, 1))
        d.append(round(dv, 1))
        hv = r[hi] if hi is not None and hi < len(r) else None
        hr.append(round(hv) if hv else None)
        cv, ev = val(r, ci), val(r, ei)
        cad.append(round(cv) if cv else None)
        el.append(round(ev, 1) if ev is not None else None)
    if len(t) < 2:
        return None
    # some watches report steps per minute of one leg (~85): double it to steps per minute
    cs = sorted(c for c in cad if c)
    if cs and cs[len(cs) // 2] < 120:
        cad = [c * 2 if c else None for c in cad]
    return {"t": t, "d": d, "hr": hr, "cad": cad if cs else None, "el": el if any(e is not None for e in el) else None,
            "v": STREAM_V, "keys": sorted(k for k in idx if k)}


def norm_sleep(item):
    secs = pick(item, "sleepTimeSeconds")
    if secs is None:
        parts = [pick(item, k) for k in ("deepSleepSeconds", "lightSleepSeconds", "remSleepSeconds")]
        secs = sum(p for p in parts if p) or None
    date = pick(item, "calendarDate")
    return date, {
        "sleep_s": secs,
        "rhr_sleep": rhr_by_date(item, date).get(str(date)[:10]) if date else None,
        "sleep_score": pick(item, "sleepScores.overall.value", "overallSleepScore.value", "sleepScore"),
    }


def norm_hrv(item):
    return pick(item, "calendarDate"), {
        "hrv": pick(item, "lastNightAvg"),
        "hrv_status": ((pick(item, "status") or "").upper() or None) if (pick(item, "status") or "").upper() != "NONE" else None,
        "hrv_low": pick(item, "baseline.balancedLow"),
    }


def norm_bb(item):
    vals = [v[1] for v in pick(item, "bodyBatteryValuesArray") or []
            if isinstance(v, (list, tuple)) and len(v) > 1 and isinstance(v[1], (int, float))]
    # the day's peak is the reading after the night's recharge
    return pick(item, "date", "calendarDate"), {"bb": max(vals) if vals else None}


def norm_daily(item):
    """v2 daily summary: data[].heartRate.restingValue, data[].bodyBattery.maxValue."""
    date = pick(item, "calendarDate")
    rhr = pick(item, "heartRate.restingValue") or rhr_by_date(item, date).get(str(date)[:10])
    return date, {"rhr": rhr if rhr and 25 < rhr < 120 else None,
                  "bb": pick(item, "bodyBattery.maxValue")}


def norm_weight(item):
    g = pick(item, "latestWeight.weight", "weight")
    date = pick(item, "summaryDate", "calendarDate", "latestWeight.calendarDate")
    if g is None or not date:
        return None, {}
    return date, {"weight": round(g / 1000.0 if g > 1000 else g, 2)}


# ------------------------------------------------------------------ sync

class Syncer:
    def __init__(self, client, out_dir, log=print):
        self.c = client
        self.dir = Path(out_dir)
        self.log = log
        self.state = _read(self.dir / "state.json", {})
        self.runs = {r["id"]: r for r in _read(self.dir / "runs.json", [])}
        self.well = _read(self.dir / "wellness.json", {})
        self.unavailable = []
        self.no_stream = set(self.state.get("no_stream", []))
        self.refetch = self.state.get("stream_v", 1) < STREAM_V  # older streams lack cadence/elevation
        self.no_fit = set(self.state.get("no_fit", []))
        if self.state.get("fit_v", 0) < FIT_V:
            self.no_fit = set()

    def run(self, since, until):
        new_runs = self.sync_runs(since, until)
        days = self.sync_wellness(since, until)
        self.state["last_sync"] = dt.datetime.now().isoformat(timespec="seconds")
        _write(self.dir / "state.json", self.state)
        return {"new_runs": new_runs, "runs": len(self.runs), "wellness_days": days,
                "requests": self.c.requests, "unavailable": self.unavailable}

    # -------------------------------------------------------------- runs
    def sync_runs(self, since, until):
        start, page, new = 0, 50, 0
        while True:
            items = self.c.get(ACT_LIST, {"start": start, "limit": page, "startDate": since.isoformat(),
                                          "endDate": until.isoformat(), "activityType": "running"})
            if items is None:
                self.unavailable.append("activities")
                return new
            for a in items:
                r = norm_run(a)
                if r["id"] is None or not r["date"]:
                    continue
                has_stream = (self.dir / "streams" / ("%s.json" % r["id"])).is_file()
                stale = self.refetch and has_stream
                if r["id"] not in self.runs or stale or not (has_stream or r["id"] in self.no_stream):
                    self._stream(r)
                    new += 1
                    if new % 25 == 0:
                        self.log("    %d lari diunduh..." % new)
                if not (self.dir / "laps" / ("%s.json" % r["id"])).is_file() and r["id"] not in self.no_fit:
                    self._fit(r)
                self.runs[r["id"]] = r
            _write(self.dir / "runs.json", sorted(self.runs.values(), key=lambda x: x["start"] or x["date"]))
            if len(items) < page:
                self.refetch = False
                self.state["stream_v"] = STREAM_V
                self.state["fit_v"] = FIT_V
                return new
            start += page

    def _stream(self, r):
        det = self.c.get(ACT_DETAILS % r["id"], {"maxChartSize": 100000, "maxPolylineSize": 0})
        s = norm_stream(det) if isinstance(det, dict) else None
        if s:
            _write(self.dir / "streams" / ("%s.json" % r["id"]), s)
        else:
            self.no_stream.add(r["id"])  # asked once; not retried on later syncs
            self.state["no_stream"] = sorted(self.no_stream)
            self.log("    ! %s %.1f km: data per detik tidak tersedia" % (r["date"], r["km"]))

    def _fit(self, r):
        """The watch's own file: laps as recorded, and the per-second data when the details answer was empty
        (Garmin's details stop for runs older than ~120 days; the FIT file does not)."""
        try:
            blob = self.c.get(FIT_DOWNLOAD % r["id"], raw=True)
        except ApiError:
            return                      # a passing failure: asked again on the next sync
        try:
            got = fit.read(blob) if blob else None
        except (ValueError, KeyError, IndexError, struct.error, zipfile.BadZipFile):
            got = None
        if not got:
            self.no_fit.add(r["id"])
            self.state["no_fit"] = sorted(self.no_fit)
            return
        _write(self.dir / "laps" / ("%s.json" % r["id"]), {"laps": got["laps"], "session": got["session"]})
        sp = self.dir / "streams" / ("%s.json" % r["id"])
        if got["stream"] and not sp.is_file():
            _write(sp, dict(got["stream"], v=STREAM_V, keys=["fit"]))
            self.no_stream.discard(r["id"])
            self.state["no_stream"] = sorted(self.no_stream)
            self.log("    + %s %.1f km: data per detik dari file FIT" % (r["date"], r["km"]))

    # -------------------------------------------------------------- wellness
    def sync_wellness(self, since, until):
        done = self.state.get("wellness_until") if self.state.get("schema") == SCHEMA else None
        if done is None and self.state.get("schema") != SCHEMA:
            self.well = {}  # parsing changed: rebuild from scratch, not on top of old values
        start = since
        if done:
            start = max(since, dt.date.fromisoformat(done) - dt.timedelta(days=REFETCH_DAYS))
        if start > until:
            return 0
        self._ranged("sleep", start, until, lambda a, b: self.c.get(SLEEP, {"startDate": a, "endDate": b}),
                     lambda r: r if isinstance(r, list) else pick(r, "dailySleepSummaries", "sleepSummaries") or [],
                     norm_sleep)
        self._ranged("hrv", start, until, lambda a, b: self.c.get(HRV % (a, b)),
                     lambda r: pick(r, "hrvSummaries") or [], norm_hrv)
        self._ranged("bb", start, until, lambda a, b: self.c.get(BB, {"startDate": a, "endDate": b}),
                     lambda r: r if isinstance(r, list) else [], norm_bb)
        self._ranged("daily", start, until, lambda a, b: self.c.get(DAILY, {"startDate": a, "endDate": b}),
                     lambda r: pick(r, "data") if isinstance(pick(r, "data"), list) else (r if isinstance(r, list) else []),
                     norm_daily)
        self._ranged("weight", start, until, lambda a, b: self.c.get(WEIGHT % (a, b), {"includeAll": "true"}),
                     lambda r: pick(r, "dailyWeightSummaries") or [], norm_weight)
        for day in self.well.values():
            if day.get("hrv_status") == "NONE":
                day.pop("hrv_status")
        self.state["wellness_until"] = until.isoformat()
        self.state["schema"] = SCHEMA
        _write(self.dir / "wellness.json", dict(sorted(self.well.items())))
        return (until - start).days + 1

    def _ranged(self, name, start, end, fetch, items, norm):
        size = CHUNK[name]
        for a, b in chunks(start, end, size):
            try:
                resp = fetch(a.isoformat(), b.isoformat())
            except ApiError as e:
                if e.status == 400 and size > 7:  # range too long: retry smaller
                    CHUNK[name] = max(7, size // 2)
                    return self._ranged(name, a, end, fetch, items, norm)
                raise
            if resp is None:
                self.unavailable.append(name)
                return
            for it in items(resp):
                date, vals = norm(it)
                if not date:
                    continue
                day = self.well.setdefault(str(date)[:10], {})
                day.update({k: v for k, v in vals.items() if v is not None})
