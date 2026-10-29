"""Minimal reader for Garmin FIT activity files (standard library only).

Only what the dashboard needs: the laps as the watch recorded them, the session
summary and the number of per-second records. Developer fields are skipped.
FIT layout: https://developer.garmin.com/fit/protocol/ (file header, then
definition and data messages; global message 18 = session, 19 = lap, 20 = record).
"""
import io
import struct
import zipfile

SESSION, LAP, RECORD = 18, 19, 20
FIT_EPOCH = 631065600          # 1989-12-31 00:00:00 UTC in Unix seconds
TRIGGER = {0: "manual", 1: "time", 2: "distance", 3: "position", 4: "position", 5: "position", 6: "position",
           7: "session_end", 8: "fitness_equipment"}
_INVALID = {1: 0xFF, 2: 0xFFFF, 4: 0xFFFFFFFF}
_FMT = {1: "B", 2: "H", 4: "I"}


def unwrap(blob):
    """Garmin's download is a zip holding <id>_ACTIVITY.fit; return the FIT bytes (or None)."""
    if blob[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            name = next((n for n in z.namelist() if n.lower().endswith(".fit")), None)
            return z.read(name) if name else None
    return blob if len(blob) > 12 and blob[8:12] == b".FIT" else None


def messages(data):
    """Yield (global message number, {field number: raw bytes}, endian) for every data message."""
    hsize = data[0]
    size = struct.unpack("<I", data[4:8])[0]
    if data[8:12] != b".FIT":
        raise ValueError("bukan file FIT")
    i, end, defs = hsize, min(len(data), hsize + size), {}
    while i < end:
        h = data[i]
        i += 1
        if h & 0x80:                     # compressed-timestamp data message
            d = defs[(h >> 5) & 0x03]
        elif h & 0x40:                   # definition message
            arch = data[i + 1]
            e = "<" if arch == 0 else ">"
            g = struct.unpack(e + "H", data[i + 2:i + 4])[0]
            n = data[i + 4]
            i += 5
            fields = [(data[i + 3 * k], data[i + 3 * k + 1]) for k in range(n)]
            i += 3 * n
            dev = 0
            if h & 0x20:
                nd = data[i]
                i += 1
                dev = sum(data[i + 3 * k + 1] for k in range(nd))
                i += 3 * nd
            defs[h & 0x0F] = {"g": g, "f": fields, "dev": dev, "e": e}
            continue
        else:
            d = defs[h & 0x0F]
        vals = {}
        for num, sz in d["f"]:
            vals[num] = data[i:i + sz]
            i += sz
        i += d["dev"]
        yield d["g"], vals, d["e"]


def _u(raw, e):
    n = len(raw or b"")
    if n not in _FMT:
        return None
    v = struct.unpack(e + _FMT[n], raw)[0]
    return None if v == _INVALID[n] else v


def read(blob):
    """{"laps": [{start, km, sec, elapsed, hr, hr_max, cad, trigger}], "session": {...}, "records": n}."""
    data = unwrap(blob)
    if data is None:
        raise ValueError("bukan file FIT")
    laps, session, records = [], {}, 0
    for g, f, e in messages(data):
        if g == RECORD:
            records += 1
        elif g == LAP:
            dist, timer, elapsed, start = _u(f.get(9), e), _u(f.get(8), e), _u(f.get(7), e), _u(f.get(2), e)
            cad = _u(f.get(17), e)
            laps.append({
                "start": None if start is None else start + FIT_EPOCH,
                "km": round(dist / 100000, 3) if dist is not None else None,
                "sec": round(timer / 1000, 1) if timer is not None else None,
                "elapsed": round(elapsed / 1000, 1) if elapsed is not None else None,
                "hr": _u(f.get(15), e), "hr_max": _u(f.get(16), e),
                "cad": None if cad is None else cad * 2,   # running cadence is stored per leg
                "trigger": TRIGGER.get(_u(f.get(24), e), "other"),
            })
        elif g == SESSION:
            dist, laps_n = _u(f.get(9), e), _u(f.get(26), e)
            session = {"km": None if dist is None else round(dist / 100000, 3), "laps": laps_n}
    return {"laps": laps, "session": session, "records": records}
