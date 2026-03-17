import json
import os
import unittest
from pathlib import Path


class DataIntegrityTest(unittest.TestCase):
    def test_seed_files_have_expected_shape(self):
        recipes_path = Path("data/recipes.jsonl")
        workflow_steps_path = Path("data/workflow_steps.jsonl")
        report_path = Path("data/raw_seed_report.json")
        if not recipes_path.exists() or not workflow_steps_path.exists() or not report_path.exists():
            self.skipTest("Local seed data is not present in this checkout.")

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertGreater(report["accepted_rows"], 0)
        self.assertGreater(report["workflow_step_rows"], 0)

        with recipes_path.open(encoding="utf-8") as handle:
            sample_count = 0
            for raw in handle:
                if not raw.strip():
                    continue
                row = json.loads(raw)
                self.assertTrue(bool(row["id"]))
                self.assertTrue(bool(row["title"]))
                self.assertTrue(bool(row["search_keywords"]))
                sample_count += 1
                if sample_count >= 200:
                    break
        self.assertEqual(sample_count, 200)

        with workflow_steps_path.open(encoding="utf-8") as handle:
            sample_count = 0
            for raw in handle:
                if not raw.strip():
                    continue
                row = json.loads(raw)
                self.assertIn("estimated_seconds", row)
                self.assertGreaterEqual(row["estimated_seconds"], 1)
                self.assertLessEqual(row["estimated_seconds"], 10)
                self.assertTrue(bool(row["recipe_id"]))
                sample_count += 1
                if sample_count >= 500:
                    break
        self.assertEqual(sample_count, 500)

    @unittest.skipUnless(os.getenv("RUN_SEED_SMOKE") == "1", "Large seed smoke disabled by default.")
    def test_seed_report_matches_full_file_counts(self):
        recipes_path = Path("data/recipes.jsonl")
        workflow_steps_path = Path("data/workflow_steps.jsonl")
        report_path = Path("data/raw_seed_report.json")
        if not recipes_path.exists() or not workflow_steps_path.exists() or not report_path.exists():
            self.skipTest("Local seed data is not present in this checkout.")

        report = json.loads(report_path.read_text(encoding="utf-8"))
        with recipes_path.open(encoding="utf-8") as handle:
            recipe_rows = sum(1 for raw in handle if raw.strip())
        with workflow_steps_path.open(encoding="utf-8") as handle:
            workflow_rows = sum(1 for raw in handle if raw.strip())

        self.assertEqual(recipe_rows, report["accepted_rows"])
        self.assertEqual(workflow_rows, report["workflow_step_rows"])


if __name__ == "__main__":
    unittest.main()
