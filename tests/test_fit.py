import io
import struct
import unittest
import zipfile

from pacelab import fit


def build_fit(laps, records=3):
    """A tiny FIT file: lap (19), record (20) incl. one compressed-timestamp record, session (18)."""
    body = b""
    # definition local 0 -> lap: start_time(2) u32, total_elapsed(7) u32, total_timer(8) u32, distance(9) u32, avg_hr(15) u8, trigger(24) u8
    body += bytes([0x40, 0, 0]) + struct.pack("<H", 19) + bytes([6, 2, 4, 134, 7, 4, 134, 8, 4, 134, 9, 4, 134, 15, 1, 2, 24, 1, 0])
    for km, sec, hr, trig in laps:
        body += bytes([0x00]) + struct.pack("<IIIIBB", 1000000000, int(sec * 1000), int(sec * 1000), int(km * 100000), hr, trig)
    # definition local 1 -> record: timestamp(253) u32, heart_rate(3) u8
    body += bytes([0x41, 0, 0]) + struct.pack("<H", 20) + bytes([2, 253, 4, 134, 3, 1, 2])
    for k in range(records - 1):
        body += bytes([0x01]) + struct.pack("<IB", 1000000000 + k, 140)
    body += bytes([0x80 | (1 << 5) | 5]) + struct.pack("<IB", 0, 141)   # compressed-timestamp header
    # definition local 2 -> session: total_distance(9) u32, num_laps(26) u16
    body += bytes([0x42, 0, 0]) + struct.pack("<H", 18) + bytes([2, 9, 4, 134, 26, 2, 132])
    body += bytes([0x02]) + struct.pack("<IH", int(sum(l[0] for l in laps) * 100000), len(laps))
    head = struct.pack("<BBHI4sH", 14, 0x20, 2132, len(body), b".FIT", 0)
    return head + body + b"\x00\x00"


class FitTest(unittest.TestCase):
    LAPS = [(1.0, 522.4, 132, 2), (0.158, 80.8, 140, 0), (1.0, 354.2, 165, 2), (0.014, 9.3, 151, 7)]

    def test_laps_session_records(self):
        r = fit.read(build_fit(self.LAPS, records=4))
        self.assertEqual([l["km"] for l in r["laps"]], [1.0, 0.158, 1.0, 0.014])
        self.assertEqual([l["sec"] for l in r["laps"]], [522.4, 80.8, 354.2, 9.3])
        self.assertEqual([l["trigger"] for l in r["laps"]], ["distance", "manual", "distance", "session_end"])
        self.assertEqual(r["laps"][2]["hr"], 165)
        self.assertEqual(r["session"], {"km": 2.172, "laps": 4})
        self.assertEqual(r["records"], 4)

    def test_zip_from_garmin_download(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("123_ACTIVITY.fit", build_fit(self.LAPS))
        self.assertEqual(len(fit.read(buf.getvalue())["laps"]), 4)

    def test_not_fit(self):
        with self.assertRaises(ValueError):
            fit.read(b'{"error":"NOT_FOUND"}')
