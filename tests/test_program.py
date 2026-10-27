import unittest
from pathlib import Path

from pacelab.program import load_program, parse_date, parse_duration, parse_times

FIX = Path(__file__).parent / "fixtures" / "program_mini.xlsx"


class ParseTest(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(parse_date("03 Agu 2026").isoformat(), "2026-08-03")
        self.assertEqual(parse_date("Sab 22 Agu 2026").isoformat(), "2026-08-22")
        self.assertEqual(parse_date("MINGGU 13 JUN 2027").isoformat(), "2027-06-13")
        self.assertEqual(parse_date("Minggu 13 Juni 2027").isoformat(), "2027-06-13")
        self.assertEqual(parse_date(46237).isoformat(), "2026-08-03")
        self.assertIsNone(parse_date("-"))

    def test_times_and_durations(self):
        self.assertEqual(parse_times("4:45:00 - 5:15:00"), [17100, 18900])
        self.assertEqual(parse_times("5:30 - 5:45"), [19800, 20700])
        self.assertEqual(parse_duration("6 jam 15 menit"), 22500)
        self.assertEqual(parse_duration("7 jam"), 25200)


class ProgramTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = load_program(FIX)

    def test_dates(self):
        self.assertEqual(self.p["ms1"], "2026-06-22")  # MS7 = 3 Aug -> MS1 six weeks earlier
        self.assertEqual(self.p["race_date"], "2027-06-13")

    def test_weeks(self):
        w = {x["ms"]: x for x in self.p["weeks"]}
        self.assertEqual((w[7]["km"], w[7]["lr"], w[7]["phase"]), (28, 14, "Base"))
        self.assertIsNone(w[9]["lr"])
        self.assertTrue(w[8]["down"])
        self.assertTrue(w[9]["event"])
        self.assertFalse(w[10]["down"], "grey row whose note says it is no longer a down week")

    def test_targets(self):
        t = self.p["target"]
        self.assertEqual((t["A"]["lo"], t["A"]["hi"]), (None, 17100))
        self.assertEqual((t["B"]["lo"], t["B"]["hi"]), (17100, 18900))
        self.assertEqual(self.p["sleep"], {"min": 23400, "before_lr": 25200})

    def test_weight_ignores_trailing_example(self):
        self.assertEqual([(x["ms"], x["kg"]) for x in self.p["weight"]], [(7, 81.3), (8, 81.0)])


if __name__ == "__main__":
    unittest.main()
