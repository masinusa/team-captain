---
id: F-083
title: Cloud backup and sync
area: Platform & runtime characteristics
status: active
origin: web
related: [F-006, F-080, F-081, F-084]
---

# F-083 — Cloud backup and sync

## Requirement

- **F-083.1** The user can back up their roster and restore it on another
  device, so data survives losing or replacing a device.
- **F-083.2** Sync is an **explicit user action**, never automatic and never
  required. The app works fully offline (F-081); with no connectivity only the
  sync action itself is unavailable.
- **F-083.3** A user's data is private to them. One account can never read or
  write another account's data, and this is enforced by the storage service
  itself, not only by the client.
- **F-083.4** Sync merges **per player**, keyed by the identifier from F-006.
  For a given player the record with the newer `updated_at` wins. A player
  present on only one side is added to the other.
- **F-083.5** Deletions propagate as tombstones (F-006.6). A deletion can lose
  to a newer edit on another device — that is intended, not a bug.
- **F-083.6** Sync never silently discards a player. Whole-roster replacement
  is not acceptable.
- **F-083.7** Restoring is idempotent: restoring the same payload twice leaves
  the roster identical.
- **F-083.8** Sync requires an account only when the user opts in. All local
  roster features remain available while signed out, offline, or after sync is
  disabled.
- **F-083.9** Sync runs only after an explicit user request. It does not
  silently upload, download, retry, or change local records in the background.
- **F-083.10** The sync service derives the account identity from verified
  credentials, never from a client-supplied account identifier, and stores
  each account's records in an isolated namespace.
- **F-083.11** If two records have equal `updated_at` values but different
  contents, every client and service uses the same documented deterministic
  tie-breaker so repeated syncs converge.

## Acceptance

- Add a player on each of two devices, sync both — both players exist on both.
- Edit the same player on both devices, sync — the newer edit wins and the
  older is not silently reintroduced later.
- Delete on one device, sync twice — the player stays deleted.
- Turn off networking: every roster operation still works; only sync fails, and
  it fails with a message rather than an error.
- A second account cannot read the first account's stored data.
- A signed-out user can create, edit, and delete local players with no network
  request or account prompt.
- A signed-in user who does not tap Sync makes no network request.
- Two different records with equal timestamps converge to the same result
  after each device syncs again.

## Sync API

The version-1 endpoint is `POST /v1/players/sync`. It accepts a F-006
version-1 player envelope and an authenticated request. The service derives
the caller's account from verified credentials, transactionally merges the
submitted records with only that account's stored records, and returns the
complete canonical version-1 envelope. The request must be rejected without
mutation when its schema version, record fields, identifier casing, timestamp
format, field ranges, collection shapes, roster size, or body size is invalid.

For each identifier, the newer `updated_at` wins. When timestamps are equal,
the UTF-8 bytewise ordering of a canonical JSON encoding with lexicographically
sorted keys and arrays in their stored order chooses the greater record. This
tie-breaker is deterministic, content-based, and does not depend on a device
or request arrival order.

## Scope at version 1

**Players only.** The web client has no game history at all — no games table,
nothing persisted — so there is nothing to sync on that side. The shared record
(F-006) reserves an empty `games` key so history sync can be added later
without a schema change.

## Web client

**Status:** partial
**Code:** `frontend/src/cloud_sync.py`, `frontend/src/pages/Settings.py`

The web client offers opt-in Firebase email/password account actions and an
explicit Sync now action. It has no network activity unless a user invokes an
account or sync action, and it keeps authentication state only in the Streamlit
session.

**Known gaps:**

- The GCP sync service is not deployed or configured for a real Firebase
  project, so the UI remains unavailable until its public configuration is
  supplied.
- iOS and Android do not yet have a released, configured sync service client.

## History

- 2026-09-06 — Created alongside F-006, which it depends on: sync is only safe
  once players have stable cross-device identifiers.
- 2026-09-06 — Defined the generic opt-in, account-isolated manual-sync
  protocol and deterministic equal-timestamp conflict rule for a future GCP
  implementation.
- 2026-09-06 — Added the opt-in web account and manual-sync client foundation;
  production service deployment and client configuration remain deferred.
