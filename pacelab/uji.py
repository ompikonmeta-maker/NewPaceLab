"""`pacelab.py uji`: the real-data acceptance checks of RENCANA 23 (omPik 15 Nov), printed as LULUS / GAGAL with the
numbers found. Reads data/ (and ekspor/*.zip or Garmin for the original FIT); prints counts and averages only.

  4a  watch speed: details directSpeed and the stored stream vs the FIT file's enhanced_speed, Taofik 10 Nov
  4b  strides Taofik 10 Nov: 6 strides, 16-23 s, peak pace 4:40-5:49
  4c  decoupling 1 Nov: Reza (start 05:56) 2,8 / 4,3 %, Taofik 4,9 / 8,4 % (+-0,3)
  4d  long run 15 Nov: walking (< walk_mps) > dec_walk_frac of the moving time -> "tidak berlaku (banyak jalan kaki)"
  4e  lari bareng 15 Nov: Reza flagged (HR over his upper limit in > pair_hr_frac of the km), Taofik not
  4f  gate 15 Nov: Reza red light (HRV LOW) -> limit red_easy_km, 16 km -> "Gerbang dilewati (+8 km)"
"""
import datetime as dt
import json
import re
import zipfile
from pathlib import Path

from . import fit, metrics as m, overrides
from .program import load_program
from .sync import ACT_DETAILS, FIT_DOWNLOAD, norm_stream

RES = []


def _read(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def ok(name, passed, got, want):
    RES.append(passed)
    print("  [%s] %s\n        hasil : %s\n        harus : %s" % ("LULUS" if passed else "GAGAL" if passed is not None else "  -  ", name, got, want))


def hms(sec):
    s = int(round(sec))
    return "%d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60) if s >= 3600 else "%d:%02d" % (s // 60, s % 60)


def mmss(sec):
    s = int(round(sec))
    return "%d:%02d" % (s // 60, s % 60)


def num(v, nd=1):
    return ("%.*f" % (nd, v)).replace(".", ",")


def _ath(cfg, aid):
    return next(a for a in cfg["athletes"] if a["id"] == aid)


def _runs(cfg, aid):
    return _read(Path(cfg["data_dir"]) / aid / "runs.json", [])


def _stream(cfg, aid, rid):
    return _read(Path(cfg["data_dir"]) / aid / "streams" / ("%s.json" % rid), None)


def _run(cfg, aid, rid=None, date=None, start=None):
    rs = _runs(cfg, aid)
    if rid:
        return next((r for r in rs if str(r["id"]) == str(rid)), None)
    rs = [r for r in rs if r.get("date") == date and (not start or (r.get("start") or "")[11:16] == start)]
    return max(rs, key=lambda r: r["km"]) if rs else None


def _fit_blob(cfg, a, rid, day, client_for):
    """The original FIT: from ekspor/NewPaceLab_<day>.zip if there, else downloaded."""
    z = Path(cfg.get("export_dir", "ekspor")) / ("NewPaceLab_%s.zip" % day)
    if z.is_file():
        with zipfile.ZipFile(z) as f:
            for n in f.namelist():
                if n.lower().startswith(a["name"].lower()) and n.endswith("_asli.fit"):
                    return f.read(n), "ekspor/%s" % z.name
    c = client_for(a) if client_for else None
    if c:
        try:
            blob = c.get(FIT_DOWNLOAD % rid, raw=True)
            return fit.unwrap(blob), "unduh dari Garmin"
        except Exception as e:  # noqa: BLE001
            print("  [!] FIT tidak terunduh: %s" % type(e).__name__)
    return None, None


def _by_t(st, key):
    return {int(round(t)): v for t, v in zip(st.get("t") or [], st.get(key) or []) if v is not None}


def _diff(a, b):
    common = sorted(set(a) & set(b))
    if not common:
        return None, 0
    return sum(abs(a[k] - b[k]) for k in common) / len(common), len(common)


def u4a(cfg, client_for):
    print("\n4a. Validasi kecepatan jam, Taofik 10 Nov (id 25025503260)")
    a, rid = _ath(cfg, "TAOFIK"), "25025503260"
    blob, src = _fit_blob(cfg, a, rid, "2026-11-10", client_for)
    if not blob:
        return ok("FIT asli", None, "FIT tidak ada di ekspor/ dan tidak bisa diunduh", "jalankan Ekspor Sesi 2026-11-10 atau cek key")
    fs = (fit.read(blob) or {}).get("stream") or {}
    ref = _by_t(fs, "sp")
    print("  FIT: %s, %d detik dengan enhanced_speed" % (src, len(ref)))
    c = client_for(a) if client_for else None
    if c:
        try:
            det = c.get(ACT_DETAILS % rid, {"maxChartSize": 100000, "maxPolylineSize": 0})
            keys = sorted(d.get("key") for d in det.get("metricDescriptors") or [])
            print("  field data detail Garmin: %s" % ", ".join(keys))
            ds = norm_stream(det) or {}
            d, n = _diff(_by_t(ds, "sp"), ref)
            ok("data detail (directSpeed) vs FIT enhanced_speed", d is not None and d < 0.05,
               "selisih rata-rata %s m/s (%d detik dicocokkan)" % (num(d, 3), n) if d is not None else "directSpeed tidak ada di data detail",
               "< 0,05 m/s")
        except Exception as e:  # noqa: BLE001
            print("  [!] data detail tidak terbaca: %s" % type(e).__name__)
    st = _stream(cfg, "TAOFIK", rid) or {}
    d, n = _diff(_by_t(st, "sp"), ref)
    ok("kolom sp di streams/%s.json vs FIT enhanced_speed" % rid, d is not None and d < 0.05,
       "selisih rata-rata %s m/s (%d detik)" % (num(d, 3), n) if d is not None else "kolom sp tidak ada (data lama, perlu Update)", "< 0,05 m/s")


def u4b(cfg):
    print("\n4b. Strides Taofik 10 Nov")
    st = _stream(cfg, "TAOFIK", "25025503260")
    if not st:
        return ok("data per detik", False, "streams/25025503260.json tidak ada", "ada")
    C = cfg.get("coach", {})
    got = m.strides(st, C.get("stride_mps", 2.6), C.get("stride_min_s", 6))
    if got is None:
        return ok("strides", False, "tidak ada kecepatan jam (sp)", "6 strides")
    want = [(19, "5:49"), (16, "5:21"), (20, "4:40"), (17, "5:15"), (21, "4:47"), (23, "4:43")]
    txt = " · ".join("%ss/%s" % (q[1], mmss(1000 / q[2])) for q in got)
    near = len(got) == 6 and all(abs(q[1] - w[0]) <= 1 and abs(1000 / q[2] - (int(w[1][0]) * 60 + int(w[1][2:]))) <= 5 for q, w in zip(got, want))
    ok("jumlah, durasi, pace puncak", near, "%d strides: %s" % (len(got), txt),
       "6 strides: " + " · ".join("%ds/%s" % w for w in want) + " (toleransi 1 dtk, 5 dtk/km)")


def u4c(cfg):
    print("\n4c. Decoupling 1 Nov")
    for aid, start, want in (("REZA", "05:56", (2.8, 4.3)), ("TAOFIK", None, (4.9, 8.4))):
        r = _run(cfg, aid, date="2026-11-01", start=start)
        name = _ath(cfg, aid)["name"]
        st = r and _stream(cfg, aid, r["id"])
        dd = st and m.decoupling_detail(st)
        if not dd:
            ok(name, False, "sesi%s tidak ditemukan atau tanpa data per detik" % (" mulai " + start if start else ""), "%s / %s %%" % (num(want[0]), num(want[1])))
            continue
        good = abs(dd["pct"] - want[0]) <= 0.3 and dd.get("full") is not None and abs(dd["full"] - want[1]) <= 0.3
        ok("%s (id %s, mulai %s%s)" % (name, r["id"], (r.get("start") or "")[11:16], "" if st.get("sp") else ", perkiraan: tanpa kecepatan jam"), good,
           "%s %% tanpa 3 km · %s %% penuh" % (num(dd["pct"]), num(dd["full"]) if dd.get("full") is not None else "–"),
           "%s / %s %% (±0,3)" % (num(want[0]), num(want[1])))


def u4d(cfg):
    print("\n4d. Long run 15 Nov: decoupling tidak berlaku kalau jalan kaki > %d%% waktu bergerak" % round(cfg["coach"]["dec_walk_frac"] * 100))
    C = cfg.get("coach", {})
    for aid, rid, est in (("TAOFIK", "25081914897", 22), ("REZA", "25081927524", 26)):
        r, st = _run(cfg, aid, rid), _stream(cfg, aid, rid)
        name = _ath(cfg, aid)["name"]
        if not r or not st:
            ok(name, False, "lari %s atau data per detiknya tidak ada" % rid, "ada")
            continue
        w = m.run_walk(st, C["walk_mps"])["walk_s"]
        mv = (r.get("g") or {}).get("moving_s") or r["sec"]
        f = w / mv
        ok("%s (id %s)%s" % (name, rid, "" if st.get("sp") else " · perkiraan: tanpa kecepatan jam"), f > C["dec_walk_frac"],
           "%s di bawah %s m/s dari %s bergerak = %s %% → %s" % (hms(w), num(C["walk_mps"]), hms(mv), num(f * 100), "tidak berlaku (banyak jalan kaki)" if f > C["dec_walk_frac"] else "dinilai"),
           "> %d %% → tidak berlaku (perkiraan omPik ~%d menit)" % (round(C["dec_walk_frac"] * 100), est))


KIND = [("rest", r"istirahat"), ("race", r"lomba|race|maraton|^tes "), ("long", r"long run"), ("hard", r"latihan keras|tempo|interval"),
        ("str", r"kekuatan|perut|pinggul|beban|atas \+"), ("rec", r"pemulihan")]


def kind(title):
    t = title.lower()
    return next((k for k, rx in KIND if re.search(rx, t)), "easy")


def _num(x):
    return float(x.replace(",", "."))


def plan_km(c):
    t = c.split("\n")[0]
    tot, first = re.search(r"total\s+(\d+(?:[.,]\d+)?)\s*km", c, re.I), re.search(r"(\d+(?:[.,]\d+)?)\s*km", t, re.I)
    return _num(tot.group(1)) if tot else _num(first.group(1)) if first else None


def swapped(cfg, a, day, cells, ovr, events):
    """The planned day this run is judged against, as the dashboard's automatic session swap (swapAuto) picks it."""
    tol, runs = cfg["coach"].get("swap_tol"), _runs(cfg, a["id"])
    mon = day - dt.timedelta(days=day.weekday())
    dates = [mon + dt.timedelta(days=i) for i in range(7)]
    longest = {}
    for r in runs:
        if r["date"] in {d.isoformat() for d in dates} and r["km"] > longest.get(r["date"], 0):
            longest[r["date"]] = r["km"]
    run_k = lambda c: c and kind(c.split("\n")[0]) not in ("rest", "str")
    today = dt.date.today()
    miss = sorted([(d, plan_km(cells[i])) for i, d in enumerate(dates) if d < today and run_k(cells[i]) and plan_km(cells[i]) and d.isoformat() not in longest],
                  key=lambda q: -q[1])
    used, out = set(), {}
    for m_day, km in miss:
        best = None
        for i, r_day in enumerate(dates):
            x = longest.get(r_day.isoformat())
            own = cells[i]
            if x is None or r_day in used or (run_k(own) and not plan_km(own)):
                continue
            if r_day.isoformat() in events or (own and kind(own.split("\n")[0]) == "race") or ovr.get(r_day.isoformat()):
                continue
            e = abs(x - km) / km
            eo = abs(x - plan_km(own)) / plan_km(own) if run_k(own) and plan_km(own) else float("inf")
            if tol is not None and e <= tol and e < eo and (not best or e < best[1]):
                best = (r_day, e)
        if best:
            out[best[0]] = m_day
            used.add(best[0])
    return out.get(day, day), dates


def plan_hr(cfg, a, day, ovr):
    """Upper HR limit as the dashboard reads it: overrides.json, else the plan cell of the (swapped) day; without an
    HR range in the cell, the profile zones (recovery: Z1 top, other easy runs: Z2 top)."""
    prog = load_program(a["program"]) if not isinstance(a["program"], dict) else a["program"]
    ms = (day - m.d(prog["ms1"])).days // 7 + 1
    wk = next((w for w in prog["weeks"] if w["ms"] == ms), {})
    cells = [str(c or "") for c in (wk.get("days") or [""] * 7)]
    mine = ovr.get(a["id"].upper(), {})
    events = {e["date"] for e in prog.get("events", [])}
    c = mine.get(day.isoformat())
    if c:
        src = "overrides.json"
    else:
        sw, dates = swapped(cfg, a, day, cells, mine, events)
        c = cells[sw.weekday()]
        src = "rencana %s%s" % (sw.isoformat(), " (tukar sesi)" if sw != day else "")
    k = kind(c.split("\n")[0]) if c else None
    mt = re.search(r"detak jantung\s*(di bawah\s*)?(\d+)\s*(?:[-–]\s*(\d+))?", c, re.I)
    z = a.get("zones") or []
    if k not in ("easy", "long", "rec"):
        return None, "%s: %s (bukan long run / lari santai)" % (src, c.split("\n")[0].strip())
    top = int(mt.group(3) or mt.group(2)) if mt else (z[0] if k == "rec" else z[1]) if len(z) > 1 else None
    return top, "%s: %s" % (src, c.split("\n")[0].strip())


def u4e(cfg):
    print("\n4e. Lari bareng 15 Nov")
    C, day, ovr = cfg.get("coach", {}), dt.date(2026, 11, 15), overrides.load(cfg.get("overrides"), lambda *x: None)
    rows = []
    for aid, rid in (("TAOFIK", "25081914897"), ("REZA", "25081927524")):
        a, r, st = _ath(cfg, aid), _run(cfg, aid, rid), _stream(cfg, aid, rid)
        if not r or not st:
            return ok("data", False, "lari %s tidak ada" % rid, "ada")
        top, src = plan_hr(cfg, a, day, ovr)
        if top is None:
            return ok(a["name"], False, "lari bareng tidak berlaku: " + src, "long run atau lari santai")
        sp = [q for q in m.per_km(st, C.get("walk_mps")) if q[2] and q[0] >= .5]
        over = [i + 1 for i, q in enumerate(sp) if q[2] > top]
        rows.append((a["name"], r, top, src, over, len(sp)))
    mn = lambda r: int(r["start"][11:13]) * 60 + int(r["start"][14:16])
    gap = abs(mn(rows[0][1]) - mn(rows[1][1]))
    print("  start %s dan %s → beda %d menit (batas < %d)" % (rows[0][1]["start"][11:16], rows[1][1]["start"][11:16], gap, C["pair_start_min"]))
    for name, r, top, src, over, n in rows:
        flag = gap < C["pair_start_min"] and n and len(over) / n > C["pair_hr_frac"]
        want = name == "Reza"
        ok(name, flag == want, "HR di atas %s di %d dari %d km%s → %s  [batas dari %s]" % (top, len(over), n, " (km %s)" % ",".join(map(str, over)) if over else "",
                                                                                  "terbawa pace partner" if flag else "tidak ditandai", src),
           "Reza ditandai (12 dari 16 km di atas 152, km 6–16); Taofik tidak (0 km di atas 150)")


def u4f(cfg):
    print("\n4f. Gerbang 15 Nov, Reza")
    a = _ath(cfg, "REZA")
    well = _read(Path(cfg["data_dir"]) / "REZA" / "wellness.json", {})
    day = dt.date(2026, 11, 15)
    lv = (m.light(well, day, a.get("rhr")) or {}).get("level")
    low = m._streak(well, day, m.LOW_HRV)
    r = _run(cfg, "REZA", "25081927524")
    lim = cfg["coach"].get("red_easy_km", 8)
    km = r["km"] if r else None
    over = lv == "merah" and km is not None and km > lim * cfg["coach"]["km"][1]
    ok("lampu dan gerbang", lv == "merah" and over,
       "lampu %s (status HRV LOW/POOR %d hari berturut-turut) · %s km%s" % (lv or "–", low, num(km) if km else "–",
                                                                              " → Gerbang dilewati (+%s km)" % num(km - lim) if over else ""),
       "lampu merah (HRV LOW 6 hari) → batas ≤ %d km → Gerbang dilewati (+8 km); baris Jarak terpisah" % lim)
    print("        catatan: baris \"Gerbang pagi\" di dashboard muncul bila rencana hari itu (setelah tukar sesi) long run.")


def run(cfg, client_for=None):
    RES.clear()
    print("Uji data asli (RENCANA 23, RUMUS-BATAS-SUMBER 15 Nov)")
    for f in (lambda: u4a(cfg, client_for), lambda: u4b(cfg), lambda: u4c(cfg), lambda: u4d(cfg), lambda: u4e(cfg), lambda: u4f(cfg)):
        try:
            f()
        except Exception as e:  # noqa: BLE001 - one broken check must not hide the others
            ok("uji ini error", False, "%s: %s" % (type(e).__name__, e), "tanpa error")
    print("\nRingkas: %d lulus, %d gagal, %d dilewati" % (RES.count(True), RES.count(False), RES.count(None)))
    print("Salin semua teks di atas ke Claude.")
    return RES.count(False) == 0
