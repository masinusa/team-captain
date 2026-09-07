---
id: F-044
title: Game notes
area: Game recording & history
status: active
origin: ios
related: [F-040, F-043]
---

# F-044 — Game notes

## Requirement

- **F-044.1** A user can add a free-text note to a saved game, optionally
  attributed to an author.
- **F-044.2** A user can view all notes on a game and delete any of them.
- **F-044.3** A note cannot be blank.

## Acceptance

- Given a saved game, a note can be added with text and an optional author,
  and appears in the game's detail view with a timestamp.
- Given an existing note, it can be deleted.
- Given blank note text, adding it is rejected.

## Web client

**Status:** implemented
**Code:** `frontend/src/game_history.py` (`add_note`, `delete_note`)

**Known gaps:** Web has no account/profile-name concept, so `author` is a
free-typed field per note rather than auto-filled from a signed-in identity.

## iOS client

**Status:** implemented
**Code:** `Models/Game.swift` (`GameNote`), `Views/GameHistoryView.swift`
(`AddNoteSheet`)

Text + optional author, timestamped at creation. Swipe-to-delete.

## History

- 2026-09-06 — Ported from iOS as part of the web Game History feature.
