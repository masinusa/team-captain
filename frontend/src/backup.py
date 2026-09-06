"""F-006 version-1 local backup serialization."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from player_database import list_players, restore_players

SCHEMA_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_backup_dir() -> Path:
    backup_dir = Path(os.getenv("BACKUP_DIR", os.path.join(os.getenv("DATA_DIR", "."), "backups")))
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def export_payload() -> dict:
    """Serialize every player record in the shared interchange envelope."""
    return {
        "schema_version": SCHEMA_VERSION,
        "exported_at": _utc_now(),
        "players": list_players(include_deleted=True),
        "games": [],
    }


def export_backup() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = get_backup_dir() / f"players-{timestamp}.json"
    path.write_text(json.dumps(export_payload(), indent=2), encoding="utf-8")
    return path


def import_backup(path: Path) -> tuple[int, int]:
    """Merge a validated version-1 local backup by stable player identifier."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION or payload.get("games") != []:
        raise ValueError("Backup is not a supported version-1 player payload.")
    if not isinstance(payload.get("players"), list):
        raise ValueError("Backup must contain a players list.")
    return restore_players(payload["players"])


def list_backups() -> list[Path]:
    return sorted(get_backup_dir().glob("players-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
