"""Pure computations: weekly totals, best efforts, decoupling, readiness light,
Saturday long-run rule, badges and the weekly head-to-head score.

Inputs are the normalized records written by sync.py:
  run      {"id", "date": "YYYY-MM-DD", "km", "sec", "avg_hr"}
  stream   {"t": [s], "d": [m], "hr": [bpm]}   (same length, t ascending)
  wellness {"YYYY-MM-DD": {"sleep_s", "hrv", "hrv_status", "bb", "rhr", "weight"}}
"""
import datetime as dt
import statistics

DIST = {"5K": 5000.0, "10K": 10000.0, "Half": 21097.5, "Full": 42195.0}
RIEGEL = 1.06
EST_WINDOW_DAYS = 120
LONG_RUN_MIN_KM = 10.0
STREAK_PCT = 0.90


def d(s):
    return dt.date.fromisoformat(s)


def ms_of(date, ms1):
    return (d(date) - d(ms1)).days // 7 + 1


# ---------------------------------------------------------------- streams

def best_effort(stream, dist_m):
    """Fastest time (s) to cover dist_m anywhere in the run, or None."""
    t, x = stream.get("t") or [], stream.get("d") or []
    n = len(t)
    if n < 2 or x[-1] - x[0] < dist_m:
        return None
    best, j = None, 0
    for i in range(n):
        while j < n and x[j] - x[i] < dist_m:
            j += 1
        if j >= n:
            break
        # interpolate the exact moment dist_m is reached between j-1 and j
        span = x[j] - x[j - 1]
        frac = (x[i] + dist_m - x[j - 1]) / span if span > 0 else 1.0
        end = t[j - 1] + frac * (t[j] - t[j - 1])
        dur = end - t[i]
        if best is None or dur < best:
            best = dur
    return best


def decoupling(stream):
    """Pa:HR decoupling in %: efficiency (speed/HR) of the 1st vs 2nd half of
    moving time. Positive = the 2nd half cost more heart rate per speed."""
    t, x, hr = stream.get("t") or [], stream.get("d") or [], stream.get("hr") or []
    seg = []  # (dt, dd, hr) for moving samples with HR
    for i in range(1, min(len(t), len(x), len(hr))):
        dtt, dd = t[i] - t[i - 1], x[i] - x[i - 1]
        if dtt <= 0 or dtt > 30 or dd / dtt < 1.0 or not hr[i]:
            continue  # pause, gap or walking-pace stop
        seg.append((dtt, dd, hr[i]))
    total = sum(s[0] for s in seg)
    if total < 20 * 60:
        return None
    halves, acc = ([], []), 0.0
    for s in seg:
        halves[0 if acc < total / 2 else 1].append(s)
        acc += s[0]

    def ef(h):
        tt = sum(s[0] for s in h)
        speed = sum(s[1] for s in h) / tt
        mean_hr = sum(s[0] * s[2] for s in h) / tt
        return speed / mean_hr

    e1, e2 = ef(halves[0]), ef(halves[1])
    return round((e1 - e2) / e1 * 100, 1)


# ---------------------------------------------------------------- weeks

def weekly(runs, program, today):
    """Per program week up to the current one: target vs actual."""
    targets = {w["ms"]: w for w in program["weeks"]}
    cur = ms_of(today.isoformat(), program["ms1"])
    out = []
    for ms in range(1, min(cur, program["total_weeks"]) + 1):
        start = d(program["ms1"]) + dt.timedelta(weeks=ms - 1)
        end = start + dt.timedelta(days=6)
        wk = [r for r in runs if start <= d(r["date"]) <= end]
        longest = max(wk, key=lambda r: r["km"]) if wk else None
        tg = targets.get(ms, {})
        out.append({
            "ms": ms, "start": start.isoformat(), "end": end.isoformat(),
            "km": round(sum(r["km"] for r in wk), 1),
            "lr": round(longest["km"], 1) if longest else None,
            "lr_id": longest["id"] if longest and longest["km"] >= LONG_RUN_MIN_KM else None,
            "km_t": tg.get("km"), "lr_t": tg.get("lr"),
            "down": tg.get("down", False), "event": tg.get("event", False),
            "phase": tg.get("phase"), "done": end < today,
        })
    return out


def streaks(weeks):
    """Longest run of consecutive completed weeks with km >= 90% of target."""
    best = cur = 0
    for w in weeks:
        if not w["done"] or not w["km_t"] or w["km"] is None:
            continue
        cur = cur + 1 if w["km"] >= STREAK_PCT * w["km_t"] else 0
        best = max(best, cur)
    return best


# ---------------------------------------------------------------- best efforts

def efforts(runs, streams):
    """{dist: [(date, sec, run_id)]} best effort of every run, chronological."""
    out = {k: [] for k in ("5K", "10K", "Half")}
    for r in sorted(runs, key=lambda r: r["date"]):
        s = streams.get(r["id"])
        if not s:
            continue
        for k in out:
            v = best_effort(s, DIST[k])
            if v:
                out[k].append((r["date"], round(v), r["id"]))
    return out


def pb_progress(eff):
    """Only the efforts that improved the running best: the PB staircase."""
    out = {}
    for k, rows in eff.items():
        best, pts = None, []
        for date, sec, rid in rows:
            if best is None or sec < best:
                best = sec
                pts.append({"date": date, "sec": sec, "id": rid})
        out[k] = pts
    return out


def riegel(sec, from_m, to_m=DIST["Full"]):
    return sec * (to_m / from_m) ** RIEGEL


def marathon_estimate(eff, on_date):
    """Riegel estimate from the longest distance with an effort in the last
    120 days (Half > 10K > 5K). Returns (sec, source) or (None, None)."""
    lo = on_date - dt.timedelta(days=EST_WINDOW_DAYS)
    for k in ("Half", "10K", "5K"):
        recent = [s for date, s, _ in eff.get(k, []) if lo <= d(date) <= on_date]
        if recent:
            return round(riegel(min(recent), DIST[k])), k
    return None, None


def estimate_series(eff, start, today):
    """Marathon estimate at each month end (and today)."""
    pts, m = [], dt.date(start.year, start.month, 1)
    while True:
        nxt = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        day = min(nxt - dt.timedelta(days=1), today)
        sec, src = marathon_estimate(eff, day)
        if sec:
            pts.append({"date": day.isoformat(), "sec": sec, "from": src})
        if day >= today:
            return pts
        m = nxt


# ---------------------------------------------------------------- readiness

LOW_HRV = ("LOW", "POOR")


def _rhr_base(wellness, day):
    prev = [wellness[k]["rhr"] for k in wellness
            if wellness[k].get("rhr") and 0 < (day - d(k)).days <= 28]
    return statistics.median(prev) if len(prev) >= 7 else None


def _hrv_low_run(wellness, day):
    n = 0
    while True:
        w = wellness.get((day - dt.timedelta(days=n)).isoformat(), {})
        if w.get("hrv_status") in LOW_HRV:
            n += 1
        else:
            return n


def light(wellness, day):
    """Daily light from the program's 'Lampu harian' table.

    MERAH : HRV below normal 3 days running, or RHR +7 vs 28-day median
    ORANYE: HRV below normal 2 days running, or Body Battery < 40, or RHR +5
    HIJAU : HRV balanced, Body Battery > 60 and sleep >= 6 h
    KUNING: anything else (HRV slightly down, BB 40-60, sleep < 6 h)
    Returns None when there is no data for the day.
    """
    w = wellness.get(day.isoformat())
    if not w:
        return None
    low_run = _hrv_low_run(wellness, day)
    base = _rhr_base(wellness, day)
    rhr_up = (w["rhr"] - base) if w.get("rhr") and base else 0
    bb, sl, st = w.get("bb"), w.get("sleep_s"), w.get("hrv_status")
    why = []
    if low_run >= 3 or rhr_up >= 7:
        level = "merah"
    elif low_run >= 2 or (bb is not None and bb < 40) or rhr_up >= 5:
        level = "oranye"
    elif st == "BALANCED" and bb is not None and bb > 60 and sl and sl >= 6 * 3600:
        level = "hijau"
    else:
        level = "kuning"
    if rhr_up:
        why.append("RHR %+d" % round(rhr_up))
    return {"level": level, "hrv": w.get("hrv"), "hrv_status": st, "bb": bb,
            "sleep_s": sl, "rhr": w.get("rhr"), "notes": why}


def saturday_rule(w):
    """'Aturan potong long run' for the night before a long run."""
    if not w:
        return None
    sl = (w.get("sleep_s") or 0) / 3600
    bb = w.get("bb")
    if bb is None or not w.get("sleep_s"):
        return None
    if sl < 5 and bb < 30 and w.get("hrv_status") in LOW_HRV:
        return "Ganti easy 8 km"
    if sl < 5 and bb < 40:
        return "Potong 40%"
    if sl >= 6 and bb >= 50:
        return "Jalankan"
    return "Potong 20%"


# ---------------------------------------------------------------- badges & score

def badges(runs, weeks, eff, ms1):
    longest = max([r["km"] for r in runs] or [0])
    month = {}
    for r in runs:
        month[r["date"][:7]] = month.get(r["date"][:7], 0) + r["km"]
    streak = streaks(weeks)

    def pr_in_program(k):
        rows = eff.get(k, [])
        before = [s for date, s, _ in rows if date < ms1]
        during = [s for date, s, _ in rows if date >= ms1]
        return bool(during) and (not before or min(during) < min(before))

    return [
        {"id": "21K", "on": longest >= 21.0975},
        {"id": "25K", "on": longest >= 25},
        {"id": "30K", "on": longest >= 30},
        {"id": "35K", "on": longest >= 35},
        {"id": "100/bln", "on": max(month.values() or [0]) >= 100},
        {"id": "7 mgg", "on": streak >= 7},
        {"id": "14 mgg", "on": streak >= 14},
        {"id": "PR 5K", "on": pr_in_program("5K")},
        {"id": "PR 10K", "on": pr_in_program("10K")},
    ]


def week_stats(week, wellness, lights, sleep_min):
    """Score inputs for one athlete-week."""
    days = [(d(week["start"]) + dt.timedelta(days=i)).isoformat() for i in range(7)]
    sleeps = [wellness[x]["sleep_s"] for x in days if wellness.get(x, {}).get("sleep_s")]
    sl = sum(sleeps) / len(sleeps) if sleeps else None
    return {
        "km_pct": week["km"] / week["km_t"] if week["km_t"] else None,
        "lr_pct": (week["lr"] or 0) / week["lr_t"] if week["lr_t"] else None,
        "sleep_s": sl,
        "sleep_pct": sl / sleep_min if sl and sleep_min else None,
        "green": sum(1 for x in days if (lights.get(x) or {}).get("level") == "hijau"),
    }


def score(a, b):
    """Head-to-head categories; higher wins, ties score nobody.
    Sleep is compared as % of each athlete's own minimum target."""
    cats = []
    for key, cmp_key in (("km", "km_pct"), ("lr", "lr_pct"), ("tidur", "sleep_pct"), ("hijau", "green")):
        va, vb = a.get(cmp_key), b.get(cmp_key)
        if va is None or vb is None:
            win = None
        else:
            win = 0 if va > vb else 1 if vb > va else None
        cats.append({"cat": key, "win": win})
    return {"a": sum(c["win"] == 0 for c in cats), "b": sum(c["win"] == 1 for c in cats), "cats": cats}
