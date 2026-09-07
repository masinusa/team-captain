---
id: F-040
title: Save a game
area: Game recording & history
status: active
origin: ios
related: [F-006, F-041, F-042, F-100]
---

# F-040 — Save a game

## Requirement

- **F-040.1** After splitting teams, a user can save the game once its final
  score is known, recording the date, the final score for each team, and both
  rosters.
- **F-040.2** Both rosters are saved as a frozen snapshot of each player's
  rating fields at that moment (F-006.5), not a reference into the live
  player list — a later rename, rating change, or merge never rewrites a
  saved game.
- **F-040.3** A saved game's rosters are immutable; only the date, final
  score, and per-player goals (F-041) can be edited afterward.
- **F-040.4** Saving is entirely local — no network request is made and no
  account is required.

## Acceptance

- Given two just-split teams and a final score, saving creates a game
  visible in Game History (F-042) with that date, score, and both rosters.
- Given a player is later renamed, merged, or re-rated, a previously saved
  game still shows the name and ratings it was saved with.
- Given a save is attempted with an invalid score or an empty roster, the
  user sees an error and nothing is saved.

## Web client

**Status:** implemented
**Code:** `frontend/src/Game_Time.py`, `frontend/src/game_history.py`

The Save Game form appears on the Team Split page immediately below the
just-split teams, so the flow matches iOS: split teams, play the game, come
back to the same page and save. Only the date (`YYYY-MM-DD`, no time-of-day)
and final score are required; per-player goals are optional. Rosters are
snapshotted with each player's stable UUID plus their rating fields — see
F-041 for why the identifier matters.

**Known gaps:** Date-only, not date+time, unlike iOS's full timestamp. The
Streamlit session holding the just-split teams is lost if the browser tab is
closed before saving — there is no "resume later" mechanism.

## iOS client

**Status:** implemented
**Code:** `Views/GameTimeView.swift` (`SaveGameSheet`), `GameStore.swift`

Date picker, score steppers 0–99, saved to a local `games.json` file.

## History

- 2026-09-06 — Ported from iOS to close the F-045 web gap (a real score is
  needed before a review-link snapshot can be sent).
