import unittest
from unittest.mock import patch

import scripts.bootstrap_db as bootstrap_db


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.executed = []

    def execute(self, query):
        self.executed.append(query)

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.cursor_instance = FakeCursor(row)

    def cursor(self):
        return self.cursor_instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class BootstrapDbTest(unittest.TestCase):
    def test_database_has_seed_data_requires_recipes_and_workflows(self):
        with patch.object(bootstrap_db, "connect", return_value=FakeConnection((True, True))):
            self.assertTrue(bootstrap_db.database_has_seed_data("postgresql://example"))

        with patch.object(bootstrap_db, "connect", return_value=FakeConnection((True, False))):
            self.assertFalse(bootstrap_db.database_has_seed_data("postgresql://example"))

    def test_bootstrap_database_skips_seed_when_data_exists(self):
        with patch.object(bootstrap_db, "migrate_main") as migrate_main, \
             patch.object(bootstrap_db, "seed_main") as seed_main, \
             patch.object(bootstrap_db, "validate_main") as validate_main, \
             patch.object(bootstrap_db, "database_has_seed_data", return_value=True):
            seeded = bootstrap_db.bootstrap_database("postgresql://example")

        self.assertFalse(seeded)
        migrate_main.assert_called_once_with()
        seed_main.assert_not_called()
        validate_main.assert_called_once_with()

    def test_bootstrap_database_seeds_when_data_missing(self):
        with patch.object(bootstrap_db, "migrate_main") as migrate_main, \
             patch.object(bootstrap_db, "seed_main") as seed_main, \
             patch.object(bootstrap_db, "validate_main") as validate_main, \
             patch.object(bootstrap_db, "database_has_seed_data", return_value=False):
            seeded = bootstrap_db.bootstrap_database("postgresql://example")

        self.assertTrue(seeded)
        migrate_main.assert_called_once_with()
        seed_main.assert_called_once_with()
        validate_main.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
