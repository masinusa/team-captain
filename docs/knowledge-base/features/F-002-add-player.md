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
  field as defined in F-001.3 — including a rating of 0.
- **F-002.4** A name that collides with an existing player, compared
  case-insensitively, is rejected with a visible message and no write occurs.
- **F-002.5** On success the roster reflects the new player immediately.

## Acceptance

- Entering only a name and confirming creates a player with default ratings.
- A rating of 0 can be entered through the UI, not merely stored.
- Adding `Sam` while `sam` exists is rejected, and the roster is unchanged.
- The rejection message names the conflict rather than failing silently.

## Web client

**Status:** partial
**Code:** `frontend/src/pages/The_Bench.py` (`add_player_view`),
`frontend/src/player_database.py` (`add_player`)

**Known gaps:**

- **Violates F-002.3.** The three rating sliders are bounded 1–5, so a rating
  of 0 cannot be entered on the Add form — even though F-001.3 allows it and
  the Edit form's sliders are 0–5. A player who should be rated 0 in a
  category has to be added and then edited.
- Whitespace-only names pass the duplicate check and are accepted (F-002.1
  implies a real name).

## History

- 2026-09-05 — Created from an audit of the existing web and iOS clients.
