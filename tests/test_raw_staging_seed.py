import json
import unittest
from pathlib import Path

from scripts.validate_workflows import validate_directory


class RawStagingSeedTest(unittest.TestCase):
    def test_staging_recipes_match_schema_shape(self):
        recipe_path = Path("data/staging/raw_first_100/recipes.jsonl")
        self.assertTrue(recipe_path.exists(), recipe_path)
        rows = [json.loads(line) for line in recipe_path.read_text().splitlines() if line.strip()]
        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertTrue(row["id"].startswith("raw_"))
            self.assertEqual(row["cuisine"], "Unknown")
            self.assertGreaterEqual(len(row["primary_ingredients"]), 1)
            self.assertLessEqual(len(row["primary_ingredients"]), 3)
            self.assertGreater(len(row["search_keywords"]), 0)
            self.assertLessEqual(len(row["search_keywords"]), 15)
            self.assertTrue(Path(row["workflow_file"]).exists(), row["workflow_file"])

    def test_staging_workflows_validate(self):
        validate_directory(Path("data/staging/raw_first_100/workflows"))

    def test_review_file_exists(self):
        review_path = Path("data/staging/raw_first_100/review.jsonl")
        self.assertTrue(review_path.exists(), review_path)
        rows = [json.loads(line) for line in review_path.read_text().splitlines() if line.strip()]
        for row in rows:
            self.assertIn("row_id", row)
            self.assertIn("title", row)
            self.assertIn("reason", row)
            self.assertIn("raw_title", row)
            self.assertIn("raw_ingredients", row)
            self.assertIn("raw_directions", row)


if __name__ == "__main__":
    unittest.main()
