"""Fake Garmin Personal API for tests and the demo dashboard.

Serves synthetic data in the response shapes sync.py reads. It is NOT real
Garmin output: field names follow the community-documented web API and the
probe report; run `python pacelab.py check` on real data to confirm them.

Usage: python tools/mock_garmin.py [port]   (keys: demo-taofik, demo-reza)
"""
import datetime as dt
import math
import json
import random
import re
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import fitgen

PROFILES = {
    "demo-taofik": {"seed": 7, "easy": 470, "hr": 142, "fit_gain": .12, "rhr": 52, "hrv": 52, "sleep": 6.6, "bb": 72, "kg": 68.0},
    "demo-reza": {"seed": 11, "easy": 545, "hr": 146, "fit_gain": .10, "rhr": 61, "hrv": 36, "sleep": 5.8, "bb": 50, "kg": 81.5},
}
START = dt.date(2026, 3, 23)
DETAILS_DAYS = 120   # like Garmin: per-second details only for recent runs; the FIT file always
MS1 = dt.date(2026, 6, 22)


def week_plan(ms):
    """Rough weekly km / long run before and after MS7 (enough for a demo)."""
    if ms < 1:
        return 18, 8
    base = [20, 21, 22, 23, 24, 22, 28, 30, 32, 24, 34, 36, 38, 28, 40, 24, 21, 36, 43, 31, 33, 45, 46, 48, 35]
    km = base[min(ms - 1, len(base) - 1)]
    return km, max(8, round(km * .5))


def demo_program():
    """Synthetic 51-week program (same shape as pacelab.program.load_program)
    so `pacelab.py demo` runs before the real Excel files are copied in."""
    phases = [("Base", 7, 15), ("Support", 16, 21), ("Build", 22, 31), ("Absorb", 32, 33),
              ("Ramadan", 34, 38), ("Rebuild", 39, 42), ("Marathon", 43, 48), ("Taper", 49, 51)]
    down = {10, 14, 21, 25, 29, 34, 35, 36, 37, 38, 46, 49, 50}
    event = {9, 16, 20, 31, 42, 51}
    weeks = []
    for ms in range(7, 52):
        km = round(min(56, 26 + ms * .65) * (.7 if ms in down else 1))
        lr = None if ms in event else round(min(24, km * .5))
        weeks.append({"ms": ms, "start": (MS1 + dt.timedelta(weeks=ms - 1)).isoformat(),
                      "phase": next(n for n, a, b in phases if a <= ms <= b),
                      "km": float(km), "lr": float(lr) if lr else None,
                      "down": ms in down, "event": ms in event, "note": ""})
    return {
        "name": "Demo", "ms1": MS1.isoformat(), "race_date": "2027-06-13", "total_weeks": 51, "weeks": weeks,
        "events": [{"ms": 20, "date": "2026-11-07", "event": "LOMBA 10K"},
                   {"ms": 31, "date": "2027-01-23", "event": "LOMBA HALF MARATHON"},
                   {"ms": 42, "date": "2027-04-10", "event": "Tes 10K"},
                   {"ms": 51, "date": "2027-06-13", "event": "MARATON"}],
        "target": {"B": {"lo": 17100, "hi": 18900, "text": "4:45:00 - 5:15:00"}},
        "sleep": {"min": 23400, "before_lr": 25200},
        "weight": [],
    }


class Athlete:
    def __init__(self, key, today):
        p = PROFILES[key]
        self.p, self.today = p, today
        rnd = random.Random(p["seed"])
        self.runs, self.streams, self.well, self.fits = [], {}, {}, {}
        day, aid = START, p["seed"] * 10 ** 8
        while day <= today:
            ms = (day - MS1).days // 7 + 1
            km, lr = week_plan(ms)
            prog = min(1, (day - START).days / 220)
            fitness = 1 - p["fit_gain"] * prog  # pace multiplier
            plan = {1: km * .2, 3: km * .2, 5: lr, 6: km - lr - km * .4}  # Tue Thu Sat Sun
            if day.weekday() in plan and day < today:
                dist = max(3, plan[day.weekday()] * rnd.uniform(.9, 1.06))
                pace = p["easy"] * fitness * rnd.uniform(.97, 1.04)
                if day == dt.date(2026, 10, 11):  # 5K race
                    dist, pace = 5.02, p["easy"] * fitness * .74
                aid += 1
                self._add_run(aid, day, dist, pace, rnd, race=day == dt.date(2026, 10, 11),
                              tempo=day.weekday() == 1 and dist >= 6)
            self._add_day(day, rnd, prog)
            day += dt.timedelta(days=1)

    def _add_run(self, aid, day, km, pace, rnd, race=False, tempo=False):
        step, t, d, hr, rows = 5, 0.0, 0.0, [], []
        total = km * 1000
        drift = rnd.uniform(.04, .14) if km >= 10 else .02
        while d < total:
            frac = d / total
            hard = tempo and 2500 <= d < 5500           # a tempo block after warm-up and strides
            v = 1000 / (pace * (.8 if hard else 1) * (1 + rnd.uniform(-.03, .03)))
            h = self.p["hr"] * (1.12 if race or hard else 1) * (1 + drift * frac) + rnd.uniform(-2, 2)
            cad = (172 if self.p["hr"] > 145 else 168) + rnd.uniform(-2, 2) - (5 * frac if km >= 15 else 1 * frac)
            ele = 15 + 8 * math.sin(d / 1700.0) + 4 * math.sin(d / 430.0)
            rows.append([t, round(d, 1), round(h), round(v, 3), round(cad), round(ele, 1)])
            t += step
            d = min(total, d + v * step)
        rows.append([t, round(total, 1)] + rows[-1][2:])
        start = dt.datetime.combine(day, dt.time(5, rnd.randint(30, 59)))
        self.fits[aid] = ([(r[0], r[1], r[2], r[4], r[5]) for r in rows], int(start.replace(tzinfo=dt.timezone.utc).timestamp()) - 7 * 3600,
                          (2160, 2320, 2480) if tempo else ())
        old = day < self.today - dt.timedelta(days=DETAILS_DAYS)
        self.streams[aid] = {
            "activityId": aid, "measurementCount": 6, "metricsCount": 0 if old else len(rows),
            "metricDescriptors": [{"metricsIndex": 0, "key": "sumDuration"}, {"metricsIndex": 1, "key": "sumDistance"},
                                  {"metricsIndex": 2, "key": "directHeartRate"}, {"metricsIndex": 3, "key": "directSpeed"},
                                  {"metricsIndex": 4, "key": "directDoubleCadence"}, {"metricsIndex": 5, "key": "directElevation"}],
            "activityDetailMetrics": [] if old else [{"metrics": r} for r in rows]}
        self.runs.append({
            "activityId": aid, "activityName": "Lari" if not race else "Race 5K",
            "activityType": {"typeKey": "running"},
            "startTimeLocal": start.strftime("%Y-%m-%d %H:%M:%S"),
            "distance": round(total, 1), "duration": round(t, 1), "averageHR": round(sum(r[2] for r in rows) / len(rows)),
            "movingDuration": round(t - 4, 1), "elapsedDuration": round(t + 30, 1), "maxHR": max(r[2] for r in rows),
            "averageRunningCadenceInStepsPerMinute": round(sum(r[4] for r in rows) / len(rows), 1),
            "maxRunningCadenceInStepsPerMinute": max(r[4] for r in rows), "averageSpeed": round(total / t, 3),
            "elevationGain": round(sum(max(0, b[5] - a[5]) for a, b in zip(rows, rows[1:])), 1),
            "elevationLoss": round(sum(max(0, a[5] - b[5]) for a, b in zip(rows, rows[1:])), 1),
            "avgStrideLength": round(total / t / (sum(r[4] for r in rows) / len(rows) / 60) * 100, 1),
            "aerobicTrainingEffect": round(min(5, 1.6 + km / 8 + (1 if tempo or race else 0)), 1),
            "anaerobicTrainingEffect": round(1.4 if tempo or race else .3, 1),
            "trainingEffectLabel": "TEMPO" if tempo else "VO2MAX" if race else "AEROBIC_BASE",
            "activityTrainingLoad": round(km * 9 * (1.4 if tempo or race else 1), 1), "calories": round(km * 68),
            "lapCount": int(total // 1000) + 1 + (3 if tempo else 0), "minTemperature": 26.0, "maxTemperature": 31.0})

    def _add_day(self, day, rnd, prog):
        p = self.p
        sl = max(3.8, rnd.gauss(p["sleep"] + .3 * prog, .55))
        hrv = round(rnd.gauss(p["hrv"] + 3 * prog, 4))
        status = "BALANCED" if hrv >= p["hrv"] - 4 else ("UNBALANCED" if hrv >= p["hrv"] - 8 else "LOW")
        bb = int(max(15, min(100, rnd.gauss(p["bb"] + (sl - p["sleep"]) * 12, 8))))
        self.well[day.isoformat()] = {
            "sleep": round(sl * 3600), "score": int(min(95, 40 + sl * 7)), "hrv": hrv, "status": status,
            "bb": bb, "rhr": round(rnd.gauss(p["rhr"] - 2 * prog, 1.3)),
            "kg": round(p["kg"] - (1.2 if p["kg"] > 75 else 0) * prog + rnd.uniform(-.4, .4), 1) if day.weekday() == 6 else None}

    # ----------------------------------------------------------- responses
    def days(self, a, b):
        a, b = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
        return [(k, v) for k, v in sorted(self.well.items()) if a <= dt.date.fromisoformat(k) <= b]

    def respond(self, path, q):
        if path.startswith("/activitylist-service/activities/search/activities"):
            rs = [r for r in self.runs if q.get("startDate", "0") <= r["startTimeLocal"][:10] <= q.get("endDate", "9")]
            rs = sorted(rs, key=lambda r: r["startTimeLocal"], reverse=True)
            s, n = int(q.get("start", 0)), int(q.get("limit", 20))
            return rs[s:s + n]
        m = re.match(r"/download-service/files/activity/(\d+)$", path)
        if m and int(m.group(1)) in self.fits:
            rows, start, manual = self.fits[int(m.group(1))]
            return RawBody(fitgen.zipped(fitgen.write_fit(rows, start, manual=manual), "%s_ACTIVITY.fit" % m.group(1)))
        m = re.match(r"/activity-service/activity/(\d+)/details$", path)
        if m:
            return self.streams.get(int(m.group(1)))
        if path == "/sleep-service/sleep/dailySleepSummariesByDate":
            return [{"calendarDate": k, "sleepTimeSeconds": v["sleep"], "deepSleepSeconds": v["sleep"] // 5,
                     "sleepScores": {"overall": {"value": v["score"]}}} for k, v in self.days(q["startDate"], q["endDate"])]
        m = re.match(r"/hrv-service/hrv/daily/([\d-]+)/([\d-]+)$", path)
        if m:
            return {"userProfilePk": 1, "hrvSummaries": [
                {"calendarDate": k, "lastNightAvg": v["hrv"], "status": v["status"],
                 "baseline": {"balancedLow": self.p["hrv"] - 4, "balancedUpper": self.p["hrv"] + 8}}
                for k, v in self.days(m.group(1), m.group(2))]}
        if path == "/wellness-service/wellness/bodyBattery/reports/daily":
            return [{"date": k, "charged": v["bb"] - 20, "drained": 50}
                    for k, v in self.days(q["startDate"], q["endDate"])]
        if path == "/usersummary-service/v2/dailysummaries":
            return {"data": [{"calendarDate": k, "heartRate": {"minValue": v["rhr"] - 3, "maxValue": 160, "restingValue": v["rhr"]},
                              "bodyBattery": {"minValue": 10, "maxValue": v["bb"], "chargedValue": 40}}
                             for k, v in self.days(q["startDate"], q["endDate"])]}
        m = re.match(r"/weight-service/weight/range/([\d-]+)/([\d-]+)$", path)
        if m:
            return {"dailyWeightSummaries": [{"summaryDate": k, "latestWeight": {"weight": v["kg"] * 1000}}
                                             for k, v in self.days(m.group(1), m.group(2)) if v["kg"]]}
        return None


class RawBody(bytes):
    """A binary answer (the FIT zip), sent as is."""


def make_server(port=0, today=None):
    today = today or dt.date.today()
    athletes = {k: Athlete(k, today) for k in PROFILES}
    tokens = {}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, obj=None):
            body = json.dumps(obj).encode() if obj is not None else b'{"error":"NOT_FOUND","status":404}'
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            key = (self.headers.get("Authorization") or "").replace("ApiKey ", "")
            if key not in athletes:
                return self._send(401, {"error": "invalid key"})
            tok = "tok-" + key
            tokens[tok] = athletes[key]
            body = tok.encode()  # real API returns a raw token string
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            ath = tokens.get((self.headers.get("Authorization") or "").replace("Bearer ", ""))
            if not ath:
                return self._send(401, {"error": "unauthorized"})
            u = urllib.parse.urlparse(self.path)
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            resp = ath.respond(u.path, q)
            if isinstance(resp, RawBody):
                self.send_response(200)
                self.send_header("Content-Type", "application/x-zip-compressed")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                return self.wfile.write(resp)
            self._send(200 if resp is not None else 404, resp)

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    s = make_server(int(sys.argv[1]) if len(sys.argv) > 1 else 8787)
    print("Mock Garmin di http://127.0.0.1:%d  (Ctrl+C untuk berhenti)" % s.server_port)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
