import datetime as dt
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

from mock_garmin import make_server  # noqa: E402
from pacelab.build import build  # noqa: E402
from pacelab.garmin import Client  # noqa: E402
from pacelab.sync import Syncer  # noqa: E402

FIX = str(ROOT / "tests" / "fixtures" / "program_mini.xlsx")
TODAY = dt.date(2026, 8, 26)


def payload(html):
    m = re.search(r"const DATA = (\{.*?\});\n", html, re.S)
    return json.loads(m.group(1))


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        srv = make_server(today=TODAY)
        base = "http://127.0.0.1:%d" % srv.server_port
        for aid, key in (("A", "demo-taofik"), ("B", "demo-reza")):
            c = Client(aid, key, base=base, cache_dir=str(cls.tmp / "tok"), delay=0, log=lambda *a: None)
            Syncer(c, cls.tmp / "data" / aid, log=lambda *a: None).run(dt.date(2026, 6, 1), TODAY)
        srv.shutdown()
        srv.server_close()
        cls.athletes = [{"id": "A", "name": "Satu", "program": FIX}, {"id": "B", "name": "Dua", "program": FIX}]

    def test_build_with_data(self):
        cfg = {"data_dir": str(self.tmp / "data")}
        html = build(cfg, self.athletes, TODAY, self.tmp / "out.html").read_text(encoding="utf-8")
        self.assertNotIn("/*__DATA__*/null", html)
        self.assertNotRegex(html, r"https?://(?!www\.w3\.org)")  # no network requests
        d = payload(html)
        self.assertEqual(d["ms_cur"], 10)
        self.assertEqual(d["race_date"], "2027-06-13")
        a = d["athletes"][0]
        self.assertEqual(a["c"], "t")
        self.assertTrue(a["has_data"])
        self.assertGreater(a["longest"], 5)
        self.assertEqual(len(a["days"]), 60)
        self.assertEqual(len(a["badges"]), 9)
        self.assertIn(a["today"]["light"]["level"], ("hijau", "kuning", "oranye", "merah"))
        self.assertTrue(a["pb"]["5K"])
        # every effort ships, not only the record staircase; the fastest effort is the last record
        self.assertGreaterEqual(len(a["eff"]["5K"]), len(a["pb"]["5K"]))
        self.assertEqual(min(sec for _, sec in a["eff"]["5K"]), a["pb"]["5K"][-1]["sec"])
        self.assertIsNotNone(d["score"])
        s = max(a["sessions"], key=lambda x: x["km"])
        self.assertEqual(len(s["splits"]), int(s["km"]) + (s["km"] % 1 >= .3))
        self.assertIsNotNone(s["dec"])
        km, sec, hr, cad, el = s["splits"][0]
        self.assertTrue(km and sec and hr and cad and el is not None)

    def test_profile_pace_and_coach_thresholds(self):
        cfg = {"data_dir": str(self.tmp / "data"), "coach": {"km": [0.95, 1.10], "tol_s": 5}}
        ath = [dict(self.athletes[0], pace={"easy": ["8:40", "9:15"], "hr_leads": True}, coach={"tol_s": 3}), self.athletes[1]]
        d = payload(build(cfg, ath, TODAY, self.tmp / "out2.html").read_text(encoding="utf-8"))
        a, b = d["athletes"]
        self.assertEqual(a["pace"], {"easy": [520, 555], "hr_leads": True})
        self.assertEqual(a["coach"], {"km": [0.95, 1.10], "tol_s": 3})   # athlete overrides the shared block
        self.assertEqual(b["coach"], {"km": [0.95, 1.10], "tol_s": 5})
        self.assertIsNone(b["pace"])

    def test_build_without_data(self):
        cfg = {"data_dir": str(self.tmp / "kosong")}
        d = payload(build(cfg, self.athletes, TODAY, self.tmp / "empty.html").read_text(encoding="utf-8"))
        a = d["athletes"][1]
        self.assertFalse(a["has_data"])
        self.assertTrue(all(w["km"] is None for w in a["weeks"]))
        self.assertIsNone(a["today"]["light"])
        self.assertIsNone(d["score"])


if __name__ == "__main__":
    unittest.main()
