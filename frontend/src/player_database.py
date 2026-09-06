"""Local player persistence and migration to the F-006 shared player record."""
import json
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Float, Integer, String, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = f"sqlite:///{os.path.join(os.getenv('DATA_DIR', '.'), 'player_database.db')}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()


class PlayerORM(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    player_id = Column(String(36), unique=True)
    name = Column(String(100), nullable=False)
    distribution_score = Column(Float)
    offense_score = Column(Float)
    defense_score = Column(Float)
    modifier = Column(Float, default=0.0)
    notes = Column(String(500), default="")
    aliases = Column(String, default="[]")
    created_at = Column(String(20))
    updated_at = Column(String(20))
    deleted_at = Column(String(20), nullable=True)
    merged_from = Column(String, default="[]")


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_id(value: str | None = None) -> str:
    return str(uuid.UUID(value)).upper() if value else str(uuid.uuid4()).upper()


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("Player collection fields must be lists of strings.")
    return parsed


def _validate_player(
    name: str, distribution: float, offense: float, defense: float, modifier: float
) -> None:
    if not name.strip():
        raise ValueError("Player name cannot be empty.")
    for rating in (distribution, offense, defense):
        if isinstance(rating, bool) or int(rating) != rating or not 1 <= int(rating) <= 5:
            raise ValueError("Ratings must be integers from 1 to 5.")
    if not -3.0 <= float(modifier) <= 3.0:
        raise ValueError("Modifier must be between -3.0 and 3.0.")


def _validate_timestamp(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be an ISO-8601 UTC timestamp ending in Z.")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 UTC timestamp ending in Z.") from error
    return value


def _player_dict(player: PlayerORM) -> dict:
    return {
        "id": _canonical_id(player.player_id),
        "name": player.name,
        "distribution": int(player.distribution_score),
        "offense": int(player.offense_score),
        "defense": int(player.defense_score),
        "modifier": float(player.modifier or 0),
        "notes": player.notes or "",
        "aliases": _json_list(player.aliases),
        "created_at": player.created_at,
        "updated_at": player.updated_at,
        "deleted_at": player.deleted_at,
        "merged_from": _json_list(player.merged_from),
    }


def _shared_record(record: dict) -> dict:
    required = {
        "id", "name", "distribution", "offense", "defense", "modifier",
        "notes", "aliases", "created_at", "updated_at", "deleted_at", "merged_from",
    }
    missing = required.difference(record)
    if missing:
        raise ValueError(f"Player record is missing required fields: {', '.join(sorted(missing))}.")
    if not isinstance(record["aliases"], list) or not all(isinstance(item, str) for item in record["aliases"]):
        raise ValueError("aliases must be a list of strings.")
    if not isinstance(record["merged_from"], list) or not all(isinstance(item, str) for item in record["merged_from"]):
        raise ValueError("merged_from must be a list of strings.")
    _validate_player(
        record["name"], record["distribution"], record["offense"],
        record["defense"], record["modifier"],
    )
    deleted_at = record["deleted_at"]
    if deleted_at is not None:
        deleted_at = _validate_timestamp(deleted_at, "deleted_at")
    return {
        "player_id": _canonical_id(record["id"]),
        "name": record["name"].strip(),
        "distribution_score": int(record["distribution"]),
        "offense_score": int(record["offense"]),
        "defense_score": int(record["defense"]),
        "modifier": float(record["modifier"]),
        "notes": record["notes"] if isinstance(record["notes"], str) else "",
        "aliases": json.dumps(record["aliases"]),
        "created_at": _validate_timestamp(record["created_at"], "created_at"),
        "updated_at": _validate_timestamp(record["updated_at"], "updated_at"),
        "deleted_at": deleted_at,
        "merged_from": json.dumps([_canonical_id(item) for item in record["merged_from"]]),
    }


def _migrate_schema() -> None:
    """Upgrade existing databases in place without changing migrated values."""
    expected_columns = {
        "player_id": "VARCHAR(36)",
        "aliases": "TEXT",
        "created_at": "VARCHAR(20)",
        "updated_at": "VARCHAR(20)",
        "deleted_at": "VARCHAR(20)",
        "merged_from": "TEXT",
    }
    with engine.begin() as connection:
        columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(players)"))
        }
        for name, definition in expected_columns.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE players ADD COLUMN {name} {definition}"))

        legacy_rows = connection.execute(
            text(
                "SELECT id, player_id, aliases, created_at, updated_at, merged_from "
                "FROM players"
            )
        ).mappings()
        for row in legacy_rows:
            now = _utc_now()
            values = {
                "player_id": _canonical_id(row["player_id"]) if row["player_id"] else _canonical_id(),
                "aliases": row["aliases"] or "[]",
                "created_at": row["created_at"] or now,
                "updated_at": row["updated_at"] or now,
                "merged_from": row["merged_from"] or "[]",
            }
            connection.execute(
                text(
                    "UPDATE players SET player_id = :player_id, aliases = :aliases, "
                    "created_at = :created_at, updated_at = :updated_at, "
                    "merged_from = :merged_from WHERE id = :id"
                ),
                {**values, "id": row["id"]},
            )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS players_live_name_unique "
                "ON players(lower(name)) WHERE deleted_at IS NULL"
            )
        )
        connection.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS players_player_id_unique ON players(player_id)")
        )


_migrate_schema()


def _find_live_name(session, name: str, excluding_id: str | None = None) -> PlayerORM | None:
    query = session.query(PlayerORM).filter(
        PlayerORM.deleted_at.is_(None), PlayerORM.name.ilike(name)
    )
    if excluding_id:
        query = query.filter(PlayerORM.player_id != _canonical_id(excluding_id))
    return query.first()


def add_player(
    name: str,
    distribution: float,
    offense: float,
    defense: float,
    modifier: float = 0.0,
    notes: str = "",
) -> dict:
    """Create a live player with a stable F-006 identifier."""
    _validate_player(name, distribution, offense, defense, modifier)
    canonical_name = name.strip()
    session = Session()
    try:
        existing = _find_live_name(session, canonical_name)
        if existing:
            raise ValueError(f"A player named '{existing.name}' already exists.")
        now = _utc_now()
        player = PlayerORM(
            player_id=_canonical_id(),
            name=canonical_name,
            distribution_score=int(distribution),
            offense_score=int(offense),
            defense_score=int(defense),
            modifier=float(modifier),
            notes=notes,
            aliases="[]",
            created_at=now,
            updated_at=now,
            merged_from="[]",
        )
        session.add(player)
        session.commit()
        return _player_dict(player)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_player(player_id: str) -> None:
    """Tombstone a player so the deletion can later propagate across devices."""
    session = Session()
    try:
        player = session.query(PlayerORM).filter_by(player_id=_canonical_id(player_id)).first()
        if not player or player.deleted_at:
            raise ValueError("Player not found.")
        now = _utc_now()
        player.deleted_at = now
        player.updated_at = now
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_player(
    player_id: str,
    name: str,
    distribution: float,
    offense: float,
    defense: float,
    modifier: float,
    notes: str,
) -> dict:
    """Update a live player by immutable UUID."""
    _validate_player(name, distribution, offense, defense, modifier)
    session = Session()
    try:
        canonical_id = _canonical_id(player_id)
        player = (
            session.query(PlayerORM)
            .filter_by(player_id=canonical_id, deleted_at=None)
            .first()
        )
        if not player:
            raise ValueError("Player not found.")
        existing = _find_live_name(session, name.strip(), excluding_id=canonical_id)
        if existing:
            raise ValueError(f"A player named '{existing.name}' already exists.")
        player.name = name.strip()
        player.distribution_score = int(distribution)
        player.offense_score = int(offense)
        player.defense_score = int(defense)
        player.modifier = float(modifier)
        player.notes = notes
        player.updated_at = _utc_now()
        session.commit()
        return _player_dict(player)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_player(player_id: str) -> dict | None:
    """Return one live player by UUID."""
    session = Session()
    try:
        player = (
            session.query(PlayerORM)
            .filter_by(player_id=_canonical_id(player_id), deleted_at=None)
            .first()
        )
        return _player_dict(player) if player else None
    finally:
        session.close()


def list_players(include_deleted: bool = False) -> list[dict]:
    """List player records, hiding tombstones unless explicitly requested."""
    session = Session()
    try:
        query = session.query(PlayerORM)
        if not include_deleted:
            query = query.filter(PlayerORM.deleted_at.is_(None))
        return [_player_dict(player) for player in query.order_by(PlayerORM.name).all()]
    finally:
        session.close()


def restore_players(records: list[dict]) -> tuple[int, int]:
    """Merge validated F-006 records by UUID, retaining the newest version."""
    normalized = [_shared_record(record) for record in records]
    ids = [record["player_id"] for record in normalized]
    if len(set(ids)) != len(ids):
        raise ValueError("Backup contains duplicate player identifiers.")
    live_names = [record["name"].casefold() for record in normalized if record["deleted_at"] is None]
    if len(set(live_names)) != len(live_names):
        raise ValueError("Backup contains duplicate live player names.")

    session = Session()
    added = updated = 0
    try:
        for record in normalized:
            existing = session.query(PlayerORM).filter_by(player_id=record["player_id"]).first()
            if existing:
                if record["updated_at"] > existing.updated_at:
                    for field, value in record.items():
                        setattr(existing, field, value)
                    updated += 1
                continue
            if record["deleted_at"] is None:
                collision = _find_live_name(session, record["name"])
                if collision:
                    raise ValueError("Backup conflicts with an existing live player name.")
            session.add(PlayerORM(**record))
            added += 1
        session.commit()
        return added, updated
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
