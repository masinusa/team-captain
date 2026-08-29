# Team-Selection Algorithm Spec

This document is the source of truth for porting the team-selection algorithm
to a new platform (e.g. native Swift for `team-picker-ios`, native Kotlin for
`team-picker-android`). It must run **entirely locally, with no network
calls** — the reference implementation lives in
`frontend/src/algorithm/` in this repo (Python).

Validate any port against `tests/fixtures/algorithm_cases.json`, which pins
down the exact values for the deterministic parts of this spec below.

## Player

Fields:
- `name: string`
- `offense: int`, range 0-5
- `distribution: int`, range 0-5
- `defense: int`, range 0-5
- `injury_handicap: float`, range -3.0 to 3.0

Derived properties:
- `offense_defense_ratio = offense / defense`, or `0` if `defense == 0`.
- `overall_score = mean(offense, distribution - injury_handicap, defense)`.

## Team

A team is a list of players. Derived properties are the arithmetic mean
across all players on the team:
- `average_od_ratio` = mean of each player's `offense_defense_ratio`
- `average_distribution` = mean of each player's `distribution`
- `average_overall_score` = mean of each player's `overall_score`

## select_teams(players) -> (team1, team2)

Requires at least 4 players. Reference: `frontend/src/algorithm/algorithm.py`.

1. Shuffle the player list randomly.
2. **Initial balanced partition**: sort players by `offense_defense_ratio`
   descending, then greedily assign each player to whichever of the two
   teams currently has the lower running sum of `offense_defense_ratio`
   (see `algorithm_utils.balanced_partition`).
3. Identify the two players with the lowest `distribution` scores — these
   two must never end up on the same team.
4. Define a variance/cost function between two teams:
   ```
   variance(t1, t2) = (
       |t1.average_od_ratio - t2.average_od_ratio|
       + 1.5 * |t1.average_distribution - t2.average_distribution|
       + |t1.average_overall_score - t2.average_overall_score|
   ) ** 2
   ```
   (distribution balance is weighted 1.5x more heavily than the other two
   terms).
5. **Local search refinement**: repeatedly try swapping a pair of players
   from team1 with a pair from team2 (only ~25% of candidate swaps are
   actually evaluated, chosen at random each time, to keep this fast and add
   variety run-to-run). Skip any swap that would put both of the two lowest
   `distribution` players on the same team. Keep whichever swap minimizes
   `variance()`, and keep iterating until all pairs have been considered.
6. Return the two teams with the lowest variance found.

**Note on determinism**: steps 1 and 5 are intentionally randomized (a
different valid team split may come back on each run, even for the same
input). A native port does not need to reproduce the exact same team
assignment as the Python reference — it needs to reproduce the same *scoring
formulas* (Player/Team properties above, pinned by the fixtures file) and the
same general approach (balanced initial partition + swap-based local search
minimizing the variance function above, keeping the two lowest-distribution
players apart).

## create_visualization(team)

Assigns each player on a team to a soccer formation position based on team
size (see `TEAM_POSITION_MAPPINGS` and `POSITION_DATA_INDEX` in
`frontend/src/algorithm/visualizations.py`), then renders a pitch diagram
with each player's name at their assigned position. This is a
web-app-specific rendering detail (matplotlib/mplsoccer) — native ports
should build their own UI for showing the two resulting teams, using
whatever positional/visual treatment fits the platform; it does not need to
match the Python rendering pixel-for-pixel.
