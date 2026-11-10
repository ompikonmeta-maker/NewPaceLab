import csv
import datetime as dt
import importlib.util
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

from mock_garmin import demo_program, make_server  # noqa: E402
from pacelab.garmin import Client  # noqa: E402
from pacelab.sync import Syncer  # noqa: E402

TODAY = dt.date(2026, 10, 30)
DAY = dt.date(2026, 10, 27)


class ExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = make_server(today=TODAY)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_port
        cls.tmp = Path(tempfile.mkdtemp())
        spec = importlib.util.spec_from_file_location("cli", ROOT / "pacelab.py")
        cls.cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cli)
        cls.cfg = cls.cli.load_config(ROOT / "config.json")
        keys = cls.tmp / "keys"
        keys.mkdir()
        for a, k in (("TAOFIK", "demo-taofik"), ("REZA", "demo-reza")):
            (keys / ("%s.key" % a)).write_text(k)
            c = Client(a, k, base=cls.base, cache_dir=str(cls.tmp / "tok"), delay=0, log=lambda *x: None)
            Syncer(c, cls.tmp / "data" / a, log=lambda *x: None).run(dt.date(2026, 10, 1), TODAY)
        cls.cfg.update(keys_dir=str(keys), data_dir=str(cls.tmp / "data"))
        cls.ath = [dict(a, program=demo_program()) for a in cls.cfg["athletes"]]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def run_export(self, **kw):
        import os
        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            buf = io.StringIO()
            import contextlib
            with contextlib.redirect_stdout(buf):
                out = self.cli.cmd_ekspor(self.cfg, self.ath, DAY, base=self.base, **kw)
            return zipfile.ZipFile(self.tmp / out), buf.getvalue()
        finally:
            os.chdir(cwd)

    def test_zip_has_summary_csv_laps_and_fit(self):
        z, out = self.run_export()
        names = set(z.namelist())
        for n in ("ringkasan.md", "taofik_per_detik.csv", "taofik_lap.csv", "taofik_asli.fit",
                  "reza_per_detik.csv", "reza_lap.csv", "reza_asli.fit"):
            self.assertIn(n, names)
        md = z.read("ringkasan.md").decode("utf-8")
        for s in ("# Sesi lari — Selasa 27 Okt 2026", "## Taofik", "## Reza", "Ringkasan Garmin", "Lap jam", "Per km",
                  "Kondisi pagi", "Zona HR: Z1 < 133", "Minggu MS19"):
            self.assertIn(s, md)
        self.assertNotIn("demo-taofik", md + out)                              # never a key
        rows = list(csv.reader(io.StringIO(z.read("taofik_per_detik.csv").decode())))
        self.assertEqual(rows[0], ["detik", "jarak_m", "hr_bpm", "kecepatan_m_s", "pace_per_km", "cadence_spm", "elevasi_m", "suhu_c"])
        self.assertGreater(len(rows), 100)
        self.assertNotIn("lat", ",".join(rows[0]))                                 # no GPS in the CSV
        self.assertEqual(z.read("taofik_asli.fit")[8:12], b".FIT")
        laps = list(csv.reader(io.StringIO(z.read("taofik_lap.csv").decode())))
        self.assertEqual(laps[-1][-1], "akhir")

    def test_without_fit(self):
        z, _ = self.run_export(with_fit=False)
        self.assertFalse([n for n in z.namelist() if n.endswith(".fit")])
        self.assertIn("taofik_lap.csv", z.namelist())                             # laps from the local copy

    def test_day_without_runs(self):
        import os
        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                out = self.cli.cmd_ekspor(self.cfg, self.ath, dt.date(2026, 10, 28), base=self.base)
            z = zipfile.ZipFile(self.tmp / out)
        finally:
            os.chdir(cwd)
        self.assertEqual(z.namelist(), ["ringkasan.md"])
        self.assertIn("Tidak ada lari tercatat", z.read("ringkasan.md").decode())
