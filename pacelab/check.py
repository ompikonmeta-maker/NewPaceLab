"""Summarise what sync managed to read — counts and field names only, no values."""
import json
from pathlib import Path

FIELDS = ("sleep_s", "sleep_score", "hrv", "hrv_status", "bb", "rhr", "weight")


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
    lines.append("  wellness hari : %d (%s .. %s)" % (len(well), min(well, default="-"), max(well, default="-")))
    for f in FIELDS:
        n = sum(1 for v in well.values() if v.get(f) is not None)
        lines.append("    %-12s %4d hari%s" % (f, n, "   <-- tidak terbaca" if n == 0 else ""))
    st = sorted({v.get("hrv_status") for v in well.values() if v.get("hrv_status")})
    lines.append("  status HRV    : %s" % (", ".join(st) or "-"))
    return "\n".join(lines)
