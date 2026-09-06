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

## Acceptance

- Add a player on each of two devices, sync both — both players exist on both.
- Edit the same player on both devices, sync — the newer edit wins and the
  older is not silently reintroduced later.
- Delete on one device, sync twice — the player stays deleted.
- Turn off networking: every roster operation still works; only sync fails, and
  it fails with a message rather than an error.
- A second account cannot read the first account's stored data.

## Scope at version 1

**Players only.** The web client has no game history at all — no games table,
nothing persisted — so there is nothing to sync on that side. The shared record
(F-006) reserves an empty `games` key so history sync can be added later
without a schema change.

## Web client

**Status:** not implemented
**Code:** `frontend/src/backup.py`, `frontend/src/cloud_sync.py` (both written,
neither wired into the UI, neither run against real infrastructure)

**Known gaps:**

- `backup.py` predates F-006: it matches players on lowercased name, has no
  identifiers, timestamps or tombstones, and upserts without deleting — so it
  resurrects deleted players. It must be rewritten against the shared record.
- `cloud_sync.py` uploads and downloads the whole file with no merge, which
  violates F-083.4 and F-083.6 as written.
- Configuration is read once at import into module-level constants, so values
  set later in a long-running Streamlit process are never picked up.
- `boto3` is imported at module top level, so importing the module at all fails
  when the dependency is absent — a direct risk to F-081.
- `sync_download` treats only `NoSuchKey` as "nothing stored yet". Because the
  IAM design deliberately withholds `s3:ListBucket`, S3 returns `403
  AccessDenied` for a missing object instead, so a user's **first ever sync**
  raises instead of returning empty. Treating 403 as "nothing yet" fixes the
  common case but masks a genuinely broken policy — that ambiguity is accepted
  and recorded here rather than pretended away.
- No AWS resources exist yet. Nothing in this entry has been exercised
  end-to-end.

## History

- 2026-09-06 — Created alongside F-006, which it depends on: sync is only safe
  once players have stable cross-device identifiers.
