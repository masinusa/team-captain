---
id: F-041
title: Per-player goal tracking
area: Game recording & history
status: active
origin: ios
related: [F-006, F-040, F-043]
---

# F-041 — Per-player goal tracking

## Requirement

- **F-041.1** When saving or editing a game, a user can record how many
  goals each player on either roster scored (0–20).
- **F-041.2** Goals are keyed by the player's stable identifier, not by
  name — so a later rename or merge (F-006.4/F-006.5) doesn't detach a
  player's historical goals from them.
- **F-041.3** Goals default to zero and are optional; a game can be saved
  with no goals recorded.

## Acceptance

- Given a saved game, each player's goal count (if any) is visible in the
  game's detail view (F-043).
- Given a player is renamed or merged after a game was saved, their
  historical goal count in that game still resolves to them.
- Given a goal count outside 0–20, or one recorded for a player not on
  either roster in that game, saving is rejected.

## Web client

**Status:** implemented
**Code:** `frontend/src/game_history.py` (`goals` column, `player_goals()`)

Goals are entered as part of the Save Game form (F-040) and are editable
afterward (F-043). Stored as a JSON object keyed by the player's canonical
uppercase UUID — the same identifier `player_database.py` uses — so goal
history survives renames and merges exactly as F-006.5 requires.

## iOS client

**Status:** implemented
**Code:** `Views/GameTimeView.swift`, `Models/Game.swift`

Steppers 0–20 per player; `goalsByPlayerID` keyed by `player.id.uuidString`.

## History

- 2026-09-06 — Ported from iOS as part of the web Game History feature.
