---
id: F-045
title: Game review link
area: Game recording & history
status: active
origin: web
related: [F-040, F-041, F-043, F-081]
---

# F-045 — Game review link

## Requirement

- **F-045.1** A user can create a game-review session for a game date and
  receive a shareable link where players can rate how balanced the teams felt
  and leave optional notes.
- **F-045.2** When the final score and rosters are already known at creation
  time (e.g. creating the link from a saved game in Game History), the client
  sends that snapshot so the review page can show it read-only. It is not
  re-collected from each reviewer, and disagreement between reviewers about
  the score is not possible by construction.
- **F-045.3** The review page shows every rating and note submitted so far,
  not just the latest, so reviewers can see what others said before adding
  their own.
- **F-045.4** The client makes the link available through its platform's
  normal sharing mechanism.
- **F-045.5** A creation failure is shown to the user and does not prevent
  local game and team-management features from working.
- **F-045.6** Session creation is intentionally public while the product has
  no sign-in or organizer-role system. The client must not claim that a
  request is restricted to official apps or authorized users.

## Acceptance

- Given a configured Game Review service and a game date, creating a session
  returns a public link that the user can open or share.
- Given a session created with a score/roster snapshot, the review page shows
  that score and both rosters read-only, and reviewers are only asked to rate
  balance and add notes.
- Given a session created without a snapshot, the review page omits the score
  section entirely; balance rating and notes still work.
- The review page lists every submission recorded so far.
- With the service unreachable or returning an error, the user receives a
  visible failure and can still use local features.
- A caller can create a session without an app account; the known security and
  cost risk is documented rather than hidden.

## Web client

**Status:** implemented
**Code:** `frontend/src/pages/Game_History.py`, `frontend/src/game_review_service.py`

Creates a session from a saved game in Game History, after the game has been
played — the final score and both rosters are already known, so they're sent
as the snapshot, matching iOS. There is no longer a way to create a link
before a game is played; that pre-game path (which only ever sent a bare
`game_date`, no snapshot) was removed once Game History gave web a real score
to attach. Each roster entry also sends the player's four raw component
scores — `offense`/`distribution`/`defense`/`modifier` (F-100) — read from
the frozen roster snapshot at link-creation time, not a single collapsed
`overall_score`/ranking: the game-review service stores these independently
so nothing has to un-average them later. These are the same skill values the
app used when the teams were built, not a live link to the player's current
rating. This lets the game-review service use them, alongside balance
ratings, to train a team-balancing model later, matching iOS's four fields
exactly.

**Known gaps:** The service URL is still supplied through
`GAME_REVIEW_SERVICE_URL`. The public endpoint can be called by any internet
client, not only Team Captain.

## iOS client

**Status:** implemented
**Code:** `TeamCaptain/Views/GameHistoryView.swift` (`createReviewSession()`),
`TeamCaptain/AppSettings.swift` (`GameReviewService`)

Creates a session from a saved game in Game History, after the game has been
played — the final score and both rosters are already known, so they're sent
as the snapshot. Real player names are always sent, regardless of the
`hideNamesFromHistory` setting (that setting only affects the organizer's own
local history view). Each roster entry also sends the player's four raw
component scores — `offense`/`distribution`/`defense`/`modifier` (F-001.3) —
not a single collapsed `overallScore`/ranking: the game-review service
stores these independently so nothing has to un-average them later. Each
score is independently optional and frozen at link-creation time like the
score, not a live link to the player's current rating. This lets the
game-review service use them, alongside balance ratings, to train a
team-balancing model later.

## History

- 2026-09-06 — Added public Game Review session creation for the web and iOS
  clients. No sign-in exists yet, so unrestricted creation is an explicit
  temporary security and cost concern.
- 2026-09-06 — Redesigned the review page: it no longer crowdsources the
  final score or goal scorers from reviewers. iOS now sends a one-time
  score/roster snapshot at link creation (from Game History, where that data
  is already known), shown read-only; reviewers only rate team balance and
  add optional notes, and can see everyone else's ratings.
- 2026-09-06 — iOS roster entries now also include each player's
  `overallScore` as an optional `ranking` snapshot, for downstream
  balance-model training. Web still cannot send it — score capture doesn't
  exist there yet, and score/roster/ranking are one all-or-nothing bundle
  server-side — so this is iOS-only for now; documented as a known gap on
  the web client.
- 2026-09-06 — Web gained Game History (F-040–F-044), closing the gap above:
  the pre-game, snapshot-less link-creation path was removed, and review
  links are now only created from a saved game, always with a real
  score/roster/`ranking` snapshot — matching iOS.
- 2026-09-06 — Corrected both clients' roster-entry payload: the game-review
  service changed to store each player's four component scores
  (`offense`/`distribution`/`defense`/`modifier`) independently rather than
  one collapsed `ranking` number, and both clients had been sending the old
  `ranking`-only shape — silently dropped by the service, since it only
  recognizes those four field names. iOS's `RosterPlayer` and web's
  `_roster_payload()` now send the four raw scores (already available on
  both clients' own player models/snapshots) instead of a computed
  `overallScore`/`overall_score`.
