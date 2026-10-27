import datetime as dt
import unittest

from pacelab import metrics as m


def stream(pace_s_per_km, km, hr=None, step=5):
    """Constant-pace stream sampled every `step` s; hr may be a function of t."""
    t, x, h = [], [], []
    v = 1000.0 / pace_s_per_km
    n = int(km * 1000 / v / step) + 1
    for i in range(n + 1):
        t.append(i * step)
        x.append(min(i * step * v, km * 1000))
        h.append(hr(i * step) if callable(hr) else (hr or 150))
    return {"t": t, "d": x, "hr": h}


class StreamTest(unittest.TestCase):
    def test_best_effort_constant_pace(self):
        s = stream(360, 12)  # 6:00/km
        self.assertAlmostEqual(m.best_effort(s, 5000), 1800, delta=1)
        self.assertAlmostEqual(m.best_effort(s, 10000), 3600, delta=1)
        self.assertIsNone(m.best_effort(s, 21097.5))

    def test_best_effort_finds_fast_segment(self):
        slow, fast = stream(420, 3), stream(300, 5)
        off_t, off_d = slow["t"][-1], slow["d"][-1]
        s = {"t": slow["t"] + [off_t + t for t in fast["t"][1:]],
             "d": slow["d"] + [off_d + x for x in fast["d"][1:]],
             "hr": slow["hr"] + fast["hr"][1:]}
        self.assertAlmostEqual(m.best_effort(s, 5000), 1500, delta=2)

    def test_decoupling(self):
        flat = stream(540, 15, hr=145)
        self.assertAlmostEqual(m.decoupling(flat), 0.0, delta=0.2)
        drift = stream(540, 15, hr=lambda t: 140 if t < 4050 else 154)  # +10% HR in 2nd half
        self.assertAlmostEqual(m.decoupling(drift), 9.1, delta=0.3)
        self.assertIsNone(m.decoupling(stream(540, 2)))  # too short


PROGRAM = {"ms1": "2026-06-22", "total_weeks": 51, "weeks": [
    {"ms": 1, "km": 20, "lr": 10, "down": False, "event": False, "phase": "Base"},
    {"ms": 2, "km": 20, "lr": 10, "down": False, "event": False, "phase": "Base"},
    {"ms": 3, "km": 20, "lr": None, "down": True, "event": False, "phase": "Base"}]}


class WeekTest(unittest.TestCase):
    def test_weekly_and_streak(self):
        runs = [{"id": 1, "date": "2026-06-23", "km": 8, "sec": 0},
                {"id": 2, "date": "2026-06-27", "km": 11, "sec": 0},
                {"id": 3, "date": "2026-07-04", "km": 12, "sec": 0}]
        w = m.weekly(runs, PROGRAM, dt.date(2026, 7, 8))
        self.assertEqual([(x["ms"], x["km"], x["lr"], x["done"]) for x in w],
                         [(1, 19, 11, True), (2, 12, 12, True), (3, 0, None, False)])
        self.assertEqual(w[0]["lr_id"], 2)
        self.assertEqual(m.streaks(w), 1)  # 19/20 ok, 12/20 breaks it, week 3 not done

    def test_ms_of(self):
        self.assertEqual(m.ms_of("2026-10-27", "2026-06-22"), 19)


class EffortTest(unittest.TestCase):
    def test_pb_and_estimate(self):
        eff = {"5K": [("2026-06-01", 1900, 1), ("2026-07-01", 1950, 2), ("2026-08-01", 1800, 3)],
               "10K": [("2026-08-10", 3700, 4)], "Half": []}
        pb = m.pb_progress(eff)
        self.assertEqual([p["sec"] for p in pb["5K"]], [1900, 1800])
        sec, src = m.marathon_estimate(eff, dt.date(2026, 9, 1))
        self.assertEqual(src, "10K")
        self.assertAlmostEqual(sec, 3700 * 4.2195 ** 1.06, delta=1)
        self.assertEqual(m.marathon_estimate(eff, dt.date(2027, 6, 1)), (None, None))


def wday(sleep_h, bb, status, rhr=55):
    return {"sleep_s": sleep_h * 3600, "bb": bb, "hrv_status": status, "hrv": 50, "rhr": rhr}


class LightTest(unittest.TestCase):
    def setUp(self):
        base = dt.date(2026, 10, 1)
        self.w = {(base + dt.timedelta(days=i)).isoformat(): wday(7, 70, "BALANCED") for i in range(28)}
        self.day = base + dt.timedelta(days=27)

    def set(self, **kw):
        self.w[self.day.isoformat()].update(kw)

    def test_levels(self):
        self.assertEqual(m.light(self.w, self.day)["level"], "hijau")
        self.set(sleep_s=5.5 * 3600)
        self.assertEqual(m.light(self.w, self.day)["level"], "kuning")
        self.set(sleep_s=7 * 3600, bb=35)
        self.assertEqual(m.light(self.w, self.day)["level"], "oranye")
        self.set(bb=70, rhr=62)  # +7 over the 28-day median
        self.assertEqual(m.light(self.w, self.day)["level"], "merah")

    def test_no_hrv_reading_and_sleep_rhr(self):
        self.set(hrv_status="NONE")
        self.assertEqual(m.light(self.w, self.day)["level"], "hijau")
        self.set(rhr=None, rhr_sleep=62)  # falls back to the sleep record: +7
        self.assertEqual(m.light(self.w, self.day)["level"], "merah")

    def test_hrv_low_streak(self):
        for i in range(3):
            self.w[(self.day - dt.timedelta(days=i)).isoformat()]["hrv_status"] = "LOW"
        self.assertEqual(m.light(self.w, self.day)["level"], "merah")
        self.w[(self.day - dt.timedelta(days=2)).isoformat()]["hrv_status"] = "BALANCED"
        self.assertEqual(m.light(self.w, self.day)["level"], "oranye")

    def test_saturday_rule(self):
        self.assertEqual(m.saturday_rule(wday(6.5, 55, "BALANCED")), "Jalankan")
        self.assertEqual(m.saturday_rule(wday(5.5, 55, "BALANCED")), "Potong 20%")
        self.assertEqual(m.saturday_rule(wday(4.5, 35, "BALANCED")), "Potong 40%")
        self.assertEqual(m.saturday_rule(wday(4.5, 25, "LOW")), "Ganti easy 8 km")


class ScoreTest(unittest.TestCase):
    def test_score(self):
        a = {"km_pct": .99, "lr_pct": 1.02, "sleep_pct": 1.03, "green": 6}
        b = {"km_pct": .94, "lr_pct": 1.03, "sleep_pct": .90, "green": 6}
        s = m.score(a, b)
        self.assertEqual((s["a"], s["b"]), (2, 1))
        self.assertIsNone(s["cats"][3]["win"])


if __name__ == "__main__":
    unittest.main()
