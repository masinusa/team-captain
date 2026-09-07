import json
import sys
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"
sys.path.insert(0, str(SRC))

from game_review_service import create_game_review_session  # noqa: E402


class _FakeResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class GameReviewServiceTests(unittest.TestCase):
    def _fake_urlopen(self, expected_link="https://example.test/s/abc123"):
        def opener(req, timeout=None):
            self.last_request = req
            body = json.dumps({"link": expected_link}).encode("utf-8")
            return _FakeResponse(body)

        return opener

    def test_bare_game_date_when_no_bundle_given(self):
        with patch("game_review_service.urlrequest.urlopen", self._fake_urlopen()):
            link = create_game_review_session("https://service.test", date(2026, 1, 1))
        self.assertEqual(link, "https://example.test/s/abc123")
        payload = json.loads(self.last_request.data)
        self.assertEqual(payload, {"game_date": "2026-01-01"})

    def test_full_bundle_sent_when_all_four_given(self):
        with patch("game_review_service.urlrequest.urlopen", self._fake_urlopen()):
            create_game_review_session(
                "https://service.test",
                date(2026, 1, 1),
                score_team1=3,
                score_team2=1,
                team1_players=[
                    {"name": "Alice", "offense": 4, "distribution": 5, "defense": 3, "modifier": 0.1}
                ],
                team2_players=[
                    {"name": "Bob", "offense": 3, "distribution": 3, "defense": 3, "modifier": 0}
                ],
            )
        payload = json.loads(self.last_request.data)
        self.assertEqual(
            payload,
            {
                "game_date": "2026-01-01",
                "score_team1": 3,
                "score_team2": 1,
                "team1_players": [
                    {"name": "Alice", "offense": 4, "distribution": 5, "defense": 3, "modifier": 0.1}
                ],
                "team2_players": [
                    {"name": "Bob", "offense": 3, "distribution": 3, "defense": 3, "modifier": 0}
                ],
            },
        )

    def test_partial_bundle_raises_value_error_without_network_call(self):
        with patch("game_review_service.urlrequest.urlopen") as mock_urlopen:
            with self.assertRaises(ValueError):
                create_game_review_session(
                    "https://service.test",
                    date(2026, 1, 1),
                    score_team1=3,
                )
            mock_urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
