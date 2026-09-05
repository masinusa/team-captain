---
id: F-021
title: Team generation
area: Team generation & display
status: active
origin: web
related: [F-020, F-022, F-100, F-101, F-104]
---

# F-021 — Team generation

## Requirement

- **F-021.1** In a single action, the user can split the selected players
  (F-020) into two teams balanced according to F-101.
- **F-021.2** Generation runs entirely on the device. No network call is made,
  and the feature works with no connectivity.
- **F-021.3** At least four players are required. A smaller selection is
  refused with a message that says so, before the user commits to the action
  where possible.
- **F-021.4** Generating again on the same selection may produce a different
  valid split — the algorithm is deliberately randomized (F-101).
- **F-021.5** Every selected player appears on exactly one of the two teams.
- **F-021.6** Failure to generate leaves the previous state intact and shows a
  message; it never leaves a partially-formed result on screen.

## Acceptance

- Four players produce two teams of two, together containing all four exactly
  once.
- Generating twice on the same seven players may yield different splits; both
  must satisfy F-021.5.
- Three players are refused, and the refusal explains the four-player minimum.
- With networking disabled, generation still succeeds.

## Web client

**Status:** implemented
**Code:** `frontend/src/Game_Time.py` ("Split Teams" button →
`frontend/src/algorithm/algorithm.py`)

The algorithm runs in-process; the former network backend was removed in
commit `2054810`.

**Known gaps:**

- **Violates F-021.3** in the pre-commitment sense: the four-player minimum is
  enforced only by the exception raised inside the algorithm, so a selection
  of 2 or 3 reaches the button before failing. See F-020 and F-104.
- Results are not retained. Any subsequent interaction reruns the script and
  the generated teams vanish until the user generates again — arguably a
  violation of the spirit of F-021.6.
- A team of 11 or more raises an uncaught `KeyError` from the position
  mapping (see F-103); only `ValueError` is handled here.

## History

- 2026-09-05 — Created from an audit of the existing web and iOS clients.
