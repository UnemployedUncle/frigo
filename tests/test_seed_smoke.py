import json
import os
import unittest
from pathlib import Path


@unittest.skipUnless(os.getenv("RUN_SEED_SMOKE") == "1", "Large seed smoke disabled by default.")
class SeedSmokeTest(unittest.TestCase):
    def test_seed_report_and_db_counts_are_sane(self):
        report_path = Path("data/raw_seed_report.json")
        if not report_path.exists():
            self.skipTest("Local seed report is not present in this checkout.")

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertGreater(report["accepted_rows"], 0)
        self.assertGreater(report["workflow_step_rows"], report["accepted_rows"])
        self.assertLess(report["excluded_rows"], 1000)


if __name__ == "__main__":
    unittest.main()
