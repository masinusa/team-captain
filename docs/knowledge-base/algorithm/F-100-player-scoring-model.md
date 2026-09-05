---
id: F-100
title: Player scoring model
area: Algorithm
status: active
origin: web
related: [F-001, F-101, F-102]
---

# F-100 — Player scoring model

Normative definition. `docs/algorithm_spec.md` is the long-form prose version;
where the two disagree, this file wins and the spec should be corrected.

## Definition

Given a player with integer ratings `offense`, `distribution`, `defense`
(each 0–5) and a real `injury_handicap` in −3.0…3.0:

- **F-100.1** `offense_defense_ratio = offense / defense`, and exactly `0`
  when `defense == 0`. The zero case is a defined result, not an error.
- **F-100.2** `overall_score = mean(offense, distribution - injury_handicap,
  defense)` — the arithmetic mean of those three terms.
- **F-100.3** A negative `injury_handicap` therefore *raises* a player's
  overall score. This is intended.
- **F-100.4** These two values are pure functions of the player's fields. They
  must be identical on every platform, to within floating-point tolerance.

## Fixture coverage

`tests/fixtures/algorithm_cases.json` pins F-100.1–F-100.3 with four players:

| Case | Pins |
|---|---|
| Alice, Cara | ordinary values |
| Bob | negative `injury_handicap` raising the score (F-100.3) |
| Dan | `defense == 0` → ratio `0` (F-100.1) |

**No repository currently has a test harness that runs this fixture.** It is
copied verbatim into `team-captain-ios` and `team-captain-android` and read by
nothing. Building a harness is the single highest-leverage piece of work
against this KB: it would have caught the F-101 discrepancy below.

## Naming

The spec calls this field `injury_handicap`. Both the web client (DB column
and UI label) and the iOS `Player` struct call it `modifier`. The clients agree
with each other and disagree with the spec. Renaming is a migration, so the
divergence is recorded here rather than papered over — treat `modifier` and
`injury_handicap` as the same field.

## Web client

**Status:** implemented
**Code:** `frontend/src/algorithm/data_models/Player.py`

`get_teams()` in `frontend/src/Game_Time.py` renames `modifier` →
`injury_handicap` when constructing the domain model. The `notes` field is
dropped before the algorithm runs; it has no bearing on scoring.

## History

- 2026-09-05 — Created from an audit of the existing web and iOS clients.
