"""`pacelab.py ekspor <tanggal>`: one day's runs packed for a deep analysis in Claude chat.

ekspor/NewPaceLab_<tanggal>.zip
  ringkasan.md          program, plan cell, profile, morning, Garmin summary, laps, per km, zones, week
  <nama>_per_detik.csv  per-second data (time, distance, HR, speed, pace, cadence, elevation), no GPS
  <nama>_lap.csv        the watch's laps
  <nama>_asli.fit       the watch's original file (has GPS), unless --tanpa-fit

The coach checks are only in the dashboard's "Simpan untuk Claude" file (they are computed there).
"""
import csv
import datetime as dt
import io
import json
import zipfile
from pathlib import Path

from . import fit, metrics as m
from .sync import FIT_DOWNLOAD, GARMIN_FIELDS

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
TRIG = {"distance": "auto", "manual": "manual", "session_end": "akhir", "time": "waktu", "position": "posisi"}
LABEL = {"moving_s": "Waktu bergerak", "elapsed_s": "Waktu total", "hr_max": "HR maks", "cad": "Cadence rata", "cad_max": "Cadence maks",
         "speed": "Kecepatan rata (m/s)", "speed_max": "Kecepatan maks (m/s)", "gain_m": "Elevasi naik (m)", "loss_m": "Elevasi turun (m)",
         "stride_cm": "Panjang langkah (cm)", "gct_ms": "Kontak tanah (ms)", "vo_cm": "Osilasi vertikal (cm)", "vr_pct": "Rasio vertikal (%)",
         "power": "Power rata (W)", "power_max": "Power maks (W)", "power_norm": "Power ternormalisasi (W)", "te_aer": "Efek latihan aerobik",
         "te_ana": "Efek latihan anaerobik", "te_label": "Label efek latihan", "load": "Beban latihan", "lt_bpm": "Ambang laktat (bpm)",
         "kcal": "Kalori", "steps": "Langkah", "temp_min": "Suhu min (°C)", "temp_max": "Suhu maks (°C)", "laps": "Jumlah lap",
         "pr": "Rekor pribadi", "water_ml": "Perkiraan keringat (ml)"}


def _read(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def hms(s):
    s = int(round(s or 0))
    return "%d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60) if s >= 3600 else "%d:%02d" % (s // 60, s % 60)


def pace(sec_per_km):
    if not sec_per_km:
        return "–"
    s = int(round(sec_per_km))
    return "%d:%02d" % (s // 60, s % 60)


def num(v, nd=1):
    return ("%.*f" % (nd, v)).replace(".", ",")


def tgl(d):
    return "%s %d %s %d" % (DAYS[d.weekday()], d.day, MONTHS[d.month - 1], d.year)


def table(head, rows):
    if not rows:
        return []
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    return out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]


def per_second_csv(stream):
    """CSV text: detik, jarak_m, hr_bpm, kecepatan_m_s, pace_per_km, cadence_spm, elevasi_m (speed over +-2 samples)."""
    t, d = stream.get("t") or [], stream.get("d") or []
    hr, cad, el = stream.get("hr") or [], stream.get("cad") or [], stream.get("el") or []
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["detik", "jarak_m", "hr_bpm", "kecepatan_m_s", "pace_per_km", "cadence_spm", "elevasi_m"])
    for i in range(len(t)):
        a, b = max(0, i - 2), min(len(t) - 1, i + 2)
        v = (d[b] - d[a]) / (t[b] - t[a]) if t[b] > t[a] else None
        w.writerow([t[i], d[i], hr[i] if i < len(hr) else "", round(v, 3) if v else "",
                    pace(1000 / v) if v and v > .5 else "", cad[i] if i < len(cad) and cad[i] else "",
                    el[i] if i < len(el) and el[i] is not None else ""])
    return buf.getvalue()


def lap_csv(laps):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["lap", "jarak_km", "waktu_s", "pace_per_km", "hr_rata", "hr_maks", "cadence_spm", "asal"])
    for i, l in enumerate(laps, 1):
        w.writerow([i, l.get("km"), l.get("sec"), pace(l["sec"] / l["km"]) if l.get("km") and l.get("sec") else "",
                    l.get("hr") or "", l.get("hr_max") or "", l.get("cad") or "", TRIG.get(l.get("trigger"), l.get("trigger") or "")])
    return buf.getvalue()


def _week(prog, day):
    ms1 = m.d(prog["ms1"])
    ms = (day - ms1).days // 7 + 1
    return ms, next((w for w in prog.get("weeks", []) if w.get("ms") == ms), {})


def summary(day, people, prog):
    """The Markdown summary. people: [{"a": athlete cfg, "runs": [(run, stream, laps)], "well": {...}, "week": [runs]}]."""
    ms, wk = _week(prog, day) if prog else (None, {})
    L = ["# Sesi lari — %s%s" % (tgl(day), " (MS%d · %s)" % (ms, wk.get("phase")) if ms and wk.get("phase") else ""), "",
         "> Tolong analisa sesi ini secara mendalam sebagai pelatih maraton: apakah sesuai rencana, apa yang bagus,",
         "> apa yang perlu diperbaiki, dan saran untuk sesi berikutnya. Data di bawah apa adanya dari Garmin + program Excel.",
         "> File CSV per detik dan lap (dan file FIT asli bila ada) ada di zip yang sama.", ""]
    if prog:
        race = m.d(prog["race_date"])
        L += ["## Konteks program", "- Maraton: %s (%d hari setelah sesi ini)" % (tgl(race), (race - day).days)]
        if ms:
            L.append("- Minggu program: MS%d%s%s%s" % (ms, ", fase %s" % wk["phase"] if wk.get("phase") else "",
                                                      " · minggu ringan" if wk.get("down") else "", " · minggu lomba/tes" if wk.get("event") else ""))
        evs = [e for e in prog.get("events", []) if e["date"] >= day.isoformat()][:3]
        if evs:
            L.append("- Tes/lomba berikutnya: " + ", ".join("%s (%s)" % (e["event"], e["date"]) for e in evs))
    for p in people:
        a = p["a"]
        L += ["", "## %s" % a["name"], "", "### Rencana hari ini (sel Excel, apa adanya)"]
        cell = (wk.get("days") or [""] * 7)[day.weekday()] if wk.get("days") else ""
        L += ["> " + x.strip() for x in cell.split("\n") if x.strip()] or ["> (tidak ada rencana di Excel untuk tanggal ini)"]
        z, pc = a.get("zones") or [], a.get("pace") or {}
        L += ["", "### Profil (config.json)"]
        if len(z) > 3:
            L.append("- Zona HR: Z1 < %d · Z2 %d–%d · Z3 %d–%d · Z4 %d–%d · Z5 ≥ %d" % (z[0], z[0], z[1] - 1, z[1], z[2] - 1, z[2], z[3] - 1, z[3]))
        if pc:
            names = {"rec": "recovery", "easy": "easy/long", "mp": "MP", "tempo": "tempo", "interval": "interval"}
            L.append("- Pace: " + " · ".join("%s %s–%s" % (names.get(k, k), v[0], v[1]) for k, v in pc.items() if isinstance(v, list))
                     + (" · HR jadi patokan" if pc.get("hr_leads") else ""))
        if a.get("cadence"):
            L.append("- Target cadence: %d–%d spm" % tuple(a["cadence"]))
        w = p["well"]
        L += ["", "### Kondisi pagi", ("- Tidur %s j · HRV %s ms%s · Body Battery %s · RHR %s" % (
            num(w["sleep_s"] / 3600) if w.get("sleep_s") else "–", w.get("hrv", "–"), " (%s)" % w["hrv_status"] if w.get("hrv_status") else "",
            w.get("bb", "–"), m.rhr(w) or "–")) if w else "- (tidak ada data pagi itu)"]
        if not p["runs"]:
            L += ["", "### Lari", "- Tidak ada lari tercatat di Garmin pada tanggal ini."]
        for n, (r, stream, laps) in enumerate(p["runs"], 1):
            g = r.get("g") or {}
            L += ["", "### Lari%s%s" % (" %d" % n if len(p["runs"]) > 1 else "", " · mulai %s" % (r.get("start") or "")[11:16] if r.get("start") else ""),
                  "", "**Ringkasan Garmin (apa adanya)**", ""]
            L += table(["Jarak", "Waktu", "Pace", "HR rata / maks", "Cadence"],
                       [["%s km" % num(r["km"], 2), hms(r["sec"]), pace(r["sec"] / r["km"]) + "/km" if r["km"] else "–",
                         "%s / %s" % (r.get("avg_hr") or "–", g.get("hr_max", "–")), "%s spm" % round(g["cad"]) if g.get("cad") else "–"]])
            more = ["%s %s" % (LABEL.get(k, k), hms(g[k]) if k.endswith("_s") else num(g[k]) if isinstance(g[k], float) else g[k])
                    for k, _ in GARMIN_FIELDS if k in g and k not in ("hr_max", "cad")]
            if more:
                L += ["", "Lainnya: " + " · ".join(more)]
            if laps:
                L += ["", "**Lap jam (file FIT, apa adanya)**", ""]
                L += table(["Lap", "Jarak", "Waktu", "Pace", "HR", "Cadence", "Asal"],
                           [[i, "%s km" % num(l["km"], 2) if l["km"] >= 1 else "%d m" % round(l["km"] * 1000), hms(l["sec"]), pace(l["sec"] / l["km"]),
                             l.get("hr") or "–", l.get("cad") or "–", TRIG.get(l.get("trigger"), l.get("trigger") or "")]
                            for i, l in enumerate(laps, 1) if l.get("km") and l.get("sec")])
            if stream:
                walk = (a.get("coach") or {}).get("walk_mps")
                sp = m.per_km(stream, walk)
                L += ["", "**Per km (hitungan dari data per detik)**", ""]
                L += table(["Km", "Jarak", "Waktu", "Pace", "HR", "Cadence lari" if walk else "Cadence", "Jalan kaki", "Elevasi akhir km"],
                           [[i, "%s km" % num(s[0], 2), hms(s[1]), pace(s[1] / s[0]), s[2] or "–", s[3] or "–", hms(s[5]) if s[5] else "–",
                             "%s m" % s[4] if s[4] is not None else "–"] for i, s in enumerate(sp, 1)])
                if walk:
                    rw = m.run_walk(stream, walk)
                    L += ["", "Jalan kaki (kecepatan ≤ %s m/s): %s · cadence saat lari %s spm" % (num(walk), hms(rw["walk_s"]), round(rw["cad_run"]) if rw["cad_run"] else "–")]
                if len(z) > 3:
                    zt, tt = [0] * 5, 0
                    for s in sp:
                        if s[2]:
                            zt[sum(1 for b in z if s[2] >= b)] += s[1]
                            tt += s[1]
                    if tt:
                        L += ["", "Waktu di zona HR (per km): " + " · ".join("Z%d %d%%" % (i + 1, round(v / tt * 100)) for i, v in enumerate(zt) if v)]
                dd = m.decoupling_detail(stream) if r["km"] >= m.LONG_RUN_MIN_KM else None
                if dd:
                    L.append("Decoupling (dokumen §6): %s%% tanpa 3 km pertama%s" % (num(dd["pct"]), " · %s%% data penuh" % num(dd["full"]) if dd.get("full") is not None else ""))
        if p["week"] and ms:
            st = m.d(prog["ms1"]) + dt.timedelta(weeks=ms - 1)
            km = sum(x["km"] for x in p["week"])
            L += ["", "### Minggu MS%d (%s – %s)" % (ms, st.isoformat(), (st + dt.timedelta(days=6)).isoformat()),
                  "- Km dijalani %s%s" % (num(km), " / target %s" % wk["km"] if wk.get("km") else "")]
            L += ["- %s: %s km · %s/km · HR %s%s" % (x["date"], num(x["km"]), pace(x["sec"] / x["km"]) if x["km"] else "–", x.get("avg_hr") or "–",
                                                    " ← sesi ini" if x["date"] == day.isoformat() else "") for x in sorted(p["week"], key=lambda q: q["date"])]
    L += ["", "---", "Dibuat oleh NewPaceLab `pacelab.py ekspor` %s. Penilaian pelatih dashboard ada di file dari tombol "
          "\"Simpan untuk Claude\" di dashboard." % dt.datetime.now().isoformat(timespec="minutes")]
    return "\n".join(L) + "\n"


def export_day(cfg, athletes, day, prog=None, client_for=None, with_fit=True, out_dir="ekspor", log=print):
    """Write ekspor/NewPaceLab_<day>.zip and return its path. client_for(athlete) -> Garmin client or None."""
    people, files = [], {}
    for a in athletes:
        folder = Path(cfg["data_dir"]) / a["id"]
        runs = [r for r in _read(folder / "runs.json", []) if r.get("date") == day.isoformat()]
        well = _read(folder / "wellness.json", {}).get(day.isoformat(), {})
        if prog:
            ms = (day - m.d(prog["ms1"])).days // 7
            st = m.d(prog["ms1"]) + dt.timedelta(weeks=ms)
            week = [r for r in _read(folder / "runs.json", []) if st.isoformat() <= r.get("date", "") <= (st + dt.timedelta(days=6)).isoformat()]
        else:
            week = []
        tag = a["name"].lower()
        rows = []
        c = client_for(a) if (client_for and with_fit and runs) else None
        for n, r in enumerate(sorted(runs, key=lambda q: q.get("start") or ""), 1):
            suffix = "" if len(runs) == 1 else "_%d" % n
            stream = _read(folder / "streams" / ("%s.json" % r["id"]), None)
            laps = (_read(folder / "laps" / ("%s.json" % r["id"]), {}) or {}).get("laps") or []
            if c:
                try:
                    blob = c.get(FIT_DOWNLOAD % r["id"], raw=True)
                    raw = fit.unwrap(blob) if blob else None
                    if raw:
                        files["%s%s_asli.fit" % (tag, suffix)] = raw
                        got = fit.read(raw)
                        laps = got["laps"] or laps
                        stream = got["stream"] or stream
                except Exception as e:  # noqa: BLE001 - the export still works from the local copy
                    log("  [!] %s: file FIT tidak terunduh (%s); pakai data lokal" % (a["name"], type(e).__name__))
            if stream:
                files["%s%s_per_detik.csv" % (tag, suffix)] = per_second_csv(stream).encode("utf-8")
            if laps:
                files["%s%s_lap.csv" % (tag, suffix)] = lap_csv(laps).encode("utf-8")
            rows.append((r, stream, laps))
        people.append({"a": a, "runs": rows, "well": well, "week": week})
    files["ringkasan.md"] = summary(day, people, prog).encode("utf-8")
    out = Path(out_dir) / ("NewPaceLab_%s.zip" % day.isoformat())
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out
