import json
import unittest
from pathlib import Path


class DataIntegrityTest(unittest.TestCase):
    def test_recipe_seed_has_hundred_rows(self):
        path = Path("data/recipes.jsonl")
        if not path.exists():
            self.skipTest("Local seed data is not present in this checkout.")
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 100)
        for row in rows:
            self.assertTrue(Path(row["workflow_file"]).exists(), row["workflow_file"])

    def test_workflow_files_are_present(self):
        workflow_dir = Path("data/workflows")
        if not workflow_dir.exists():
            self.skipTest("Local workflow data is not present in this checkout.")
        workflow_files = list(workflow_dir.glob("*.jsonl"))
        self.assertEqual(len(workflow_files), 100)


if __name__ == "__main__":
    unittest.main()
