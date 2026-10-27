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
from pacelab.sync import Syncer, norm_stream  # noqa: E402

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
        r2 = Syncer(self.client(), out, log=lambda *a: None).run(dt.date(2026, 9, 1), TODAY)
        self.assertEqual(r2["new_runs"], 0)
        self.assertLess(r2["requests"], 15)

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

    def test_stream_missing_distance(self):
        self.assertIsNone(norm_stream({"metricDescriptors": [{"metricsIndex": 0, "key": "sumDuration"}],
                                       "activityDetailMetrics": [{"metrics": [1]}, {"metrics": [2]}]}))


if __name__ == "__main__":
    unittest.main()
