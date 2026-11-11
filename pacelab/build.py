"""Turn synced data + program workbooks into one offline dashboard.html."""
import datetime as dt
import json
from pathlib import Path

from . import metrics as m
from . import overrides
from .program import load_program

WEB = Path(__file__).parent / "web"
DAYS = 60  # daily history shipped to the page (period filter: 7 / 14 / 30 / 60 days)
COLORS = ["t", "r"]  # CSS series slots: first athlete blue, second orange


def _read(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


PS_SCALE = {"t": 1, "d": 10, "hr": 1, "cad": 1, "el": 10, "sp": 1000, "tc": 1}


def per_second(stream):
    """Per-second data packed for the page ("Semua data (.zip)"): per field, integers at PS_SCALE (0.1 m, mm/s ...),
    each the difference from the previous non-empty value; null stays null."""
    out = {}
    for k, sc in PS_SCALE.items():
        a = stream.get(k)
        if not a or all(v is None for v in a):
            continue
        prev, row = 0, []
        for v in a:
            if v is None:
                row.append(None)
                continue
            q = int(round(v * sc))
            row.append(q - prev)
            prev = q
        out[k] = row
    return out


def athlete_data(a, data_dir, today, ps_weeks=0):
    prog = a["program"] if isinstance(a["program"], dict) else load_program(a["program"])
    folder = Path(data_dir) / a["id"]
    runs = _read(folder / "runs.json", [])
    well = _read(folder / "wellness.json", {})
    streams = {}
    for r in runs:
        s = _read(folder / "streams" / ("%s.json" % r["id"]), None)
        if s:
            streams[r["id"]] = s

    weeks = m.weekly(runs, prog, today)
    if not runs:  # no sync yet: show targets only, not a row of zeros
        for w in weeks:
            w["km"] = None
    run_date = {r["id"]: r["date"] for r in runs}
    for w in weeks:
        dd = m.decoupling_detail(streams[w["lr_id"]]) if w["lr_id"] in streams else None
        w["dec"] = dd and dd["pct"]
        # rated only for steady long runs >= 20 km (not race weeks), docs §6
        w["decd"] = dd and {"date": run_date.get(w["lr_id"]), "km": w["lr"], "h": dd["h"], "full": dd["full"], "hf": dd["hf"],
                            "rated": bool(w["lr"] and w["lr"] >= 20 and not w["event"])}
    weight_t = {x["ms"]: x["kg"] for x in prog["weight"]}
    for w in weeks:
        kgs = [well[k]["weight"] for k in well
               if well[k].get("weight") and w["start"] <= k <= w["end"]]
        w["kg"] = round(sum(kgs) / len(kgs), 2) if kgs else None
        w["kg_t"] = weight_t.get(w["ms"])

    eff = m.efforts(runs, streams, a.get("effort"), m.test_days(prog["events"]))
    pb = m.pb_progress(eff)
    est_series = m.estimate_series(eff, m.d(prog["ms1"]), today)
    est_now, est_src = m.marathon_estimate(eff, today)

    days = [today - dt.timedelta(days=i) for i in range(DAYS - 1, -1, -1)]
    lights = {}
    for i in range(DAYS + 2, -1, -1):
        day = today - dt.timedelta(days=i)
        lights[day.isoformat()] = m.light(well, day, a.get("rhr"))
    latest = next((day for day in sorted(well, reverse=True) if day <= today.isoformat()), None)

    in_program = [r for r in runs if r["date"] >= prog["ms1"]]
    sessions = [_session(r, streams.get(r["id"]), _read(folder / "laps" / ("%s.json" % r["id"]), None), (a.get("coach") or {}).get("walk_mps"), a.get("coach"))
                for r in in_program]
    ps_from = (today - dt.timedelta(weeks=ps_weeks)).isoformat()   # per-second data only for the last weeks (file size)
    for s, r in zip(sessions, in_program):
        if ps_weeks and r["date"] >= ps_from and r["id"] in streams:
            s["ps"] = per_second(streams[r["id"]])
    done = [w for w in weeks if w["done"]]
    last_done = done[-1] if done else None
    return {
        "id": a["id"], "name": a["name"],
        "program": prog, "weight_floor": a.get("weight_floor"), "lthr": a.get("lthr"), "zones": a.get("zones"), "cadence": a.get("cadence"),
        "pace": _pace(a.get("pace")), "coach": a.get("coach") or None,
        "has_data": bool(runs or well),
        "longest": max([r["km"] for r in in_program] or [0]),
        "weeks": weeks,
        "est": {"sec": est_now, "from": est_src, "series": est_series},
        "pb": {k: v for k, v in pb.items()},
        # every run's fastest segment per distance (date, seconds): all points on the best-progress charts
        "eff": {k: [[d, sec, 1] if est else [d, sec] for d, sec, _, est in rows] for k, rows in eff.items()},
        "days": [{
            "date": day.isoformat(),
            "sleep_h": round(well.get(day.isoformat(), {}).get("sleep_s", 0) / 3600, 2) or None,
            "hrv": well.get(day.isoformat(), {}).get("hrv"),
            "bb": well.get(day.isoformat(), {}).get("bb"),
            "rhr": m.rhr(well.get(day.isoformat())),
            "hrv_status": well.get(day.isoformat(), {}).get("hrv_status"),
            # Garmin's 7-day average and personal normal range (docs §7b: the status reads the average, not the night)
            "hrv_week": well.get(day.isoformat(), {}).get("hrv_week"),
            "hrv_low": well.get(day.isoformat(), {}).get("hrv_low"), "hrv_hi": well.get(day.isoformat(), {}).get("hrv_hi"),
            "level": (lights.get(day.isoformat()) or {}).get("level"),
        } for day in days],
        # §7: the long-run gate is judged on the long run's own morning; other days only say which day that is
        "today": dict({"date": latest, "light": lights.get(latest) if latest else None}, **_lr_today(prog, today, latest, well, lights)),
        "badges": m.badges(runs, weeks, eff, prog["ms1"]),
        "week_stats": m.week_stats(last_done, well, lights, prog["sleep"].get("min")) if last_done and runs else None,
        "last_done_ms": last_done["ms"] if last_done else None,
        "sync": _read(folder / "state.json", {}).get("last_sync"),
        "run_days": _run_days(in_program),
        "sessions": sessions,
    }


def _lr_today(prog, today, latest, well, lights):
    """Which weekday of this program week holds the long run, and the gate when that day is today (docs §7, §7b)."""
    ms = m.ms_of(today.isoformat(), prog["ms1"])
    wk = next((w for w in prog["weeks"] if w["ms"] == ms), None)
    days = (wk or {}).get("days") or []
    lr = next((i for i, c in enumerate(days) if "LONG RUN" in str(c).strip().split("\n")[0].upper()), None) if len(days) == 7 else None   # title line only
    is_today = lr is not None and lr == today.weekday()
    gate = None
    if is_today and latest == today.isoformat():
        gate = m.long_run_gate(well.get(latest), (lights.get(latest) or {}).get("level"))
    return {"lr_day": lr, "lr_today": is_today, "saturday": gate}


LAP_TRIG = {"distance": "a", "manual": "m", "session_end": "e", "time": "t", "position": "p"}


def _session(r, stream, laps=None, walk=None, coach=None):
    """One run for the Sesi tab: totals, the watch's laps (from its FIT file), per-km splits and (for runs of
    10 km or more) decoupling. "g" holds the run summary exactly as Garmin reports it."""
    s = {"id": r["id"], "date": r["date"], "time": (r.get("start") or "")[11:16], "km": round(r["km"], 2),
         "sec": round(r["sec"]), "hr": r.get("avg_hr"), "splits": [], "dec": None, "dec_full": None,
         "g": r.get("g") or {}, "name": r.get("name"),
         # [km, seconds (timer), mean HR, mean cadence, trigger a=auto-lap distance m=manual e=end t=time p=position w=other,
         #  walking seconds (added below when there is per-second data)]
         "laps": [[l["km"], l["sec"], l.get("hr"), l.get("cad"), LAP_TRIG.get(l.get("trigger"), "w")]
                  for l in (laps or {}).get("laps", []) if l.get("km") is not None and l.get("sec")]}
    if stream:
        s["splits"] = m.per_km(stream, walk)      # [km, s, HR, cadence (running only with walk), elevation, walking s]
        if walk:
            s.update(m.run_walk(stream, walk))
            if s["laps"]:                     # walking per lap: lap edges in timer time = running sums of lap times
                edges = [0.0]
                for l in s["laps"]:
                    edges.append(edges[-1] + l[1])
                for l, w in zip(s["laps"], m.walk_in(stream, walk, edges)):
                    l.append(w)
        C = coach or {}
        st = m.strides(stream, C.get("stride_mps", 2.6), C.get("stride_min_s", 6))
        if st:
            s["strides"] = st                 # [[start km, seconds, peak m/s]] from the watch's speed (docs §5)
        tc = [v for v in (stream.get("tc") or []) if v is not None]
        if tc:
            s["tc"] = [min(tc), max(tc)]      # temperature range on the watch, °C
        if r["km"] >= m.LONG_RUN_MIN_KM:
            dd = m.decoupling_detail(stream)
            if dd:
                s["dec"], s["dec_full"] = dd["pct"], dd["full"]
    return s


def _run_days(runs):
    """{date: km run that day} for the overlay's per-day ticks."""
    out = {}
    for r in runs:
        out[r["date"]] = round(out.get(r["date"], 0) + r["km"], 1)
    return out


def _pace(p):
    """Profile pace ranges "m:ss" -> seconds per km; other keys (flags) pass through."""
    if not p:
        return None
    sec = lambda v: int(v.split(":")[0]) * 60 + int(v.split(":")[1])
    return {k: [sec(x) for x in v] if isinstance(v, list) else v for k, v in p.items()}


def build(cfg, athletes, today, out_path):
    # coach thresholds: config "coach", overridable per athlete
    athletes = [dict(a, coach={**cfg.get("coach", {}), **a.get("coach", {})}, effort=cfg.get("effort")) for a in athletes]
    ovr = overrides.load(cfg.get("overrides"))
    if ovr:
        print("[i] %s: %d sesi diatur manual" % (cfg.get("overrides"), sum(len(v) for v in ovr.values())))
    data = [athlete_data(a, cfg["data_dir"], today, cfg.get("per_detik_minggu", 10)) for a in athletes]
    p0 = data[0]["program"]
    ms_cur = m.ms_of(today.isoformat(), p0["ms1"])
    phases = []
    for w in p0["weeks"]:
        if phases and phases[-1]["name"] == w["phase"]:
            phases[-1]["b"] = w["ms"]
        else:
            phases.append({"name": w["phase"], "a": w["ms"], "b": w["ms"]})
    first_ms = p0["weeks"][0]["ms"]
    if first_ms > 1:
        phases.insert(0, {"name": "Awal", "a": 1, "b": first_ms - 1})
    score = None
    if len(data) >= 2 and data[0]["week_stats"] and data[1]["week_stats"]:
        score = m.score(data[0]["week_stats"], data[1]["week_stats"])
        score["ms"] = data[0]["last_done_ms"]

    payload = {
        "generated": dt.datetime.now().isoformat(timespec="minutes"),
        "today": today.isoformat(),
        "ps_weeks": cfg.get("per_detik_minggu", 10),
        "race_date": p0["race_date"],
        "ms1": p0["ms1"],
        "ms_cur": ms_cur,
        "total_weeks": p0["total_weeks"],
        "phase": next((ph["name"] for ph in phases if ph["a"] <= ms_cur <= ph["b"]), None),
        "phases": phases,
        "events": [e for e in p0["events"] if e["date"] >= today.isoformat()][:3],
        "all_events": p0["events"],
        "score": score,
        "athletes": [_slim(x, COLORS[i], ovr) for i, x in enumerate(data)],
    }
    html = (WEB / "template.html").read_text(encoding="utf-8")
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/null", blob)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def _slim(x, color, ovr=None):
    prog = x["program"]
    tgt = prog["target"].get("B") or {}
    return {
        "id": x["id"], "name": x["name"], "c": color, "has_data": x["has_data"],
        "longest": round(x["longest"], 1),
        "target": tgt, "targets": prog["target"], "weight_floor": x.get("weight_floor"), "lthr": x.get("lthr"), "ovr": (ovr or {}).get(x["id"].upper(), {}), "zones": x.get("zones"), "cadence": x.get("cadence"), "pace": x.get("pace"), "coach": x.get("coach"), "sleep_min": prog["sleep"].get("min"),
        "weeks": [{k: w[k] for k in ("ms", "start", "km", "km_t", "lr", "lr_t", "dec", "decd", "kg", "kg_t", "done", "down", "event")}
                  for w in x["weeks"]],
        "est": x["est"], "pb": x["pb"], "eff": x["eff"], "days": x["days"], "today": x["today"],
        "badges": x["badges"], "week_stats": x["week_stats"], "sync": x["sync"],
        # full program for the track and the weekly schedule overlay
        "plan": [{k: w.get(k) for k in ("ms", "start", "phase", "km", "lr", "down", "event", "notes", "days")}
                 for w in prog["weeks"]],
        "run_days": x["run_days"], "sessions": x["sessions"],
    }
