---
name: propagate-to-siblings
description: Use whenever you change user-visible behavior, the data model, the team-selection algorithm, or a shared API contract in team-captain, and whenever you add or retire a requirement. Records the change in the knowledge base, ports it to team-captain-ios and team-captain-android, and updates each sibling's status file even when that sibling cannot implement the change.
---

# Propagate a change through the knowledge base

`team-captain` owns the requirements. `../team-captain-ios` and
`../team-captain-android` are separate git repos checked out beside it (not
submodules), each with its own native implementation and its own status file.

- Source of truth: `docs/knowledge-base/` in this repo.
- Each sibling mirrors **status only**, in `docs/knowledge-base/STATUS.md`.
  A sibling never restates a requirement; it links back by ID.

## When to use this

Any change with behavioral surface:

- added, removed, or altered a user-visible capability
- changed the player/team/game data model or a field range
- changed the team-selection algorithm or its scoring rules
- changed a shared API contract (once one exists)
- found an inconsistency worth recording

Skip only for changes with no behavioral surface — formatting, comments,
tooling, dependency bumps. When you skip, put `No KB impact: <reason>` in the
commit body rather than skipping silently.

## Workflow

### 1. Check the knowledge base is internally consistent

Confirm both siblings exist. If one is missing, stop and tell the user.

From `docs/knowledge-base/`, check that every file has an INDEX row and that
every INDEX link resolves. A row with **no** file is normal — that is a
reserved ID — so do not flag it.

```bash
comm -23 <(ls features algorithm | grep -oE '^F-[0-9]{3}' | sort -u) \
         <(grep -oE '^\| `F-[0-9]{3}' INDEX.md | grep -oE 'F-[0-9]{3}' | sort -u)

grep -oE '\]\((features|algorithm)/[^)]+\)' INDEX.md | tr -d ']()' \
  | while read -r p; do [ -f "$p" ] || echo "MISSING: $p"; done
```

Both must print nothing. Then check that no ID is missing from a sibling's
table:

```bash
for s in ios android; do
  echo "== $s"
  diff <(grep -oE '^\| `F-[0-9]{3}' INDEX.md | grep -oE 'F-[0-9]{3}' | sort -u) \
       <(grep -oE '\| `F-[0-9]{3}' ../team-captain-$s/docs/knowledge-base/STATUS.md \
         | grep -oE 'F-[0-9]{3}' | sort -u)
done
```

Repair any gaps as part of this run. They are cheap now and compounding later.

### 2. Update the knowledge base first

Before the code, so the requirement survives even if the port is abandoned.

- Identify the affected IDs. For a genuinely new capability, claim the next
  free ID from the counter block at the top of `INDEX.md`, increment it, and
  create the file from the template in `docs/knowledge-base/README.md`.
- Never reuse or renumber an ID. Retirement uses `status: withdrawn` /
  `superseded-by:` — see the README.
- Update `## Requirement` (platform-neutral wording), `## Acceptance`, and
  `## Web client`.
- Record anything you found but did not fix under `## Known gaps`. Recording
  is always in scope; fixing is a separate decision — and if the finding is a
  conflict between the spec and the code, **do not resolve it by editing one
  to match the other.** Write it down as open and tell the user.
- Append one dated line to `## History`, and update the `INDEX.md` row.

### 3. Commit this repo

One commit containing the code change **and** the knowledge-base change.

### 4. Port to each sibling — iOS first, then Android

For each sibling, in order:

**a.** Read its `STATUS.md` row for the affected IDs, and its
`docs/knowledge-base/pitfalls/` before touching the build.

**b.** Check its working tree with `git status` **before editing anything**.
If it is already dirty, note which files were dirty on arrival — you must not
sweep the user's in-progress work into your commit.

**c.** Decide one of:

- **Port it** — idiomatic Swift/Kotlin implementing the requirement. Match
  behavior and the `## Acceptance` cases, not the Python's structure.
- **Cannot port** — no app code yet, missing platform capability, or blocked
  on another ID. A legitimate outcome, not a skip.
- **Not applicable** to this platform, with a written reason.

**d.** If the algorithm or fixtures changed, copy
`tests/fixtures/algorithm_cases.json` verbatim and update the sha256 line in
the sibling's `STATUS.md` header:

```bash
shasum -a 256 tests/fixtures/algorithm_cases.json
```

The sibling's hash must equal this repo's. If the sibling has no harness
consuming the fixture, say so in your report — do not quietly accept it.

**e.** Update `STATUS.md` **in every case, including "cannot port"**, using the
closed vocabulary from `docs/knowledge-base/README.md`:
`implemented | partial | deviates | not implemented | n/a | blocked`.

- `partial` must name the missing clause (e.g. "missing F-002.3")
- `deviates` must cite the clause it knowingly differs from
- `n/a` must give a reason
- update the `Reconciled against team-captain commit:` line to the SHA from
  step 3
- anything longer than a table cell goes in `pitfalls/<topic>.md`

**f.** If you hit a platform gotcha, append an entry to
`docs/knowledge-base/pitfalls/`. An entry without an actionable rule is a
diary, not a knowledge base.

**g.** Build/test per that repo's `AGENTS.md`, then commit that repo
separately, naming the affected IDs in the subject:

```
F-002: allow a rating of 0 on the add-player form
```

**If the tree was dirty on arrival, stage only the paths you touched**
(`git add <explicit paths>`). Never `git add -A` in a sibling. Never push
unless asked.

### 5. A sibling that cannot implement the change still gets a commit

`team-captain-android` is an empty scaffold — no Gradle, no Kotlin. **Do not
bootstrap a project to satisfy a propagation.** Add or update the `STATUS.md`
row as `not implemented`, leave `Code` as `—`, and commit the KB-only change.

The reason is that the moment Android is bootstrapped, its `STATUS.md` is a
complete, ordered work list. An ID that never reaches a sibling's table is
invisible there forever — that is the most likely way this whole scheme decays.

The same applies to iOS for anything you choose not to port now.

### 6. Report back

End with one row per repo:

| Repo | IDs touched | Code | KB | Build/test | Notes |
|---|---|---|---|---|---|

Call out explicitly: IDs left `not implemented`, any `deviates` rows you
created, fixture hash mismatches, and any pre-existing dirty working tree you
deliberately left alone.
