import importlib
import os
import sys
import tempfile
import unittest
import uuid
from datetime import date
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"
sys.path.insert(0, str(SRC))


def _player(name, offense=3, distribution=3, defense=3, injury_handicap=0.0, player_id=None):
    return {
        "id": player_id or str(uuid.uuid4()),
        "name": name,
        "offense": offense,
        "distribution": distribution,
        "defense": defense,
        "injury_handicap": injury_handicap,
    }


class GameHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_data_dir = os.environ.get("DATA_DIR")
        os.environ["DATA_DIR"] = self.tempdir.name
        sys.modules.pop("game_history", None)

    def tearDown(self):
        if self.previous_data_dir is None:
            os.environ.pop("DATA_DIR", None)
        else:
            os.environ["DATA_DIR"] = self.previous_data_dir
        self.tempdir.cleanup()

    def _module(self):
        return importlib.import_module("game_history")

    def test_save_game_returns_id_and_winner(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        game = game_history.save_game(date(2026, 1, 1), [alice], [bob], 3, 1)
        self.assertTrue(game["id"])
        self.assertEqual(game["winner"], 1)
        self.assertEqual(game["date"], "2026-01-01")

    def test_save_game_tie_has_no_winner(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        game = game_history.save_game(date(2026, 1, 1), [alice], [bob], 2, 2)
        self.assertIsNone(game["winner"])

    def test_list_games_orders_newest_first(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        game_history.save_game(date(2026, 1, 1), [alice], [bob], 1, 0)
        game_history.save_game(date(2026, 3, 1), [alice], [bob], 2, 0)
        game_history.save_game(date(2026, 2, 1), [alice], [bob], 3, 0)
        games = game_history.list_games()
        self.assertEqual([g["date"] for g in games], ["2026-03-01", "2026-02-01", "2026-01-01"])

    def test_get_game_round_trips_and_unknown_id_is_none(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        saved = game_history.save_game(date(2026, 1, 1), [alice], [bob], 1, 0)
        fetched = game_history.get_game(saved["id"])
        self.assertEqual(fetched["id"], saved["id"])
        self.assertIsNone(game_history.get_game(str(uuid.uuid4())))

    def test_update_game_changes_score_and_date_but_not_rosters(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        saved = game_history.save_game(date(2026, 1, 1), [alice], [bob], 1, 0)
        updated = game_history.update_game(saved["id"], date(2026, 1, 2), 5, 5)
        self.assertEqual(updated["date"], "2026-01-02")
        self.assertEqual(updated["score1"], 5)
        self.assertEqual(updated["score2"], 5)
        self.assertEqual(updated["team1_players"], saved["team1_players"])
        self.assertEqual(updated["team2_players"], saved["team2_players"])

    def test_delete_game_removes_it(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        saved = game_history.save_game(date(2026, 1, 1), [alice], [bob], 1, 0)
        game_history.delete_game(saved["id"])
        self.assertIsNone(game_history.get_game(saved["id"]))
        self.assertEqual(game_history.list_games(), [])

    def test_add_and_delete_note(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        saved = game_history.save_game(date(2026, 1, 1), [alice], [bob], 1, 0)
        game = game_history.add_note(saved["id"], "Great game", author="Mike")
        self.assertEqual(len(game["notes"]), 1)
        note_id = game["notes"][0]["id"]
        game = game_history.delete_note(saved["id"], note_id)
        self.assertEqual(game["notes"], [])

    def test_add_note_rejects_blank_text(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        saved = game_history.save_game(date(2026, 1, 1), [alice], [bob], 1, 0)
        with self.assertRaises(ValueError):
            game_history.add_note(saved["id"], "   ")

    def test_save_game_rejects_score_out_of_range(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        with self.assertRaises(ValueError):
            game_history.save_game(date(2026, 1, 1), [alice], [bob], 100, 0)

    def test_save_game_rejects_goal_out_of_range(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        with self.assertRaises(ValueError):
            game_history.save_game(
                date(2026, 1, 1), [alice], [bob], 1, 0, {alice["id"]: 21}
            )

    def test_save_game_rejects_goal_for_unknown_player(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        with self.assertRaises(ValueError):
            game_history.save_game(
                date(2026, 1, 1), [alice], [bob], 1, 0, {"not-a-player": 1}
            )

    def test_save_game_rejects_empty_roster(self):
        game_history = self._module()
        bob = _player("Bob")
        with self.assertRaises(ValueError):
            game_history.save_game(date(2026, 1, 1), [], [bob], 1, 0)

    def test_save_game_rejects_malformed_snapshot_entry(self):
        game_history = self._module()
        bob = _player("Bob")
        with self.assertRaises(ValueError):
            game_history.save_game(date(2026, 1, 1), [{"name": "Alice"}], [bob], 1, 0)

    def test_player_goals_defaults_to_zero(self):
        game_history = self._module()
        alice = _player("Alice")
        bob = _player("Bob")
        saved = game_history.save_game(date(2026, 1, 1), [alice], [bob], 1, 0)
        self.assertEqual(game_history.player_goals(saved, alice["id"]), 0)


if __name__ == "__main__":
    unittest.main()
