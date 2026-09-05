---
id: F-020
title: Player selection for a split
area: Team generation & display
status: active
origin: web
related: [F-001, F-005, F-021, F-104]
---

# F-020 — Player selection for a split

## Requirement

- **F-020.1** The user can choose a subset of the roster to be split into
  teams, selecting and deselecting players freely before generating.
- **F-020.2** The current count of selected players is visible at all times.
- **F-020.3** The selection survives navigating away to another part of the
  app and back within the same session.
- **F-020.4** If a selected player is deleted from the roster, they are
  dropped from the selection rather than leaving it in a broken state.
- **F-020.5** The user is told when the selection cannot produce teams, and
  the bound they are told must match the bound actually enforced (see F-104).

## Acceptance

- Select four players, navigate to the roster screen, return — the same four
  are still selected.
- Select a player, delete them from the roster, return to the picker — the
  selection contains the remaining players and does not error.
- The guidance shown for an unusable selection agrees with what happens when
  the user tries to generate.

## Web client

**Status:** partial
**Code:** `frontend/src/Game_Time.py`

Selection persistence across page navigation (F-020.3) is handled explicitly:
Streamlit clears widget keys on page change, so the selection is mirrored into
`st.session_state.persistent_selected_players` and re-seeded when the widget
key is absent, filtered against players that still exist (F-020.4).

**Known gaps:**

- **Violates F-020.5.** Three different bounds are in play: the label says
  "Choose 2-18 players", the guards enforce a minimum of 2 and a maximum of
  20, and the algorithm rejects anything under 4. Selecting 2 or 3 players
  therefore shows no warning, enables the generate action, and then fails.
  See F-104.

## History

- 2026-09-05 — Created from an audit of the existing web and iOS clients.
