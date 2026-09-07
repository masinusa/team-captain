"""Local game history persistence (F-040-F-044).

Games are frozen snapshots by design (F-006.5/F-041): each saved game embeds
the full roster it was played with, not references into the live player
table, so a later rename or merge never rewrites history. This module never
imports player_database -- the UI layer is responsible for resolving live
players into snapshot dicts before calling save_game.
"""
import json
import os
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = f"sqlite:///{os.path.join(os.getenv('DATA_DIR', '.'), 'game_history.db')}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

SNAPSHOT_FIELDS = ("id", "name", "offense", "distribution", "defense", "injury_handicap")


class GameORM(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    game_id = Column(String(36), unique=True, nullable=False)
    game_date = Column(String(10), nullable=False)
    team1_players = Column(String, nullable=False)
    team2_players = Column(String, nullable=False)
    score1 = Column(Integer, nullable=False)
    score2 = Column(Integer, nullable=False)
    goals = Column(String, default="{}")
    notes = Column(String, default="[]")
    created_at = Column(String(20), nullable=False)
    updated_at = Column(String(20), nullable=False)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_id(value: str | None = None) -> str:
    return str(uuid.UUID(value)).upper() if value else str(uuid.uuid4()).upper()


def _game_date_str(value: date | str) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as error:
            raise ValueError("game_date must be an ISO-8601 date.") from error
    raise ValueError("game_date must be a date or an ISO-8601 date string.")


def _validate_roster(players: list[dict], field: str) -> list[dict]:
    if not isinstance(players, list) or not players:
        raise ValueError(f"{field} must be a non-empty list of players.")
    normalized = []
    for entry in players:
        if not isinstance(entry, dict) or any(key not in entry for key in SNAPSHOT_FIELDS):
            raise ValueError(f"{field} entries must include {', '.join(SNAPSHOT_FIELDS)}.")
        player_id = entry["id"]
        name = entry["name"]
        if not isinstance(player_id, str) or not player_id.strip():
            raise ValueError(f"{field} entries must have a non-empty id.")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{field} entries must have a non-empty name.")
        for rating_field in ("offense", "distribution", "defense"):
            rating = entry[rating_field]
            if isinstance(rating, bool) or int(rating) != rating or not 1 <= int(rating) <= 5:
                raise ValueError(f"{field} ratings must be integers from 1 to 5.")
        modifier = entry["injury_handicap"]
        if not -3.0 <= float(modifier) <= 3.0:
            raise ValueError(f"{field} injury_handicap must be between -3.0 and 3.0.")
        normalized.append(
            {
                "id": _canonical_id(player_id),
                "name": name,
                "offense": int(entry["offense"]),
                "distribution": int(entry["distribution"]),
                "defense": int(entry["defense"]),
                "injury_handicap": float(modifier),
            }
        )
    return normalized


def _validate_score(value, field: str) -> int:
    if isinstance(value, bool) or int(value) != value or not 0 <= int(value) <= 99:
        raise ValueError(f"{field} must be an integer from 0 to 99.")
    return int(value)


def _validate_goals(goals: dict | None, valid_ids: set[str]) -> dict[str, int]:
    if goals is None:
        return {}
    if not isinstance(goals, dict):
        raise ValueError("goals_by_player_id must be a dict.")
    validated: dict[str, int] = {}
    for player_id, count in goals.items():
        canonical = _canonical_id(player_id)
        if canonical not in valid_ids:
            raise ValueError("Goal recorded for a player not in this game.")
        if isinstance(count, bool) or int(count) != count or not 0 <= int(count) <= 20:
            raise ValueError("Goals must be integers from 0 to 20.")
        validated[canonical] = int(count)
    return validated


def _game_dict(game: GameORM) -> dict:
    score1 = game.score1
    score2 = game.score2
    return {
        "id": game.game_id,
        "date": game.game_date,
        "team1_players": json.loads(game.team1_players),
        "team2_players": json.loads(game.team2_players),
        "score1": score1,
        "score2": score2,
        "winner": 1 if score1 > score2 else (2 if score2 > score1 else None),
        "goals": json.loads(game.goals or "{}"),
        "notes": json.loads(game.notes or "[]"),
        "created_at": game.created_at,
        "updated_at": game.updated_at,
    }


def save_game(
    game_date: date | str,
    team1_players: list[dict],
    team2_players: list[dict],
    score1: int,
    score2: int,
    goals_by_player_id: dict[str, int] | None = None,
) -> dict:
    """Save a newly played game with its final score and both rosters."""
    normalized_date = _game_date_str(game_date)
    normalized_team1 = _validate_roster(team1_players, "team1_players")
    normalized_team2 = _validate_roster(team2_players, "team2_players")
    normalized_score1 = _validate_score(score1, "score1")
    normalized_score2 = _validate_score(score2, "score2")
    valid_ids = {player["id"] for player in normalized_team1 + normalized_team2}
    normalized_goals = _validate_goals(goals_by_player_id, valid_ids)

    session = Session()
    try:
        now = _utc_now()
        game = GameORM(
            game_id=_canonical_id(),
            game_date=normalized_date,
            team1_players=json.dumps(normalized_team1),
            team2_players=json.dumps(normalized_team2),
            score1=normalized_score1,
            score2=normalized_score2,
            goals=json.dumps(normalized_goals),
            notes="[]",
            created_at=now,
            updated_at=now,
        )
        session.add(game)
        session.commit()
        return _game_dict(game)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_game(
    game_id: str,
    game_date: date | str,
    score1: int,
    score2: int,
    goals_by_player_id: dict[str, int] | None = None,
) -> dict:
    """Update a saved game's date/score/goals. Rosters are frozen at save time."""
    normalized_date = _game_date_str(game_date)
    normalized_score1 = _validate_score(score1, "score1")
    normalized_score2 = _validate_score(score2, "score2")

    session = Session()
    try:
        game = session.query(GameORM).filter_by(game_id=_canonical_id(game_id)).first()
        if not game:
            raise ValueError("Game not found.")
        valid_ids = {
            player["id"]
            for player in json.loads(game.team1_players) + json.loads(game.team2_players)
        }
        normalized_goals = _validate_goals(goals_by_player_id, valid_ids)
        game.game_date = normalized_date
        game.score1 = normalized_score1
        game.score2 = normalized_score2
        game.goals = json.dumps(normalized_goals)
        game.updated_at = _utc_now()
        session.commit()
        return _game_dict(game)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_game(game_id: str) -> None:
    """Permanently remove a game. Games aren't in the sync/backup envelope yet,
    so unlike players (which tombstone) there is no reason to keep a record."""
    session = Session()
    try:
        game = session.query(GameORM).filter_by(game_id=_canonical_id(game_id)).first()
        if not game:
            raise ValueError("Game not found.")
        session.delete(game)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_game(game_id: str) -> dict | None:
    session = Session()
    try:
        game = session.query(GameORM).filter_by(game_id=_canonical_id(game_id)).first()
        return _game_dict(game) if game else None
    finally:
        session.close()


def list_games() -> list[dict]:
    """List games, newest first by game date, then by creation time."""
    session = Session()
    try:
        query = session.query(GameORM).order_by(
            GameORM.game_date.desc(), GameORM.created_at.desc()
        )
        return [_game_dict(game) for game in query.all()]
    finally:
        session.close()


def add_note(game_id: str, text: str, author: str = "") -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Note text cannot be empty.")
    session = Session()
    try:
        game = session.query(GameORM).filter_by(game_id=_canonical_id(game_id)).first()
        if not game:
            raise ValueError("Game not found.")
        notes = json.loads(game.notes or "[]")
        notes.append(
            {
                "id": _canonical_id(),
                "text": text.strip(),
                "author": author.strip() if isinstance(author, str) else "",
                "date": _utc_now(),
            }
        )
        game.notes = json.dumps(notes)
        game.updated_at = _utc_now()
        session.commit()
        return _game_dict(game)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_note(game_id: str, note_id: str) -> dict:
    session = Session()
    try:
        game = session.query(GameORM).filter_by(game_id=_canonical_id(game_id)).first()
        if not game:
            raise ValueError("Game not found.")
        notes = json.loads(game.notes or "[]")
        remaining = [note for note in notes if note.get("id") != note_id]
        if len(remaining) == len(notes):
            raise ValueError("Note not found.")
        game.notes = json.dumps(remaining)
        game.updated_at = _utc_now()
        session.commit()
        return _game_dict(game)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def player_goals(game: dict, player_id: str) -> int:
    return game["goals"].get(_canonical_id(player_id), 0)
