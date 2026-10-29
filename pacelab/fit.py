"""Minimal reader for Garmin FIT activity files (standard library only).

Only what the dashboard needs: the laps as the watch recorded them, the session
summary and the number of per-second records. Developer fields are skipped.
FIT layout: https://developer.garmin.com/fit/protocol/ (file header, then
definition and data messages; global message 18 = session, 19 = lap, 20 = record).
"""
import io
import struct
import zipfile

SESSION, LAP, RECORD, EVENT = 18, 19, 20, 21
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
    """Yield (global message number, {field number: raw bytes}, endian, timestamp) for every data message.
    The timestamp (FIT seconds) is the message's own field 253 or, for compressed headers, rebuilt from
    the last full timestamp and the 5-bit offset."""
    hsize = data[0]
    size = struct.unpack("<I", data[4:8])[0]
    if data[8:12] != b".FIT":
        raise ValueError("bukan file FIT")
    i, end, defs, last = hsize, min(len(data), hsize + size), {}, None
    while i < end:
        h = data[i]
        i += 1
        ts = None
        if h & 0x80:                     # compressed-timestamp data message
            d = defs[(h >> 5) & 0x03]
            if last is not None:
                off = h & 0x1F
                ts = (last & ~0x1F) + off + (0x20 if off < (last & 0x1F) else 0)
                last = ts
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
        if 253 in vals:
            full = _u(vals[253], d["e"])
            if full is not None:
                ts = last = full
        yield d["g"], vals, d["e"], ts


def _u(raw, e):
    n = len(raw or b"")
    if n not in _FMT:
        return None
    v = struct.unpack(e + _FMT[n], raw)[0]
    return None if v == _INVALID[n] else v


def _alt(f, e):
    a = _u(f.get(78), e)                  # enhanced_altitude
    a = _u(f.get(2), e) if a is None else a
    return None if a is None else round(a / 5 - 500, 1)


def read(blob):
    """{"laps": [{start, km, sec, elapsed, hr, hr_max, cad, trigger}], "session": {...}, "records": n,
        "stream": {"t","d","hr","cad","el"} or None}.

    The stream uses timer time (pauses left out, from the timer start/stop events), like the
    sumDuration column of Garmin's activity details, so both sources cut kilometres the same way."""
    data = unwrap(blob)
    if data is None:
        raise ValueError("bukan file FIT")
    laps, session, records = [], {}, 0
    t, d, hr, cad, el = [], [], [], [], []
    run, acc, since = False, 0.0, None
    for g, f, e, ts in messages(data):
        if g == EVENT and _u(f.get(0), e) == 0 and ts is not None:      # timer events
            kind = _u(f.get(1), e)
            if kind == 0 and not run:                                       # start
                run, since = True, ts
            elif kind in (1, 4) and run:                                    # stop / stop_all
                run, acc = False, acc + ts - since
        if g == RECORD:
            records += 1
            dist = _u(f.get(5), e)
            if ts is None or dist is None:
                continue
            if since is None:                                               # no timer events: wall clock
                run, since = True, ts
            tv, dv = (acc + ts - since) if run else acc, dist / 100
            if t and (tv < t[-1] or dv < d[-1]):
                continue
            c, frac = _u(f.get(4), e), _u(f.get(53), e)
            t.append(round(tv, 1))
            d.append(round(dv, 1))
            h = _u(f.get(3), e)
            hr.append(h or None)
            cad.append(round((c + (frac or 0) / 128) * 2) if c else None)  # per leg -> steps per minute
            el.append(_alt(f, e))
        elif g == LAP:
            dist, timer, elapsed, start = _u(f.get(9), e), _u(f.get(8), e), _u(f.get(7), e), _u(f.get(2), e)
            lc = _u(f.get(17), e)
            laps.append({
                "start": None if start is None else start + FIT_EPOCH,
                "km": round(dist / 100000, 3) if dist is not None else None,
                "sec": round(timer / 1000, 1) if timer is not None else None,
                "elapsed": round(elapsed / 1000, 1) if elapsed is not None else None,
                "hr": _u(f.get(15), e), "hr_max": _u(f.get(16), e),
                "cad": None if lc is None else lc * 2,     # running cadence is stored per leg
                "trigger": TRIGGER.get(_u(f.get(24), e), "other"),
            })
        elif g == SESSION:
            dist, laps_n = _u(f.get(9), e), _u(f.get(26), e)
            session = {"km": None if dist is None else round(dist / 100000, 3), "laps": laps_n}
    stream = {"t": t, "d": d, "hr": hr, "cad": cad if any(cad) else None, "el": el if any(v is not None for v in el) else None} \
        if len(t) > 1 else None
    return {"laps": laps, "session": session, "records": records, "stream": stream}
