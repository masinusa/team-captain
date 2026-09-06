import importlib
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"
sys.path.insert(0, str(SRC))


class PlayerSchemaTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_data_dir = os.environ.get("DATA_DIR")
        os.environ["DATA_DIR"] = self.tempdir.name
        sys.modules.pop("player_database", None)
        sys.modules.pop("backup", None)

    def tearDown(self):
        if self.previous_data_dir is None:
            os.environ.pop("DATA_DIR", None)
        else:
            os.environ["DATA_DIR"] = self.previous_data_dir
        self.tempdir.cleanup()

    def _legacy_database(self):
        connection = sqlite3.connect(Path(self.tempdir.name) / "player_database.db")
        connection.execute(
            """
            CREATE TABLE players (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                distribution_score FLOAT,
                offense_score FLOAT,
                defense_score FLOAT,
                modifier FLOAT,
                notes VARCHAR(500)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO players
                (name, distribution_score, offense_score, defense_score, modifier, notes)
            VALUES ('Legacy player', 3, 4, 2, 0.5, 'migrated')
            """
        )
        connection.commit()
        connection.close()

    def _database(self):
        return importlib.import_module("player_database")

    def test_legacy_rows_get_stable_shared_fields(self):
        self._legacy_database()
        database = self._database()

        first = database.list_players()[0]
        self.assertRegex(first["id"], r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$")
        self.assertEqual(first["aliases"], [])
        self.assertEqual(first["merged_from"], [])
        self.assertIsNone(first["deleted_at"])
        self.assertTrue(first["created_at"].endswith("Z"))
        self.assertEqual(first["created_at"], first["updated_at"])

        sys.modules.pop("player_database", None)
        second = self._database().list_players()[0]
        self.assertEqual(second["id"], first["id"])
        self.assertEqual(second["created_at"], first["created_at"])

    def test_delete_tombstones_and_payload_round_trips(self):
        database = self._database()
        player = database.add_player("Player One", 3, 4, 2, 0.0, "note")
        database.delete_player(player["id"])

        self.assertEqual(database.list_players(), [])
        tombstone = database.list_players(include_deleted=True)[0]
        self.assertIsNotNone(tombstone["deleted_at"])

        backup = importlib.import_module("backup")
        payload = backup.export_payload()
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["games"], [])
        self.assertEqual(payload["players"], [tombstone])

        self.assertEqual(database.restore_players(payload["players"]), (0, 0))

    def test_restore_uses_uuid_and_newer_timestamp(self):
        database = self._database()
        player = database.add_player("Player One", 3, 4, 2)
        older = dict(player)
        older["updated_at"] = "2020-01-01T00:00:00Z"
        newer = dict(player)
        newer["name"] = "Renamed"
        newer["updated_at"] = "2030-01-02T00:00:00Z"

        self.assertEqual(database.restore_players([older]), (0, 0))
        self.assertEqual(database.restore_players([newer]), (0, 1))
        self.assertEqual(database.get_player(player["id"])["name"], "Renamed")


if __name__ == "__main__":
    unittest.main()
