# Agent notes for team-captain

This repo is one of three sibling apps for the same product, checked out
side by side on disk (not submodules):

- `team-captain` (this repo) — Streamlit web client, Python
- `../team-captain-ios` — native SwiftUI client
- `../team-captain-android` — native Kotlin client (scaffold only, no app code)

Today each app is fully independent and offline (see
[docs/system_architecture.md](docs/system_architecture.md)) — there is no
shared backend. Shared cloud infrastructure across all three apps is planned
for future work, so treat any backend/API design here as something the other
two clients will eventually need to match too.

## Knowledge base

**[docs/knowledge-base/](docs/knowledge-base/) is the source of truth for what
the product does** — across all three clients, not just this one. Read
[its README](docs/knowledge-base/README.md) before adding or changing an entry.

Two things about it are easy to get wrong:

1. **It is the union, not a description of the web app.** Eleven requirements
   in it originated on iOS and have no web implementation. Each entry records
   this repo's own status in a `## Web client` block, and `not implemented` is
   a normal value there.
2. **This repo is a client too.** When the web app is behind, say so in the
   entry. Do not quietly narrow a requirement to match what Streamlit does.

Requirements are written platform-neutrally. Streamlit vocabulary belongs in a
`## Web client` block, never in a `## Requirement`.

Requirement IDs (`F-021`, and clause anchors like `F-021.3`) are immutable and
never reused. Claim a new one by incrementing the counter block at the top of
[docs/knowledge-base/INDEX.md](docs/knowledge-base/INDEX.md) in the same commit
that creates the file.

### Definition of done

A change with any behavioral surface is not finished until:

- the affected entry's `## Requirement` and `## Web client` reflect it,
- `INDEX.md` agrees, and
- the code change and the knowledge-base change are in the **same commit** —
  they are the same fact, and splitting them is how the KB goes stale.

If a change genuinely has no knowledge-base impact — formatting, comments,
tooling, dependency bumps — say so explicitly in the commit body:

```
No KB impact: <reason>
```

Writing the reason down is the point; `git log --grep='No KB impact'` then
gives a cheap audit of every skipped decision.

## Cross-repo changes

Some things must stay consistent across all three apps even though each has
its own native implementation:

- The team-selection algorithm — normative definitions in
  [docs/knowledge-base/algorithm/](docs/knowledge-base/algorithm/), long-form
  prose in [docs/algorithm_spec.md](docs/algorithm_spec.md). **Where the two
  disagree, the knowledge base wins** and the spec should be corrected.
- Any future shared cloud API/data contract.

Use the `propagate-to-siblings` skill for these. "Equivalent" means matching
behavior in idiomatic Swift/Kotlin — not a literal copy of the Python diff.

Purely web-app-specific changes (Streamlit layout, this repo's SQLite schema,
Python-only tooling) still need a knowledge-base entry if they change what the
user can do, but do not need porting.

## Test fixtures

`tests/fixtures/algorithm_cases.json` is owned by this repo and copied verbatim
into both siblings. Changing it means re-copying to both in the same
propagation.

**No repository currently has a harness that runs it.** It is dead weight in
all three repos, which is why the `F-101` discrepancy went unnoticed. Building
a harness here is the highest-leverage available work — mention it if the user
asks what to do next.

## The player database is real people's data

`frontend/data/player_database.db` holds ~70 real names, each with skill
ratings and in some cases a free-text note about that person. Treat it as
personal data, not test fixtures.

- **Never commit it, never paste its contents, never copy it into a scratch
  directory that outlives the task.** When you need to inspect it, redact
  names in anything you print.
- The ignore globs are `*.db`, `*.db.*`, `*.sqlite`, `*.sqlite3`. Keep them
  wide. A plain `*.db` once failed to match `player_database.db.bak-68players`,
  leaving a full copy untracked-but-committable.
- It has already leaked once. A copy reached this repo's public history and
  the only complete fix was deleting and recreating the GitHub repo.

If you ever have to purge something from history again, two things cost real
time last round and are worth knowing up front:

1. **Enumerate every historical path first.** The database lived at
   `services/web_frontend_streamlit/data/player_database.db` before the repo
   reorganization. Filtering only its current path left the data in branches
   that predate the move. Run
   `git rev-list --all --objects | grep -i <name>` and filter *all* the paths
   it returns, in one pass.
2. **A force-push does not remove anything from GitHub.** Unreferenced objects
   stay fetchable by exact SHA until GitHub garbage-collects, which you cannot
   trigger. Only deleting the repository, or a GitHub Support request, actually
   removes them. Verify with a fresh clone plus a direct
   `git fetch origin <old-sha>` — do not assume.

## Working alongside other sessions

This project is often worked on by several Claude sessions at once, in git
worktrees under `~/orca/workspaces/team-captain/`. Before anything destructive:

- **Never `git worktree remove --force` a worktree you did not create.** That
  flag exists specifically to override the refusal to delete uncommitted work.
- **Re-check `git status` immediately before acting on it.** A clean reading
  goes stale in minutes when another session is live — a worktree that reported
  zero dirty files was deleted minutes later with 21 new files in it.
- Prefer committing another session's work to a branch over deleting it.

If work is lost this way it is usually recoverable: the session transcripts in
`~/.claude/projects/<encoded-cwd>/*.jsonl` record every `Write` and `Edit` tool
call with full content. Replaying them in timestamp order reconstructs the
files exactly.

## Running locally

```
make install
make run
```
