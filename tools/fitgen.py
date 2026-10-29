"""Write small FIT activity files (standard library only) for the mock server and the tests.

Messages: timer start/stop events (21), per-second records (20), laps (19), session (18).
Only the fields pacelab/fit.py reads are written.
"""
import io
import struct
import zipfile

FIT_EPOCH = 631065600


def _def(local, glob, fields):
    return bytes([0x40 | local, 0, 0]) + struct.pack("<H", glob) + bytes([len(fields)]) + \
        b"".join(bytes([n, s, t]) for n, s, t in fields)


def write_fit(rows, start_unix, lap_m=1000, manual=()):
    """rows: [(t seconds, distance m, hr, cadence spm, elevation m)], one per sample, timer time.
    Auto-lap every lap_m metres; manual = extra lap boundaries in metres (as if the lap key was pressed).
    The last lap ends the session."""
    t0 = start_unix - FIT_EPOCH
    out = b""
    out += _def(0, 21, [(253, 4, 134), (0, 1, 0), (1, 1, 0)])                       # event: timestamp, event, type
    out += _def(1, 20, [(253, 4, 134), (5, 4, 134), (3, 1, 2), (4, 1, 2), (78, 4, 134)])
    out += _def(2, 19, [(253, 4, 134), (2, 4, 134), (7, 4, 134), (8, 4, 134), (9, 4, 134), (15, 1, 2), (16, 1, 2), (17, 1, 2), (24, 1, 0)])
    out += bytes([0]) + struct.pack("<IBB", t0, 0, 0)                                 # timer start
    manual, laps, a, lap0 = sorted(manual), [], 0, 0.0      # auto-lap restarts after a manual lap, like the watch
    for i, (t, d, hr, cad, el) in enumerate(rows):
        out += bytes([1]) + struct.pack("<IIBBI", t0 + int(t), int(d * 100), hr or 0xFF, (cad // 2) if cad else 0xFF,
                                        int((el + 500) * 5) if el is not None else 0xFFFFFFFF)
        last = i == len(rows) - 1
        hand = bool(manual) and d >= manual[0]
        if hand or d >= lap0 + lap_m or last:
            trig = 7 if last else 0 if hand else 2
            while manual and d >= manual[0]:
                manual.pop(0)
            lap0 = d
            seg = rows[a:i + 1]
            sec = t - (rows[a - 1][0] if a else 0)
            dist = d - (rows[a - 1][1] if a else 0)
            hrs = [r[2] for r in seg if r[2]]
            cads = [r[3] for r in seg if r[3]]
            laps.append(struct.pack("<IIIIIBBBB", t0 + int(t), t0 + int(rows[a][0]), int(sec * 1000), int(sec * 1000), int(dist * 100),
                                    round(sum(hrs) / len(hrs)) if hrs else 0xFF, max(hrs) if hrs else 0xFF,
                                    round(sum(cads) / len(cads) / 2) if cads else 0xFF, trig))
            a = i + 1
    out += bytes([0]) + struct.pack("<IBB", t0 + int(rows[-1][0]), 0, 4)             # timer stop_all
    for lap in laps:
        out += bytes([2]) + lap
    out += _def(3, 18, [(9, 4, 134), (26, 2, 132)])
    out += bytes([3]) + struct.pack("<IH", int(rows[-1][1] * 100), len(laps))
    head = struct.pack("<BBHI4sH", 14, 0x20, 2132, len(out), b".FIT", 0)
    return head + out + b"\x00\x00"


def zipped(fit_bytes, name="activity_ACTIVITY.fit"):
    """Garmin's download service sends the FIT inside a zip."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, fit_bytes)
    return buf.getvalue()
