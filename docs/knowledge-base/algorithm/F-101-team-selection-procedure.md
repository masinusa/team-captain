---
id: F-101
title: Team selection procedure
area: Algorithm
status: active
origin: web
related: [F-021, F-100, F-102, F-104]
---

# F-101 — Team selection procedure

Normative definition of `select_teams(players) -> (team1, team2)`.

## Definition

- **F-101.1** Requires at least four players; fewer raises an error (F-104).
- **F-101.2** The player list is shuffled before partitioning.
- **F-101.3** **Initial partition.** Sort players by `offense_defense_ratio`
  descending, then assign each in turn to whichever team currently has the
  lower running sum of that ratio.
- **F-101.4** **Separation constraint.** The two players with the lowest
  `distribution` must not end up on the same team.
- **F-101.5** **Cost function.**
  ```
  variance(t1, t2) = ( |t1.avg_od_ratio     - t2.avg_od_ratio|
                     + 1.5 * |t1.avg_distribution - t2.avg_distribution|
                     + |t1.avg_overall_score - t2.avg_overall_score| ) ** 2
  ```
  Distribution balance is weighted 1.5× the other two terms.
- **F-101.6** **Local search.** Consider swapping a pair of players from team 1
  with a pair from team 2. Roughly 25% of candidate swaps are evaluated,
  chosen at random, both to bound the cost and to add run-to-run variety. Any
  swap that would violate F-101.4 is skipped.
- **F-101.7** Return the lowest-variance pair of teams found.
- **F-101.8** The result is **not** deterministic. F-101.2 and F-101.6 are
  randomized by design, so the same input may yield different valid splits.
  A port must reproduce the *scoring formulas* (F-100, F-102) and this general
  approach — not a specific assignment.

## Known gaps

**Open discrepancy — the spec and both implementations disagree, and the
implementations agree with each other.**

`docs/algorithm_spec.md` step 5 reads: *"Keep whichever swap minimizes
`variance()`, and keep iterating until all pairs have been considered."* That
wording describes a hill-climb in which the teams evolve — each accepted swap
becomes the new baseline for the next comparison, so a run can apply many
swaps.

Neither implementation does that:

- `frontend/src/algorithm/algorithm.py` scores every candidate swap against
  the *initial* partition (`team1`/`team2` are never reassigned inside the
  loop) and tracks only `min_var_team1`/`min_var_team2`.
- `team-captain-ios`'s `TeamSelector.selectTeams` does the same.

So both apply **at most one swap per run**. Whether the intended behavior is
one best swap or an iterated hill-climb is a product decision and is **not
settled here** — F-101.6 above is deliberately worded to describe what the code
does, and this section records that the spec prose asks for something stronger.

Deciding it matters: an iterated search would produce measurably better-balanced
teams, and would change results on every platform at once.

Two lesser divergences between the two implementations, both consequences of
the sampling in F-101.6 rather than of intent:

- The Python version walks candidate pairs with a hand-rolled index dance,
  the Swift version with clean nested `i<j` / `k<l` loops. They therefore do
  not enumerate the same candidate set, so their 25% samples are not drawn
  from the same population.
- `random.shuffle(players)` in Python mutates the caller's list in place, and
  `select_teams` prints diagnostics to stdout. The Swift port does neither.

## Web client

**Status:** implemented
**Code:** `frontend/src/algorithm/algorithm.py`,
`frontend/src/algorithm/algorithm_utils.py` (`balanced_partition`)

## History

- 2026-09-05 — Created from an audit of the existing web and iOS clients.
  Recorded the spec-vs-implementation discrepancy above as open.
