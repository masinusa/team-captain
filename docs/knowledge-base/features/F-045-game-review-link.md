---
id: F-045
title: Game review link
area: Game recording & history
status: active
origin: web
related: [F-040, F-081]
---

# F-045 — Game review link

## Requirement

- **F-045.1** A user can create a game-review session for a game date and
  receive a shareable link where players can submit the final score, goal
  scorers, and a balance assessment.
- **F-045.2** The client makes the link available through its platform's
  normal sharing mechanism.
- **F-045.3** A creation failure is shown to the user and does not prevent
  local game and team-management features from working.
- **F-045.4** Session creation is intentionally public while the product has
  no sign-in or organizer-role system. The client must not claim that a
  request is restricted to official apps or authorized users.

## Acceptance

- Given a configured Game Review service and a game date, creating a session
  returns a public link that the user can open or share.
- With the service unreachable or returning an error, the user receives a
  visible failure and can still use local features.
- A caller can create a session without an app account; the known security and
  cost risk is documented rather than hidden.

## Web client

**Status:** implemented
**Code:** `frontend/src/Game_Time.py`

**Known gaps:** The service URL is supplied through
`GAME_REVIEW_SERVICE_URL`, and creation is available after a team split. The
public endpoint can be called by any internet client, not only Team Captain.

## History

- 2026-09-06 — Added public Game Review session creation for the web and iOS
  clients. No sign-in exists yet, so unrestricted creation is an explicit
  temporary security and cost concern.
