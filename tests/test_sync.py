import contextlib
import datetime as dt
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

from mock_garmin import make_server  # noqa: E402
from pacelab.garmin import AuthError, Client  # noqa: E402
from pacelab.sync import Syncer, key_tree, norm_bb, norm_daily, norm_hrv, norm_sleep, norm_stream, rhr_by_date  # noqa: E402

TODAY = dt.date(2026, 10, 27)


class SyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = make_server(today=TODAY)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_port

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def client(self, key="demo-reza"):
        return Client("REZA", key, base=self.base, cache_dir=str(self.tmp / "tok"), delay=0, log=lambda *a: None)

    def test_full_then_incremental(self):
        out = self.tmp / "REZA"
        r1 = Syncer(self.client(), out, log=lambda *a: None).run(dt.date(2026, 9, 1), TODAY)
        self.assertGreater(r1["new_runs"], 20)
        self.assertEqual(r1["unavailable"], [])
        runs = json.loads((out / "runs.json").read_text())
        self.assertEqual(len(runs), r1["runs"])
        self.assertEqual(len(list((out / "streams").glob("*.json"))), len(runs))
        well = json.loads((out / "wellness.json").read_text())
        day = well["2026-10-20"]
        for k in ("sleep_s", "hrv", "hrv_status", "bb", "rhr"):
            self.assertIn(k, day)
        s = json.loads(next((out / "streams").glob("*.json")).read_text())
        self.assertTrue(s["cad"] and 150 < sorted(c for c in s["cad"] if c)[len(s["cad"]) // 2] < 190)
        self.assertTrue(s["el"])
        r2 = Syncer(self.client(), out, log=lambda *a: None).run(dt.date(2026, 9, 1), TODAY)
        self.assertEqual(r2["new_runs"], 0)
        self.assertLess(r2["requests"], 15)

    def test_fit_gives_laps_and_fills_old_runs(self):
        out = self.tmp / "REZA"
        Syncer(self.client(), out, log=lambda *a: None).run(TODAY - dt.timedelta(days=150), TODAY)
        runs = json.loads((out / "runs.json").read_text())
        old = [r for r in runs if r["date"] < (TODAY - dt.timedelta(days=120)).isoformat()]
        self.assertTrue(old)
        for r in runs:   # every run has laps from its FIT file and per-second data (old ones only from the FIT)
            self.assertTrue((out / "laps" / ("%s.json" % r["id"])).is_file())
            self.assertTrue((out / "streams" / ("%s.json" % r["id"])).is_file())
        s = json.loads((out / "streams" / ("%s.json" % old[0]["id"])).read_text())
        self.assertEqual(s["keys"], ["fit"])
        self.assertAlmostEqual(s["d"][-1] / 1000, old[0]["km"], delta=.05)
        lp = json.loads((out / "laps" / ("%s.json" % runs[-1]["id"])).read_text())["laps"]
        self.assertAlmostEqual(sum(l["km"] for l in lp), runs[-1]["km"], delta=.05)
        self.assertEqual(lp[-1]["trigger"], "session_end")
        self.assertIn("hr_max", runs[-1]["g"])
        self.assertIn("te_aer", runs[-1]["g"])
        tempo = [r for r in runs if r["g"].get("te_label") == "TEMPO"]
        self.assertIn("manual", [l["trigger"] for l in json.loads((out / "laps" / ("%s.json" % tempo[-1]["id"])).read_text())["laps"]])

    def test_old_streams_downloaded_once_more_for_cadence(self):
        out = self.tmp / "REZA"
        Syncer(self.client(), out, log=lambda *a: None).run(dt.date(2026, 10, 1), TODAY)
        st = json.loads((out / "state.json").read_text())
        st["stream_v"] = 1  # as written by the previous version
        (out / "state.json").write_text(json.dumps(st))
        n = len(list((out / "streams").glob("*.json")))
        r = Syncer(self.client(), out, log=lambda *a: None).run(dt.date(2026, 10, 1), TODAY)
        self.assertEqual(r["new_runs"], n)
        self.assertEqual(Syncer(self.client(), out, log=lambda *a: None).run(dt.date(2026, 10, 1), TODAY)["new_runs"], 0)

    def test_bad_key_message_has_no_key(self):
        secret = "SANGAT-RAHASIA-123"
        with self.assertRaises(AuthError) as cm:
            self.client(secret).token()
        self.assertNotIn(secret, str(cm.exception))
        self.assertIn("REZA", str(cm.exception))
        self.assertNotIn(secret, repr(self.client(secret)))

    def test_cli_continues_after_bad_key(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("cli", ROOT / "pacelab.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        cfg = cli.load_config(ROOT / "config.json")
        cfg["data_dir"] = str(self.tmp / "data")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = cli.cmd_sync(cfg, cfg["athletes"], dt.date(2026, 10, 1), base=self.base,
                              keys={"TAOFIK": "KUNCI-SALAH-XYZ", "REZA": "demo-reza"}, delay=0)
        out = buf.getvalue()
        self.assertFalse(ok)
        self.assertIn("Key TAOFIK", out)
        self.assertNotIn("KUNCI-SALAH-XYZ", out)
        self.assertIn("[Reza] sync", out)
        self.assertTrue((self.tmp / "data" / "REZA" / "runs.json").is_file())


    def test_inspect_reports_lap_endpoints_without_values(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("cli", ROOT / "pacelab.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        cfg = cli.load_config(ROOT / "config.json")
        keys = self.tmp / "keys_i"
        keys.mkdir(exist_ok=True)
        (keys / "REZA.key").write_text("demo-reza", encoding="utf-8")
        cfg.update(keys_dir=str(keys), data_dir=str(self.tmp / "data_i"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.cmd_inspect(cfg, [a for a in cfg["athletes"] if a["id"] == "REZA"], base=self.base)
        out = buf.getvalue()
        for n in ("lari: daftar aktivitas", "lari: data per detik", "lari: file FIT: BOLEH", "lari: ringkasan",
                  "lari: splits", "lari: typedsplits", "lari: split_summaries"):
            self.assertIn(n, out)
        self.assertNotIn("demo-reza", out)

    def test_check_lists_runs_without_per_second_data(self):
        from pacelab.check import report
        d = self.tmp / "chk"
        (d / "streams").mkdir(parents=True, exist_ok=True)
        (d / "runs.json").write_text(json.dumps([{"id": 1, "date": "2026-10-01", "km": 5.0, "type": "running"},
                                                 {"id": 2, "date": "2026-10-02", "km": 6.2, "type": "treadmill_running"}]))
        (d / "wellness.json").write_text("{}")
        (d / "streams" / "1.json").write_text(json.dumps({"t": [0], "d": [0], "keys": []}))
        (d / "state.json").write_text(json.dumps({"no_stream": [2]}))
        out = report(d, "X")
        self.assertIn("tanpa data per detik (1)", out)
        self.assertIn("2026-10-02", out)
        self.assertIn("treadmill_running", out)
        self.assertIn("Garmin: tidak ada detail", out)
        self.assertNotIn("2026-10-01   ", out)


class SchemaTest(unittest.TestCase):
    def test_old_schema_rereads_wellness_once(self):
        srv = make_server(today=TODAY)
        tmp = Path(tempfile.mkdtemp())
        c = Client("REZA", "demo-reza", base="http://127.0.0.1:%d" % srv.server_port,
                   cache_dir=str(tmp / "tok"), delay=0, log=lambda *a: None)
        Syncer(c, tmp / "R", log=lambda *a: None).run(dt.date(2026, 9, 1), TODAY)
        st = json.loads((tmp / "R" / "state.json").read_text())
        st.pop("schema")
        (tmp / "R" / "state.json").write_text(json.dumps(st))
        self.assertEqual(Syncer(c, tmp / "R", log=lambda *a: None).run(dt.date(2026, 9, 1), TODAY)["wellness_days"], 57)
        self.assertEqual(Syncer(c, tmp / "R", log=lambda *a: None).run(dt.date(2026, 9, 1), TODAY)["wellness_days"], 4)
        srv.shutdown()
        srv.server_close()


class NoStreamTest(unittest.TestCase):
    def test_missing_details_asked_once(self):
        srv = make_server(today=TODAY)
        tmp = Path(tempfile.mkdtemp())
        c = Client("REZA", "demo-reza", base="http://127.0.0.1:%d" % srv.server_port,
                   cache_dir=str(tmp / "tok"), delay=0, log=lambda *a: None)
        s1 = Syncer(c, tmp / "R", log=lambda *a: None)
        orig = s1.c.get
        s1.c.get = lambda path, params=None, **kw: None if "/details" in path else orig(path, params, **kw)
        r1 = s1.run(dt.date(2026, 10, 1), TODAY)
        self.assertGreater(r1["new_runs"], 0)
        s2 = Syncer(c, tmp / "R", log=lambda *a: None)
        s2.c.get = s1.c.get
        self.assertEqual(s2.run(dt.date(2026, 10, 1), TODAY)["new_runs"], 0)
        srv.shutdown()
        srv.server_close()


class NormalizeTest(unittest.TestCase):
    def test_stream_from_timestamps(self):
        det = {"metricDescriptors": [{"metricsIndex": 0, "key": "directTimestamp"},
                                     {"metricsIndex": 1, "key": "sumDistance"},
                                     {"metricsIndex": 2, "key": "directHeartRate"}],
               "activityDetailMetrics": [{"metrics": [1000000, 0, 120]}, {"metrics": [1005000, 15, 125]},
                                         {"metrics": [1010000, 31, None]}]}
        s = norm_stream(det)
        self.assertEqual(s["t"], [0, 5, 10])
        self.assertEqual(s["d"], [0, 15, 31])
        self.assertEqual(s["hr"], [120, 125, None])
        self.assertIsNone(s["cad"])

    def test_stream_cadence_one_leg_is_doubled(self):
        det = {"metricDescriptors": [{"metricsIndex": 0, "key": "sumDuration"}, {"metricsIndex": 1, "key": "sumDistance"},
                                     {"metricsIndex": 2, "key": "directRunCadence"}, {"metricsIndex": 3, "key": "directElevation"}],
               "activityDetailMetrics": [{"metrics": [0, 0, 84, 10.0]}, {"metrics": [5, 15, 86, 10.5]}, {"metrics": [10, 31, 85, 11.2]}]}
        s = norm_stream(det)
        self.assertEqual(s["cad"], [168, 172, 170])
        self.assertEqual(s["el"], [10.0, 10.5, 11.2])

    def test_rhr_shapes(self):
        self.assertEqual(rhr_by_date({"data": [{"calendarDate": "2026-10-26", "restingHeartRate": 52}]}),
                         {"2026-10-26": 52})
        self.assertEqual(rhr_by_date({"data": {"2026-10-26": {"restingHeartRateValue": 53}}}), {"2026-10-26": 53})
        self.assertEqual(rhr_by_date([{"date": "2026-10-25", "wellness": {"rhr": 54, "maxHeartRate": 150}}]),
                         {"2026-10-25": 54})
        self.assertEqual(rhr_by_date({"data": [{"calendarDate": "2026-10-26", "restingHeartRate": 0}]}), {})

    def test_sleep_rhr_and_hrv_none(self):
        _, v = norm_sleep({"calendarDate": "2026-10-26", "sleepTimeSeconds": 22000, "restingHeartRate": 51})
        self.assertEqual((v["sleep_s"], v["rhr_sleep"]), (22000, 51))
        self.assertIsNone(norm_hrv({"calendarDate": "2026-10-26", "status": "NONE"})[1]["hrv_status"])

    def test_daily_summary_real_shape(self):
        # field paths reported by `pacelab.py inspect` on a real account (2026-10-28)
        item = {"calendarDate": "2026-10-27", "heartRate": {"minValue": 48, "maxValue": 171, "restingValue": 52},
                "bodyBattery": {"minValue": 12, "maxValue": 78, "chargedValue": 55, "latestValue": 40}}
        self.assertEqual(norm_daily(item), ("2026-10-27", {"rhr": 52, "bb": 78}))

    def test_bb_report_without_values_is_not_charged(self):
        self.assertIsNone(norm_bb({"date": "2026-10-27", "charged": 55, "drained": 60})[1]["bb"])

    def test_key_tree_has_no_values(self):
        tree = key_tree({"data": {"2026-10-26": {"restingHeartRate": 52, "x": [{"y": "rahasia"}]}}})
        self.assertEqual(tree, [("data.<tanggal>.restingHeartRate", "int"), ("data.<tanggal>.x[].y", "str")])
        self.assertNotIn("rahasia", str(tree))

    def test_stream_missing_distance(self):
        self.assertIsNone(norm_stream({"metricDescriptors": [{"metricsIndex": 0, "key": "sumDuration"}],
                                       "activityDetailMetrics": [{"metrics": [1]}, {"metrics": [2]}]}))


if __name__ == "__main__":
    unittest.main()
