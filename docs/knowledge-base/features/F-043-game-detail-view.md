---
id: F-043
title: Game detail view
area: Game recording & history
status: active
origin: ios
related: [F-040, F-041, F-044, F-045, F-060]
---

# F-043 — Game detail view

## Requirement

- **F-043.1** Opening a saved game (from F-042) shows the final score, both
  rosters with each player's ratings and any goals scored (F-041), and any
  notes (F-044).
- **F-043.2** A user can edit the date, final score, and per-player goals of
  a saved game. Rosters cannot be edited (F-040.3).
- **F-043.3** A user can create a Game Review link (F-045) from this view,
  sending the game's real score, rosters, and per-player ranking snapshot.

## Acceptance

- Given a saved game, its detail view shows score, both rosters (with
  ratings and any goals), and notes.
- Given an edit to date/score/goals, the change is reflected immediately and
  the roster is unchanged.
- Given `GAME_REVIEW_SERVICE_URL` is configured, a review link can be
  created from this view carrying the game's real data.

## Web client

**Status:** implemented
**Code:** `frontend/src/pages/Game_History.py`

**Known gaps:** No hide-ratings/anonymize-names toggle exists on web at all
(F-060 isn't implemented there), so ratings and real names are always shown
— there is no equivalent of iOS's privacy settings for this view yet.

## iOS client

**Status:** implemented
**Code:** `Views/GameHistoryView.swift` (`GameDetailView`)

Score header; per-team player rows (name, goals, ratings — each hideable via
`hideNamesFromHistory`/`hideRatingsFromHistory`); notes section; edit via the
same `SaveGameSheet` used to create the game (rosters excluded); Game Review
link creation at the bottom.

## History

- 2026-09-06 — Ported from iOS as part of the web Game History feature; also
  became the new (and only) place web creates Game Review links from,
  replacing the old pre-game, snapshot-less path (see F-045's History).
