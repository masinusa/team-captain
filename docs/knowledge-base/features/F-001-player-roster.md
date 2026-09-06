---
id: F-001
title: Player roster
area: Player management
status: active
origin: web
related: [F-002, F-003, F-004, F-005, F-080]
---

# F-001 — Player roster

## Requirement

- **F-001.1** The app stores a roster of players that persists between
  sessions on the device.
- **F-001.2** A player record has: a name, a distribution rating, an offense
  rating, a defense rating, a modifier, and a free-text note.
- **F-001.3** The three ratings are integers in the range 1–5. The modifier is
  a number in the range −3.0 to 3.0. The note is optional. A rating of 0 is
  **not** valid — every player is rated at least 1 in every category.
- **F-001.4** The user can see every player on the roster together with their
  ratings, in a stable, predictable order.
- **F-001.5** Player names are unique, compared case-insensitively.
- **F-001.6** An empty roster is shown as an explicit empty state, not a blank
  screen.

## Acceptance

- Adding `Sam` and then `sam` is rejected — F-001.5 is case-insensitive.
- Ratings of 1 and 5 are both accepted; 0, 6 and −1 are not.
- A modifier of exactly −3.0 and exactly 3.0 are both accepted.
- Restarting the app shows the same roster.

## Web client

**Status:** implemented
**Code:** `frontend/src/pages/The_Bench.py`, `frontend/src/player_database.py`

**Known gaps:**

- The Add form's rating sliders run 1–5 and the Edit form's run 0–5. Under
  F-001.3 the **Add form is correct and the Edit form is the defect** — editing
  a player can set a rating to 0, which the domain model then accepts (it still
  validates `ge=0`) and which no UI can produce on creation. (Also on F-002.)
- The domain model in `frontend/src/algorithm/data_models/Player.py` still
  validates `ge=0`, so a 0 written by the Edit form round-trips silently
  instead of being rejected.
- Uniqueness (F-001.5) is enforced in application code only. The `players`
  table has **no unique constraint** on `name`, so a concurrent or direct
  write can violate it.
- Rating columns are `FLOAT` in SQLite but the domain model requires `int`.
  A non-integer value already in the database will fail validation at read
  time rather than at write time.
- Empty or whitespace-only names are not rejected.

## History

- 2026-09-05 — Created from an audit of the existing web and iOS clients.
