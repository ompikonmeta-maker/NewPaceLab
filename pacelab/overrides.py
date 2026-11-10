"""overrides.json (docs/RUMUS-BATAS-SUMBER.md §1 "Tukar sesi"): a session moved or changed by hand.

    [{"date": "2026-11-01", "athlete": "TAOFIK", "session": "long_run", "km": 22, "note": "dipindah dari Sabtu"}]

The dashboard judges that day's run against this plan instead of the Excel cell; the day's export (.md) shows it
too, so Claude project reads the same plan. session: long_run, easy, recovery, tempo, interval, race, rest.
Optional: "tempo_km" (tempo / interval length), "note".
"""
import json
from pathlib import Path

TITLES = {"long_run": "LONG RUN", "easy": "Lari santai", "recovery": "Lari pemulihan", "tempo": "LATIHAN KERAS: Tempo",
          "interval": "LATIHAN KERAS: Interval", "race": "LOMBA", "rest": "ISTIRAHAT PENUH"}


def cell(e):
    """The entry written like a Kalender cell, so the dashboard reads it with the same parser."""
    s, km = e.get("session"), e.get("km")
    title = TITLES[s]
    if s in ("tempo", "interval"):
        lines = [title + (" %s km" % _n(e["tempo_km"]) if e.get("tempo_km") else "")]
        if km:
            lines.append("Total %s km" % _n(km))
    else:
        lines = [title + (" %s km" % _n(km) if km and s != "rest" else "")]
    lines.append("(overrides.json%s)" % (": " + str(e["note"]) if e.get("note") else ""))
    return "\n".join(lines)


def _n(v):
    return ("%g" % float(v)).replace(".", ",")


def load(path, log=print):
    """{athlete id: {date: cell text}}; a missing file is fine, bad entries are skipped with a message."""
    if not path or not Path(path).is_file():
        return {}
    try:
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        log("[!] %s tidak terbaca: %s" % (path, e))
        return {}
    out = {}
    for i, e in enumerate(rows if isinstance(rows, list) else []):
        if not isinstance(e, dict) or not e.get("date") or not e.get("athlete") or e.get("session") not in TITLES:
            log("[!] %s entri %d dilewati: perlu date, athlete, session (%s)" % (path, i + 1, ", ".join(TITLES)))
            continue
        out.setdefault(str(e["athlete"]).upper(), {})[str(e["date"])[:10]] = cell(e)
    return out
