"""Turn synced data + program workbooks into one offline dashboard.html."""
import datetime as dt
import json
from pathlib import Path

from . import metrics as m
from .program import load_program

WEB = Path(__file__).parent / "web"
DAYS = 60  # daily history shipped to the page (period filter: 7 / 14 / 30 / 60 days)
COLORS = ["t", "r"]  # CSS series slots: first athlete blue, second orange


def _read(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def athlete_data(a, data_dir, today):
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
    for w in weeks:
        w["dec"] = m.decoupling(streams[w["lr_id"]]) if w["lr_id"] in streams else None
    weight_t = {x["ms"]: x["kg"] for x in prog["weight"]}
    for w in weeks:
        kgs = [well[k]["weight"] for k in well
               if well[k].get("weight") and w["start"] <= k <= w["end"]]
        w["kg"] = round(sum(kgs) / len(kgs), 2) if kgs else None
        w["kg_t"] = weight_t.get(w["ms"])

    eff = m.efforts(runs, streams)
    pb = m.pb_progress(eff)
    est_series = m.estimate_series(eff, m.d(prog["ms1"]), today)
    est_now, est_src = m.marathon_estimate(eff, today)

    days = [today - dt.timedelta(days=i) for i in range(DAYS - 1, -1, -1)]
    lights = {}
    for i in range(DAYS + 2, -1, -1):
        day = today - dt.timedelta(days=i)
        lights[day.isoformat()] = m.light(well, day)
    latest = next((day for day in sorted(well, reverse=True) if day <= today.isoformat()), None)

    in_program = [r for r in runs if r["date"] >= prog["ms1"]]
    done = [w for w in weeks if w["done"]]
    last_done = done[-1] if done else None
    return {
        "id": a["id"], "name": a["name"],
        "program": prog,
        "has_data": bool(runs or well),
        "longest": max([r["km"] for r in in_program] or [0]),
        "weeks": weeks,
        "est": {"sec": est_now, "from": est_src, "series": est_series},
        "pb": {k: v for k, v in pb.items()},
        "days": [{
            "date": day.isoformat(),
            "sleep_h": round(well.get(day.isoformat(), {}).get("sleep_s", 0) / 3600, 2) or None,
            "hrv": well.get(day.isoformat(), {}).get("hrv"),
            "bb": well.get(day.isoformat(), {}).get("bb"),
            "rhr": m.rhr(well.get(day.isoformat())),
            "hrv_status": well.get(day.isoformat(), {}).get("hrv_status"),
            "level": (lights.get(day.isoformat()) or {}).get("level"),
        } for day in days],
        "today": {"date": latest, "light": lights.get(latest) if latest else None,
                  "saturday": m.saturday_rule(well.get(latest)) if latest else None},
        "badges": m.badges(runs, weeks, eff, prog["ms1"]),
        "week_stats": m.week_stats(last_done, well, lights, prog["sleep"].get("min")) if last_done and runs else None,
        "last_done_ms": last_done["ms"] if last_done else None,
        "sync": _read(folder / "state.json", {}).get("last_sync"),
        "run_days": _run_days(in_program),
    }


def _run_days(runs):
    """{date: km run that day} for the overlay's per-day ticks."""
    out = {}
    for r in runs:
        out[r["date"]] = round(out.get(r["date"], 0) + r["km"], 1)
    return out


def build(cfg, athletes, today, out_path):
    data = [athlete_data(a, cfg["data_dir"], today) for a in athletes]
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
        "race_date": p0["race_date"],
        "ms1": p0["ms1"],
        "ms_cur": ms_cur,
        "total_weeks": p0["total_weeks"],
        "phase": next((ph["name"] for ph in phases if ph["a"] <= ms_cur <= ph["b"]), None),
        "phases": phases,
        "events": [e for e in p0["events"] if e["date"] >= today.isoformat()][:3],
        "all_events": p0["events"],
        "score": score,
        "athletes": [_slim(x, COLORS[i]) for i, x in enumerate(data)],
    }
    html = (WEB / "template.html").read_text(encoding="utf-8")
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/null", blob)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def _slim(x, color):
    prog = x["program"]
    tgt = prog["target"].get("B") or {}
    return {
        "id": x["id"], "name": x["name"], "c": color, "has_data": x["has_data"],
        "longest": round(x["longest"], 1),
        "target": tgt, "sleep_min": prog["sleep"].get("min"),
        "weeks": [{k: w[k] for k in ("ms", "start", "km", "km_t", "lr", "lr_t", "dec", "kg", "kg_t", "done", "down", "event")}
                  for w in x["weeks"]],
        "est": x["est"], "pb": x["pb"], "days": x["days"], "today": x["today"],
        "badges": x["badges"], "week_stats": x["week_stats"], "sync": x["sync"],
        # full program for the track and the weekly schedule overlay
        "plan": [{k: w.get(k) for k in ("ms", "start", "phase", "km", "lr", "down", "event", "notes", "days")}
                 for w in prog["weeks"]],
        "run_days": x["run_days"],
    }
