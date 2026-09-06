---
id: F-006
title: Player identity, aliases, and duplicate merge
area: Player management
status: active
origin: web
related: [F-001, F-003, F-005, F-041, F-080, F-083]
---

# F-006 — Player identity, aliases, and duplicate merge

## Requirement

- **F-006.1** Every player has an identifier that is stable for the lifetime of
  that person, unique across all devices, and never reused. It is assigned once
  at creation and never changes — not when the player is renamed, edited, or
  merged.
- **F-006.2** A player has one canonical `name` plus zero or more `aliases`.
  Searching the roster matches against the canonical name **and** every alias.
- **F-006.3** Aliases are never used to match players automatically. They make
  a person findable; they never cause two records to be treated as one.
- **F-006.4** Two records representing the same person can be merged by an
  explicit user action. Merging picks a winner; the loser's name and aliases
  become aliases of the winner, and the loser's identifier is recorded on the
  winner so historical references still resolve.
- **F-006.5** A merge never rewrites stored game history. Games keep the
  identifier and the player snapshot they were saved with (F-041).
- **F-006.6** Deleting a player records a deletion rather than erasing the
  record, so the deletion can propagate to other devices (F-083).
- **F-006.7** Identifiers are compared case-insensitively but written in one
  canonical casing, so the same person is never split by formatting alone.

## Acceptance

- Rename a player: the identifier is unchanged and past games still resolve.
- Delete a player and re-add them with the same name: these are two different
  people with two identifiers, and the roster does not silently rejoin them.
- Merge those two: searching either name finds the surviving player, and goals
  recorded against the absorbed identifier still count toward that person.
- A player deleted on one device stays deleted after syncing with another.
- An alias equal to another player's canonical name does not merge anything.

## The shared record

This is the interchange format every client reads and writes. Field names match
what the clients already store (`modifier`, not the spec's `injury_handicap`).

```json
{
  "schema_version": 1,
  "exported_at": "2026-09-06T14:30:00Z",
  "players": [
    {
      "id": "550E8400-E29B-41D4-A716-446655440000",
      "name": "Michael Spicer",
      "aliases": ["Mike", "Spice"],
      "offense": 4,
      "distribution": 3,
      "defense": 2,
      "modifier": 0.0,
      "notes": "",
      "created_at": "2026-01-15T09:00:00Z",
      "updated_at": "2026-09-06T14:00:00Z",
      "deleted_at": null,
      "merged_from": []
    }
  ],
  "games": []
}
```

| Field | Rule |
|---|---|
| `id` | UUID, **uppercase** canonical form. Compare case-insensitively, emit uppercase. |
| `name` | Canonical display name; unique case-insensitively among live records. |
| `aliases` | Alternate names. Searchable. Never used for automatic matching. |
| `offense`, `distribution`, `defense` | Integers **1–5** (F-001.3). |
| `modifier` | Float −3.0…3.0. |
| `created_at`, `updated_at`, `deleted_at` | **ISO-8601 UTC with `Z`.** `deleted_at` is `null` when live. |
| `merged_from` | Identifiers that now redirect to this record. |
| `games` | Reserved. Always `[]` at schema version 1. |

Uppercase `id` is not arbitrary: it is what Swift's `UUID.uuidString` produces,
and iOS keys game goals by that exact string.

`games` exists as an empty reserved key so game sync can be added later without
a schema version bump.

## Why merges redirect instead of rewriting

Game history is a snapshot by design (F-041) — each saved game embeds frozen
copies of its players, and goals are keyed by player identifier. Rewriting those
records during a merge would mutate history that is supposed to be immutable,
and a partial failure would corrupt it.

`merged_from` makes the winner a forwarding address instead. Any question of the
form "everything this person ever did" resolves through it, and not one stored
game is touched.

## Web client

**Status:** not implemented
**Code:** —

The web client currently has no stable identity at all. `players.id` is a SQLite
autoincrement rowid that is never read, never exported, and differs per device;
every operation keys off the name string. There is no alias, timestamp, or
tombstone field.

**Known gaps:**

- `get_player`, `update_player` and `delete_player` match names
  case-sensitively while `add_player` guards uniqueness case-insensitively, so
  a row whose stored casing differs from the queried casing is unreachable.
  Keying on `id` removes this class of bug entirely.
- `backup.py` matches on lowercased name and never deletes, so a player removed
  on one device is resurrected by the next import.

## History

- 2026-09-06 — Created. Defines the shared record for cross-device sync, after
  finding that iOS keys players by UUID and the web client keys them by name,
  which would detach every historical goal on first sync.
