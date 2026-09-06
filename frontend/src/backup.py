import json
import os
from datetime import datetime, timezone
from pathlib import Path

from player_database import add_player, list_players, update_player


def get_backup_dir() -> Path:
    """Resolve the local backup directory, creating it if needed."""
    backup_dir = Path(os.getenv("BACKUP_DIR", os.path.join(os.getenv("DATA_DIR", "."), "backups")))
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def export_payload() -> dict:
    """The current roster in the shared backup/sync JSON schema."""
    return {"players": list_players()}


def export_backup() -> Path:
    """Write the current roster to a timestamped local JSON backup file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = get_backup_dir() / f"players-{timestamp}.json"
    path.write_text(json.dumps(export_payload(), indent=2))
    return path


def restore_players(players: list[dict]) -> tuple[int, int]:
    """Upsert a list of player dicts (the shared backup/sync schema) into the local DB.

    Matching is case-insensitive, the same rule add_player enforces. The stored
    spelling of an existing player wins, because update_player looks a player up
    by exact name — passing the backup's spelling of an already-present player
    would match nothing and silently drop the update.

    Returns (added, updated).
    """
    # Map lowercased name -> the spelling actually stored in the DB.
    existing_names = {p["name"].lower(): p["name"] for p in list_players()}
    added = updated = 0
    for player in players:
        name = (player.get("name") or "").strip()
        if not name:
            continue
        args = (
            player.get("distribution", 2),
            player.get("offense", 2),
            player.get("defense", 2),
            player.get("modifier", 0.0),
            player.get("notes", ""),
        )
        stored_name = existing_names.get(name.lower())
        if stored_name is not None:
            update_player(stored_name, *args)
            updated += 1
        else:
            add_player(name, *args)
            existing_names[name.lower()] = name
            added += 1
    return added, updated


def import_backup(path: Path) -> tuple[int, int]:
    """Restore players from a local backup JSON file. Returns (added, updated)."""
    payload = json.loads(Path(path).read_text())
    return restore_players(payload.get("players", []))


def list_backups() -> list[Path]:
    """Local backup files, newest first."""
    return sorted(get_backup_dir().glob("players-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
