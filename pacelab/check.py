"""Summarise what sync managed to read — counts and field names only, no values."""
import json
from pathlib import Path

FIELDS = ("sleep_s", "sleep_score", "hrv", "hrv_status", "bb", "rhr", "rhr_sleep", "weight")


def report(folder, name):
    folder = Path(folder)
    lines = ["== %s" % name]
    try:
        runs = json.loads((folder / "runs.json").read_text())
        well = json.loads((folder / "wellness.json").read_text())
    except (OSError, ValueError):
        return "\n".join(lines + ["  belum ada data: jalankan `python pacelab.py sync` dulu"])
    streams = list((folder / "streams").glob("*.json"))
    keys, with_hr = set(), 0
    for p in streams:
        s = json.loads(p.read_text())
        keys.update(s.get("keys", []))
        with_hr += any(s.get("hr") or [])
    types = sorted({r.get("type") or "?" for r in runs})
    lines.append("  lari          : %d (tipe: %s)" % (len(runs), ", ".join(types)))
    lines.append("  stream        : %d/%d lari, %d dengan HR" % (len(streams), len(runs), with_hr))
    lines.append("  stream keys   : %s" % (", ".join(sorted(keys)) or "-"))
    have = {p.stem for p in streams}
    try:
        no = set(json.loads((folder / "state.json").read_text()).get("no_stream") or [])
    except (OSError, ValueError):
        no = set()
    miss = [r for r in runs if str(r.get("id")) not in have]
    if miss:
        lines.append("  tanpa data per detik (%d):" % len(miss))
        for r in sorted(miss, key=lambda r: r.get("date") or ""):
            lines.append("    %s  %6.2f km  %-16s %s" % (r.get("date"), r.get("km") or 0, r.get("type") or "?",
                                                        "Garmin: tidak ada detail" if r.get("id") in no else "belum diminta"))
    lines.append("  wellness hari : %d (%s .. %s)" % (len(well), min(well, default="-"), max(well, default="-")))
    last30 = sorted(well)[-30:]
    lines.append("    %-12s %9s %14s" % ("", "semua", "30 hr terakhir"))
    for f in FIELDS:
        n = sum(1 for v in well.values() if v.get(f) is not None)
        n30 = sum(1 for k in last30 if well[k].get(f) is not None)
        lines.append("    %-12s %4d hari %9d hari%s" % (f, n, n30, "   <-- tidak terbaca" if n == 0 and f != "rhr_sleep" else ""))
    st = sorted({v.get("hrv_status") for v in well.values() if v.get("hrv_status")})
    lines.append("  status HRV    : %s" % (", ".join(st) or "-"))
    return "\n".join(lines)
