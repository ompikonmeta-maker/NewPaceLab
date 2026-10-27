"""Read a training-program workbook (Program_Marathon_<NAME>.xlsx).

Only the facts the dashboard needs are extracted: weekly targets (Kalender),
race date, checkpoints and target times (Checkpoint), sleep targets
(Tidur dan Pemulihan) and weekly weight targets (Log Berat).
"""
import datetime as dt
import re

from .xlsx import read_workbook

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6, "jul": 7,
          "agu": 8, "aug": 8, "agt": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11, "des": 12, "dec": 12}
EXCEL_EPOCH = dt.date(1899, 12, 30)
# Kalender legend: grey row = down week, light orange row = race/test week
FILL_DOWN = "F2F2F2"
FILL_EVENT = "FCE4D6"


class ProgramError(ValueError):
    pass


def parse_date(v):
    """'03 Agu 2026', 'Sab 22 Agu 2026', 'MINGGU 13 JUN 2027', Excel serial -> date."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return EXCEL_EPOCH + dt.timedelta(days=int(v))
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\.?\s+(\d{4})", str(v))
    if not m:
        return None
    mon = MONTHS.get(m.group(2)[:3].lower())
    if not mon:
        return None
    return dt.date(int(m.group(3)), mon, int(m.group(1)))


def parse_times(text):
    """All clock times in text, as seconds. '5:30' (h:mm) and '5:16:27' (h:mm:ss)."""
    out = []
    for m in re.finditer(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", str(text or "")):
        h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        out.append(h * 3600 + mi * 60 + s)
    return out


def parse_duration(text):
    """'6 jam 15 menit' / '7 jam' -> seconds."""
    t = str(text or "").lower()
    h = re.search(r"(\d+)\s*jam", t)
    m = re.search(r"(\d+)\s*menit", t)
    if not h and not m:
        return None
    return (int(h.group(1)) if h else 0) * 3600 + (int(m.group(1)) if m else 0) * 60


def num(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _cell(row, i):
    return row[i] if i < len(row) else None


def _find_row(rows, pred, start=0):
    for i in range(start, len(rows)):
        if pred(rows[i]):
            return i
    return -1


def _label(row, i=0):
    return str(_cell(row, i) or "").strip().lower()


def load_program(path):
    fills = {}
    wb = read_workbook(path, fills)
    for need in ("Kalender", "Checkpoint"):
        if need not in wb:
            raise ProgramError("%s: sheet '%s' tidak ditemukan" % (path, need))

    weeks = _kalender(wb["Kalender"], fills.get("Kalender", {}))
    if not weeks:
        raise ProgramError("%s: tabel Kalender kosong" % path)
    first = weeks[0]
    ms1 = dt.date.fromisoformat(first["start"]) - dt.timedelta(weeks=first["ms"] - 1)

    cp = _checkpoint(wb["Checkpoint"])
    race = next((c for c in cp["events"] if "maraton" in c["event"].lower()), None)
    race_date = race["date"] if race else _race_from_guide(wb.get("Panduan", []))
    if not race_date:
        raise ProgramError("%s: tanggal race tidak ditemukan" % path)

    title = str(_cell(wb["Kalender"][0], 0) or "")
    m = re.search(r"KALENDER HARIAN\s+(\S+)", title)
    return {
        "name": m.group(1).title() if m else None,
        "ms1": ms1.isoformat(),
        "race_date": race_date,
        "total_weeks": max(w["ms"] for w in weeks),
        "weeks": weeks,
        "events": cp["events"],
        "target": cp["target"],
        "sleep": _sleep(wb.get("Tidur dan Pemulihan", [])),
        "weight": _weight(wb.get("Log Berat", [])),
    }


def _kalender(rows, fill):
    h = _find_row(rows, lambda r: _label(r) == "ms")
    if h < 0:
        raise ProgramError("Kalender: baris header 'MS' tidak ditemukan")
    head = [str(c or "").replace("\n", " ").strip().upper() for c in rows[h]]

    def col(prefix):
        for i, c in enumerate(head):
            if c.startswith(prefix):
                return i
        raise ProgramError("Kalender: kolom '%s' tidak ditemukan" % prefix)

    c_date, c_phase, c_km, c_lr = col("TANGGAL"), col("FASE"), col("KM TOTAL"), col("LONG RUN")
    c_note = col("CATATAN")
    weeks = []
    for ri in range(h + 1, len(rows)):
        r = rows[ri]
        ms = num(_cell(r, 0))
        start = parse_date(_cell(r, c_date))
        if ms is None or start is None:
            continue
        note = " | ".join(str(c) for c in r[c_note:] if c)
        note_l = note.lower()
        color = (fill.get((ri, 0)) or "")[-6:].upper()
        weeks.append({
            "ms": int(ms),
            "start": start.isoformat(),
            "phase": re.sub(r"^\d+\s*", "", str(_cell(r, c_phase) or "")).strip(),
            "km": num(_cell(r, c_km)),
            "lr": num(_cell(r, c_lr)),
            "down": color == FILL_DOWN and "bukan minggu ringan" not in note_l,
            "event": color == FILL_EVENT,
            "note": note.split("|")[0].strip(),
        })
    return weeks


def _checkpoint(rows):
    events, target = [], {}
    h = _find_row(rows, lambda r: _label(r) == "ms" and "acara" in _label(r, 2))
    if h >= 0:
        for r in rows[h + 1:]:
            ms = num(_cell(r, 0))
            d = parse_date(_cell(r, 1))
            if ms is None or d is None:
                break
            events.append({"ms": int(ms), "date": d.isoformat(), "event": str(_cell(r, 2) or "").strip()})
    t = _find_row(rows, lambda r: _label(r).startswith("tingkat"))
    if t >= 0:
        for r in rows[t + 1:]:
            lab = _label(r)
            if not re.match(r"^[abc]\s*-", lab):
                break
            secs = parse_times(_cell(r, 1))
            if not secs:
                continue
            txt = str(_cell(r, 1)).lower()
            lo, hi = (min(secs), max(secs)) if len(secs) > 1 else (secs[0], secs[0])
            if "bawah" in txt and len(secs) == 1:
                lo = None  # "di bawah 4:45:00": open lower bound
            target[lab[0].upper()] = {"lo": lo, "hi": hi, "text": str(_cell(r, 1)).strip()}
    return {"events": events, "target": target}


def _race_from_guide(rows):
    for r in rows:
        if _label(r, 1) == "race":
            d = parse_date(_cell(r, 2))
            return d.isoformat() if d else None
    return None


def _sleep(rows):
    out = {}
    for r in rows:
        lab = _label(r)
        if lab == "target minimum":
            out["min"] = parse_duration(_cell(r, 1))
        elif lab.startswith("target malam sebelum long run"):
            out["before_lr"] = parse_duration(_cell(r, 1))
    return out


def _weight(rows):
    h = _find_row(rows, lambda r: _label(r) == "ms")
    if h < 0:
        return []
    head = [str(c or "").lower() for c in rows[h]]
    ci = next((i for i, c in enumerate(head) if c.startswith("target") or c.startswith("acuan")), None)
    if ci is None:
        return []
    out, seen = [], set()
    for r in rows[h + 1:]:
        ms, d, kg = num(_cell(r, 0)), parse_date(_cell(r, 1)), num(_cell(r, ci))
        if ms is None or d is None or kg is None or ms in seen:
            continue  # the sheet ends with a filled-in example row; keep the first per MS
        seen.add(ms)
        out.append({"ms": int(ms), "date": d.isoformat(), "kg": kg})
    return out
