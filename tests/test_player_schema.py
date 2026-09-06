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

    def _legacy_database_with_duplicate_names(self):
        """A pre-F-006 database that already violates live-name uniqueness."""
        self._legacy_database()
        connection = sqlite3.connect(Path(self.tempdir.name) / "player_database.db")
        connection.execute(
            """
            INSERT INTO players
                (name, distribution_score, offense_score, defense_score, modifier, notes)
            VALUES ('Marcel', 3, 3, 3, 0.0, ''), ('marcel', 3, 3, 3, 0.6, 'good passing')
            """
        )
        connection.commit()
        connection.close()

    def _database(self):
        return importlib.import_module("player_database")

    def test_duplicate_names_do_not_abort_the_migration(self):
        # Real rosters predate the uniqueness rule. Creating the unique index
        # regardless raises inside the migration transaction, which runs at
        # import and would take the whole app down rather than just refusing
        # the index.
        self._legacy_database_with_duplicate_names()
        database = self._database()

        self.assertEqual(database.DUPLICATE_LIVE_NAMES, ["marcel"])
        self.assertEqual(len(database.list_players()), 3)

        connection = sqlite3.connect(Path(self.tempdir.name) / "player_database.db")
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
        connection.close()
        # Deferred, not silently created against violating data.
        self.assertNotIn("players_live_name_unique", indexes)

    def _index_exists(self, name):
        connection = sqlite3.connect(Path(self.tempdir.name) / "player_database.db")
        found = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
        connection.close()
        return name in found

    def test_merge_folds_loser_into_winner_and_restores_the_index(self):
        self._legacy_database_with_duplicate_names()
        database = self._database()
        self.assertEqual(database.DUPLICATE_LIVE_NAMES, ["marcel"])
        self.assertFalse(self._index_exists("players_live_name_unique"))

        marcels = [p for p in database.list_players() if p["name"].lower() == "marcel"]
        winner = next(p for p in marcels if p["notes"] == "good passing")
        loser = next(p for p in marcels if p["id"] != winner["id"])

        merged = database.merge_players(winner["id"], loser["id"])

        # Winner keeps its identity and its ratings.
        self.assertEqual(merged["id"], winner["id"])
        self.assertEqual(merged["notes"], "good passing")
        # The loser is redirected, not erased.
        self.assertIn(loser["id"], merged["merged_from"])
        # Identical names must not become a self-alias.
        self.assertEqual(merged["aliases"], [])

        live = database.list_players()
        self.assertEqual(len([p for p in live if p["name"].lower() == "marcel"]), 1)
        # Tombstoned, so it no longer reads as a live player...
        self.assertIsNone(database.get_player(loser["id"]))
        # ...but the record survives, carrying the deletion timestamp that lets
        # the merge propagate to other devices.
        archived = database.list_players(include_deleted=True)
        tombstoned = next(p for p in archived if p["id"] == loser["id"])
        self.assertIsNotNone(tombstoned["deleted_at"])

        # Resolving the last duplicate reinstates the constraint by itself.
        self.assertEqual(database.DUPLICATE_LIVE_NAMES, [])
        self.assertTrue(self._index_exists("players_live_name_unique"))

    def test_merge_keeps_a_differing_name_as_an_alias(self):
        self._legacy_database()
        database = self._database()
        winner = database.add_player("Sam Rodriguez", 3, 3, 3)
        loser = database.add_player("Sam R", 3, 3, 3)

        merged = database.merge_players(winner["id"], loser["id"])

        self.assertEqual(merged["aliases"], ["Sam R"])
        self.assertEqual(merged["merged_from"], [loser["id"]])

    def test_merge_rejects_self_and_tombstoned_records(self):
        self._legacy_database()
        database = self._database()
        a = database.add_player("Ana", 3, 3, 3)
        b = database.add_player("Ben", 3, 3, 3)

        with self.assertRaises(ValueError):
            database.merge_players(a["id"], a["id"])

        database.delete_player(b["id"])
        with self.assertRaises(ValueError):
            database.merge_players(a["id"], b["id"])

    def test_unique_index_is_created_when_no_duplicates_exist(self):
        self._legacy_database()
        database = self._database()

        self.assertEqual(database.DUPLICATE_LIVE_NAMES, [])

        connection = sqlite3.connect(Path(self.tempdir.name) / "player_database.db")
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
        connection.close()
        self.assertIn("players_live_name_unique", indexes)

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

    def test_restore_uses_canonical_record_order_for_equal_timestamps(self):
        database = self._database()
        player = database.add_player("Player One", 3, 4, 2)
        canonical_winner = dict(player)
        canonical_winner["name"] = "Zebra"

        self.assertEqual(database.restore_players([canonical_winner]), (0, 1))
        self.assertEqual(database.get_player(player["id"])["name"], "Zebra")


if __name__ == "__main__":
    unittest.main()
