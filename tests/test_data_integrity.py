import json
import unittest
from pathlib import Path


class DataIntegrityTest(unittest.TestCase):
    def test_recipe_seed_has_five_rows(self):
        path = Path("data/recipes.jsonl")
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 5)

    def test_workflow_files_are_present(self):
        workflow_files = list(Path("data/workflows").glob("*.jsonl"))
        self.assertEqual(len(workflow_files), 5)


if __name__ == "__main__":
    unittest.main()
