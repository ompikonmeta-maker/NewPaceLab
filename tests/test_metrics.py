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

    def test_short_gps_runs_count_as_estimated_efforts(self):
        rule = {"min_frac": 0.98, "test_min_frac": 0.8}
        runs = [{"id": 1, "date": "2026-10-10", "km": 4.718}, {"id": 2, "date": "2026-10-10", "km": 2.0},
                {"id": 3, "date": "2026-10-11", "km": 4.996}, {"id": 4, "date": "2026-10-12", "km": 4.7},
                {"id": 5, "date": "2026-10-13", "km": 5.024}]
        streams = {r["id"]: stream(360, r["km"]) for r in runs}
        eff = m.efforts(runs, streams, rule, m.test_days([{"date": "2026-10-10", "event": "Tes 5K"}]))["5K"]
        got = {rid: (sec, est) for _, sec, rid, est in eff}
        self.assertAlmostEqual(got[1][0], 1800, delta=6)   # test day, 4.7 km at 6:00/km -> 30:00 for 5 km
        self.assertTrue(got[1][1])
        self.assertNotIn(2, got)                           # only the longest run of a test day
        self.assertTrue(got[3][1])                         # 4 m short: within 98%
        self.assertNotIn(4, got)                           # 4.7 km on an ordinary day stays out
        self.assertFalse(got[5][1])                        # a full 5 km is measured, not estimated
        self.assertEqual(len(m.efforts(runs, streams)["5K"]), 1)   # without the rule: strict 5000 m

    def test_decoupling(self):
        flat = stream(540, 15, hr=145)
        self.assertAlmostEqual(m.decoupling(flat), 0.0, delta=0.2)
        drift = stream(540, 15, hr=lambda t: 140 if t < 4050 else 154)  # +10% HR in the 2nd half
        r = m.decoupling_detail(drift)
        self.assertAlmostEqual(r["full"], 9.1, delta=0.3)  # all records: halves split exactly at the HR step
        # rated version drops the first 3 km, so its 1st half already holds some 154-bpm records
        self.assertTrue(0 < r["pct"] < r["full"])
        self.assertEqual(r["pct"], m.decoupling(drift))
        self.assertIsNone(m.decoupling(stream(540, 2)))  # too short
        (n1, k1, v1, h1), (n2, k2, v2, h2) = r["h"]
        self.assertLessEqual(abs(n1 - n2), 1)  # split by record count
        e1, e2 = v1 / h1, v2 / h2  # the working shown in the dashboard gives the same result
        self.assertAlmostEqual((e1 - e2) / e1 * 100, r["pct"], delta=0.06)

    def test_per_km(self):
        s = stream(540, 5.5, hr=lambda t: 140 if t < 1350 else 150)
        s["cad"] = [170] * len(s["t"])
        s["el"] = list(range(len(s["t"])))
        k = m.per_km(s)
        self.assertEqual(len(k), 6)  # 5 full km + the last 500 m
        self.assertAlmostEqual(k[0][0], 1.0, delta=.01)
        self.assertAlmostEqual(k[0][1], 540, delta=6)
        self.assertEqual(k[0][2], 140)
        self.assertEqual(k[4][2], 150)
        self.assertEqual(k[0][3], 170)
        self.assertAlmostEqual(k[-1][0], .5, delta=.01)
        self.assertEqual(m.per_km(stream(540, 1.2))[-1][0], 1.0)  # 200 m tail dropped

    def test_walking_left_out_of_cadence(self):
        run, walk = stream(360, 2), stream(1000 / 1.0, .12)          # 2 km at 6:00/km, then 2 min walking at 1 m/s
        t0, d0 = run["t"][-1], run["d"][-1]
        s = {"t": run["t"] + [t0 + t for t in walk["t"][1:]], "d": run["d"] + [d0 + d for d in walk["d"][1:]]}
        s["hr"] = [140] * len(s["t"])
        s["cad"] = [170] * len(run["t"]) + [110] * (len(walk["t"]) - 1)
        rw = m.run_walk(s, 1.5)
        self.assertAlmostEqual(rw["walk_s"], 120, delta=12)
        self.assertAlmostEqual(rw["cad_run"], 170, delta=1)            # the walking steps do not pull it down
        k = m.per_km(s, 1.5)
        self.assertEqual(k[0][5], 0)
        self.assertEqual(k[1][3], 170)
        self.assertEqual(m.per_km(s)[0][5], 0)                         # without a threshold nothing is walking

    def test_decoupling_filters_records(self):
        s = stream(540, 15, hr=lambda t: 70 if t < 1000 else 150)  # HR <= 80 is dropped
        self.assertAlmostEqual(m.decoupling(s), 0.0, delta=0.2)
        s = stream(540, 15, hr=150)
        s["d"][200:260] = [s["d"][199]] * 60  # standing still (speed 0) is dropped
        self.assertAlmostEqual(m.decoupling(s), 0.0, delta=0.3)


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
        self.assertEqual(src, "10K")  # the 10K predicts a faster marathon than the 5K
        self.assertAlmostEqual(sec, 3700 * 4.2195 ** 1.06, delta=1)
        # a slow 10K inside an easy long run must not hide a fast 5K race
        eff["10K"] = [("2026-08-10", 5000, 4)]
        self.assertEqual(m.marathon_estimate(eff, dt.date(2026, 9, 1))[1], "5K")
        self.assertEqual(m.marathon_estimate(eff, dt.date(2027, 6, 1)), (None, None))


def wday(sleep_h, bb, status, rhr=55):
    return {"sleep_s": sleep_h * 3600, "bb": bb, "hrv_status": status, "hrv": 50, "rhr": rhr}


class LightTest(unittest.TestCase):
    """docs/RUMUS-BATAS-SUMBER.md §7b (versi 10 Nov 2026)."""
    def setUp(self):
        base = dt.date(2026, 10, 1)
        self.w = {(base + dt.timedelta(days=i)).isoformat(): wday(7, 70, "BALANCED") for i in range(28)}
        self.day = base + dt.timedelta(days=27)

    def set(self, **kw):
        self.w[self.day.isoformat()].update(kw)

    def lv(self, profile=None):
        return m.light(self.w, self.day, profile)["level"]

    def test_levels(self):
        self.assertEqual(self.lv(), "hijau")
        self.set(sleep_s=5.5 * 3600)                 # §7 row 2
        self.assertEqual(self.lv(), "kuning")
        self.set(sleep_s=7 * 3600, bb=35)            # BB < 50 alone is row 2 too
        self.assertEqual(self.lv(), "kuning")
        self.set(sleep_s=4.5 * 3600, bb=35)          # §7 row 3
        self.assertEqual(self.lv(), "oranye")
        self.set(sleep_s=7 * 3600, bb=70, rhr=60)    # +5 over the 7-day mean
        self.assertEqual(self.lv(), "kuning")
        self.set(rhr=62)                             # +7
        self.assertEqual(self.lv(), "oranye")

    def test_hrv_status(self):
        self.set(hrv_status="UNBALANCED")
        self.assertEqual(self.lv(), "kuning")
        for i in range(3):
            self.w[(self.day - dt.timedelta(days=i)).isoformat()]["hrv_status"] = "UNBALANCED"
        self.assertEqual(self.lv(), "oranye")
        for i in range(3):
            self.w[(self.day - dt.timedelta(days=i)).isoformat()]["hrv_status"] = "LOW"
        self.assertEqual(self.lv(), "merah")
        self.w[(self.day - dt.timedelta(days=2)).isoformat()]["hrv_status"] = "BALANCED"
        self.assertEqual(self.lv(), "kuning")        # LOW 2 days: not all clear

    def test_last_night_under_normal_range(self):
        self.set(hrv=40, hrv_low=43)
        self.assertEqual(self.lv(), "kuning")

    def test_rhr_profile_when_history_is_short(self):
        self.w = {self.day.isoformat(): wday(7, 70, "BALANCED", rhr=62)}
        self.assertEqual(self.lv(), "hijau")         # no baseline, no profile
        self.assertEqual(self.lv(55), "oranye")      # profile 55: +7

    def test_checks_explain_the_level(self):
        s = lambda: {c["k"]: c["s"] for c in m.light(self.w, self.day)["checks"]}
        self.assertEqual(s(), {"hrv": "ok", "bb": "ok", "sleep": "ok", "rhr": "ok"})
        self.set(sleep_s=5.5 * 3600, bb=45)
        self.assertEqual(s(), {"hrv": "ok", "bb": "warn", "sleep": "warn", "rhr": "ok"})
        self.set(sleep_s=4.5 * 3600, bb=35, rhr=62, hrv_status="NONE")
        self.assertEqual(s(), {"hrv": None, "bb": "bad", "sleep": "bad", "rhr": "bad"})

    def test_green_needs_body_battery_50(self):
        self.set(bb=50)
        self.assertEqual(self.lv(), "hijau")
        self.set(bb=49)
        self.assertEqual(self.lv(), "kuning")

    def test_no_hrv_reading_and_sleep_rhr(self):
        self.set(hrv_status="NONE")
        self.assertEqual(self.lv(), "hijau")
        self.set(rhr=None, rhr_sleep=62)  # falls back to the sleep record: +7
        self.assertEqual(self.lv(), "oranye")

    def test_saturday_rule(self):  # §7 only; the old "ganti easy 8 km" row is not in the document
        self.assertEqual(m.saturday_rule(wday(6.5, 55, "BALANCED")), "Jalankan")
        self.assertEqual(m.saturday_rule(wday(5.5, 55, "BALANCED")), "Potong 20%")
        self.assertEqual(m.saturday_rule(wday(4.5, 35, "BALANCED")), "Potong 40%")
        self.assertEqual(m.saturday_rule(wday(4.5, 25, "LOW")), "Potong 40%")

    def test_long_run_gate_takes_the_strictest(self):  # Uji 3b: §7 passes, light red
        w = wday(6.8, 65, "LOW")
        self.assertEqual(m.long_run_gate(w, "merah"), "Lari santai ≤8 km atau istirahat")
        self.assertEqual(m.long_run_gate(wday(5.6, 70, "BALANCED"), "hijau"), "Potong 20%")
        self.assertEqual(m.long_run_gate(wday(7, 70, "BALANCED"), "oranye"), "Potong 40%")


class ScoreTest(unittest.TestCase):
    def test_score(self):
        a = {"km_pct": .99, "lr_pct": 1.02, "sleep_pct": 1.03, "green": 6}
        b = {"km_pct": .94, "lr_pct": 1.03, "sleep_pct": .90, "green": 6}
        s = m.score(a, b)
        self.assertEqual((s["a"], s["b"]), (2, 1))
        self.assertIsNone(s["cats"][3]["win"])


if __name__ == "__main__":
    unittest.main()


class WatchSpeedTest(unittest.TestCase):
    """docs §5 / §6 (versi 10 Nov): strides and decoupling read the watch's speed when the stream has it."""
    def stream(self, sp):
        t = list(range(len(sp)))
        d, x = [], 0.0
        for v in sp:
            d.append(round(x, 1))
            x += v
        return {"t": t, "d": d, "hr": [150] * len(sp), "sp": sp}

    def test_strides_need_six_seconds_above_2_6(self):
        sp = [2.4] * 30 + [3.2] * 19 + [1.2] * 60 + [3.4] * 5 + [1.2] * 60 + [3.6] * 16 + [1.2] * 10
        st = m.strides(self.stream(sp))
        self.assertEqual([s[1] for s in st], [19, 16])            # the 5-second burst is not a stride
        self.assertEqual(st[1][2], 3.6)
        self.assertIsNone(m.strides({"t": [0, 1], "d": [0, 3]}))  # no watch speed: not guessed from distance

    def test_decoupling_uses_watch_speed(self):
        n = 3600
        s = {"t": list(range(n)), "d": [i * 2.5 for i in range(n)], "hr": [140 if i < n // 2 else 150 for i in range(n)]}
        plain = m.decoupling_detail(dict(s))
        s["sp"] = [2.5 if i < n // 2 else 2.7 for i in range(n)]   # the watch saw a faster 2nd half
        watch = m.decoupling_detail(s)
        self.assertNotEqual(plain["full"], watch["full"])
