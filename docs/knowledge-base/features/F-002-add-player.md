---
id: F-002
title: Add a player
area: Player management
status: active
origin: web
related: [F-001, F-003]
---

# F-002 — Add a player

## Requirement

- **F-002.1** The user can add a new player to the roster, supplying a name,
  the three ratings, a modifier, and an optional note.
- **F-002.2** Every field is offered with a sensible default so that supplying
  only a name produces a valid player.
- **F-002.3** The input controls must permit the full valid range of each
  field as defined in F-001.3 — ratings 1–5 — and must not permit values
  outside it.
- **F-002.4** A name that collides with an existing player, compared
  case-insensitively, is rejected with a visible message and no write occurs.
- **F-002.5** On success the roster reflects the new player immediately.

## Acceptance

- Entering only a name and confirming creates a player with default ratings.
- A rating of 0 cannot be entered through the UI and is rejected if supplied.
- Adding `Sam` while `sam` exists is rejected, and the roster is unchanged.
- The rejection message names the conflict rather than failing silently.

## Web client

**Status:** implemented
**Code:** `frontend/src/pages/The_Bench.py` (`add_player_view`),
`frontend/src/player_database.py` (`add_player`)

The three rating sliders are bounded 1–5, which satisfies F-002.3.

**Known gaps:**

- Whitespace-only names pass the duplicate check and are accepted (F-002.1
  implies a real name).
- The duplicate check uses SQL `ilike`, which treats `%` and `_` in a name as
  wildcards — so a name containing either can match the wrong row, or fail to
  match itself.
- The Add form's `1–5` bound is enforced only by the widget. The domain model
  still validates `ge=0`, so nothing rejects a 0 arriving from the Edit form
  or an import. See F-001.

## History

- 2026-09-05 — Created from an audit of the existing web and iOS clients.
