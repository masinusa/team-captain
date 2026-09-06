"""Local player persistence and migration to the F-006 shared player record."""
import json
import os
import uuid
import warnings
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

# Lower-cased names held by more than one live player. Populated by
# _migrate_schema() when existing data already violates the uniqueness rule
# (F-001.5), which prevents the unique index from being created. The roster UI
# surfaces these so they can be merged; see F-006.4.
DUPLICATE_LIVE_NAMES: list[str] = []


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


def _normalize_aliases(candidates: list[str], owner_name: str) -> list[str]:
    """Clean a set of alternate names for one player.

    Trims, drops blanks, and dedupes case-insensitively while keeping the first
    spelling seen. The player's own canonical name is never kept as an alias of
    itself. Blank entries must not survive: the iOS record validator rejects
    them outright, so one would break sync rather than fail here.
    """
    aliases: list[str] = []
    seen = {owner_name.strip().lower()}
    for candidate in candidates:
        cleaned = candidate.strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            aliases.append(cleaned)
    return aliases


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


def _canonical_record_bytes(record: dict) -> bytes:
    """Return the F-083 equal-timestamp conflict ordering for one record."""
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _public_record(record: dict) -> dict:
    """Convert an internally normalized shared record to its F-006 shape."""
    return {
        "id": record["player_id"],
        "name": record["name"],
        "distribution": record["distribution_score"],
        "offense": record["offense_score"],
        "defense": record["defense_score"],
        "modifier": record["modifier"],
        "notes": record["notes"],
        "aliases": json.loads(record["aliases"]),
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
        "deleted_at": record["deleted_at"],
        "merged_from": json.loads(record["merged_from"]),
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


def _refresh_live_name_index() -> list[str]:
    """Create the live-name uniqueness index once the data permits it.

    Databases created before F-001.5 was enforced can already hold duplicate
    live names. Creating the index regardless raises IntegrityError inside the
    migration transaction, which runs at import and would stop the app from
    starting at all. F-006.3 forbids resolving duplicates automatically, so the
    blocking names are recorded for the UI to surface and the index is deferred.

    Called again after a merge, so the constraint reappears on its own as soon
    as the last duplicate is resolved.
    """
    with engine.begin() as connection:
        duplicates = [
            row[0]
            for row in connection.execute(
                text(
                    "SELECT lower(name) FROM players WHERE deleted_at IS NULL "
                    "GROUP BY lower(name) HAVING count(*) > 1 ORDER BY lower(name)"
                )
            )
        ]
        if not duplicates:
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS players_live_name_unique "
                    "ON players(lower(name)) WHERE deleted_at IS NULL"
                )
            )
    DUPLICATE_LIVE_NAMES[:] = duplicates
    return duplicates


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
            text("CREATE UNIQUE INDEX IF NOT EXISTS players_player_id_unique ON players(player_id)")
        )

    _refresh_live_name_index()
    if DUPLICATE_LIVE_NAMES:
        warnings.warn(
            "Duplicate player names found, so live-name uniqueness is not "
            "enforced yet: "
            + ", ".join(DUPLICATE_LIVE_NAMES)
            + ". Merge them (F-006.4); the index is created automatically "
            "once none remain.",
            RuntimeWarning,
            stacklevel=2,
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


def merge_players(winner_id: str, loser_id: str) -> dict:
    """Fold one player record into another, per F-006.4.

    The winner keeps its identifier and ratings. The loser's name and aliases
    become aliases of the winner, its identifier is recorded in the winner's
    ``merged_from``, and it is tombstoned rather than deleted.

    Nothing in stored game history is rewritten. Games embed player snapshots
    and key goals by identifier (F-006.5), so ``merged_from`` acts as a
    forwarding address instead — an old reference to the loser still resolves
    to the surviving player.
    """
    winner_key = _canonical_id(winner_id)
    loser_key = _canonical_id(loser_id)
    if winner_key == loser_key:
        raise ValueError("Cannot merge a player into itself.")

    session = Session()
    try:
        winner = session.query(PlayerORM).filter_by(player_id=winner_key).first()
        loser = session.query(PlayerORM).filter_by(player_id=loser_key).first()
        if not winner or winner.deleted_at:
            raise ValueError("Surviving player not found.")
        if not loser or loser.deleted_at:
            raise ValueError("Merged player not found.")

        aliases = _normalize_aliases(
            _json_list(winner.aliases) + [loser.name] + _json_list(loser.aliases),
            winner.name,
        )

        # Carry the loser's own redirects across so a chain of merges keeps
        # resolving rather than dead-ending at the intermediate record.
        merged_from: list[str] = []
        for candidate in _json_list(winner.merged_from) + [loser.player_id] + _json_list(loser.merged_from):
            key = _canonical_id(candidate)
            if key != winner_key and key not in merged_from:
                merged_from.append(key)

        now = _utc_now()
        winner.aliases = json.dumps(aliases)
        winner.merged_from = json.dumps(merged_from)
        winner.updated_at = now
        loser.deleted_at = now
        loser.updated_at = now
        session.commit()
        merged = _player_dict(winner)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    # The merge may have removed the last duplicate blocking the constraint.
    _refresh_live_name_index()
    return merged


def update_player(
    player_id: str,
    name: str,
    distribution: float,
    offense: float,
    defense: float,
    modifier: float,
    notes: str,
    aliases: list[str] | None = None,
) -> dict:
    """Update a live player by immutable UUID.

    ``aliases`` defaults to None meaning "leave unchanged", so existing
    positional callers keep working. Passing a list replaces the alternate
    names wholesale; pass [] to clear them.
    """
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
        if aliases is not None:
            player.aliases = json.dumps(_normalize_aliases(aliases, player.name))
        elif player.name.strip().lower() in {
            alias.strip().lower() for alias in _json_list(player.aliases)
        }:
            # A rename can collide with an existing alias, which would leave the
            # player listed as an alias of itself.
            player.aliases = json.dumps(
                _normalize_aliases(_json_list(player.aliases), player.name)
            )
        player.updated_at = _utc_now()
        session.commit()
        return _player_dict(player)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def resolve_player_id(player_id: str) -> str | None:
    """Follow a merge redirect to the player that absorbed this identifier.

    Returns the id unchanged when it still names a live player, the surviving
    player's id when it was merged away, or None when it resolves to nothing.

    This is F-006.5: game history and saved selections keep referring to
    identifiers that a later merge tombstoned, and those references are meant to
    keep resolving rather than dangling.
    """
    canonical = _canonical_id(player_id)
    session = Session()
    try:
        live = (
            session.query(PlayerORM)
            .filter_by(player_id=canonical, deleted_at=None)
            .first()
        )
        if live:
            return live.player_id
        # A merge chain is stored flattened -- merge_players carries the loser's
        # own redirects onto the winner -- so one pass is enough.
        for candidate in session.query(PlayerORM).filter(PlayerORM.deleted_at.is_(None)):
            if canonical in _json_list(candidate.merged_from):
                return candidate.player_id
        return None
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
                incoming_wins_tie = (
                    record["updated_at"] == existing.updated_at
                    and _canonical_record_bytes(_public_record(record))
                    > _canonical_record_bytes(_player_dict(existing))
                )
                if record["updated_at"] > existing.updated_at or incoming_wins_tie:
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
