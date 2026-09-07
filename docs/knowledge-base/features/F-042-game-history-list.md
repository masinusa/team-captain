---
id: F-042
title: Game history list
area: Game recording & history
status: active
origin: ios
related: [F-040, F-043]
---

# F-042 — Game history list

## Requirement

- **F-042.1** A user can browse every game saved (F-040), newest first,
  each row showing at least the date, final score, and result summary.
- **F-042.2** A user can select a row to open that game's detail view
  (F-043).
- **F-042.3** A user can delete a saved game from this list.

## Acceptance

- Given at least one saved game, the list shows every one of them, most
  recent first.
- Given no saved games, the list shows an empty-state message rather than
  nothing.
- Deleting a game removes it from the list immediately.

## Web client

**Status:** implemented
**Code:** `frontend/src/pages/Game_History.py`

Auto-discovered as the "Game History" sidebar page. Ordered by game date,
then by save time as a tiebreaker.

**Known gaps:** iOS orders by raw insertion order (newest saved always at the
top); web orders by the game's own date instead, since SQL storage has no
natural insertion order once a game is edited. In practice these usually
agree, but if someone saves an old game after a recent one, the two clients
would order them differently.

## iOS client

**Status:** implemented
**Code:** `Views/GameHistoryView.swift`

`List` bound to `GameStore.games` (already newest-first by construction —
`save()` inserts at index 0). Swipe-to-delete.

## History

- 2026-09-06 — Ported from iOS as part of the web Game History feature.
