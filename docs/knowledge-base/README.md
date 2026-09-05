# Knowledge base

This directory is the **source of truth for what Team Captain does** — across
all three clients, not just this one. `team-captain` happens to host the docs,
but it is a client like the others, and its own gaps are recorded here honestly.

Requirements are written platform-neutrally. Streamlit / SwiftUI / Compose
vocabulary belongs in a `## Web client` block or in a sibling repo's
`STATUS.md`, never in a `## Requirement`.

## Layout

```
docs/knowledge-base/
  README.md      this file — the rules and the template
  INDEX.md       every ID, plus the next-free-ID counters
  features/      user-facing capabilities   (F-001 … F-099)
  algorithm/     the selection algorithm    (F-100 … F-199)
```

The sibling repos each hold a `docs/knowledge-base/STATUS.md` that references
these IDs and records what is true on that platform.

## ID blocks

| Block | Area |
|---|---|
| `F-001`–`F-019` | Player management |
| `F-020`–`F-039` | Team generation & display |
| `F-040`–`F-059` | Game recording & history |
| `F-060`–`F-079` | Settings & privacy |
| `F-080`–`F-099` | Platform & runtime characteristics |
| `F-100`–`F-199` | Algorithm |

Filename is `F-0NN-kebab-title.md`. The ID is canonical and immutable; the
slug is a convenience. Change a slug only in a commit that does nothing else.

**Claim an ID by incrementing the counter block at the top of `INDEX.md` in the
same commit that creates the file.** Two branches claiming the same number will
conflict on that line, which is the point.

### Clause numbering

Number the bullets under `## Requirement` as `F-021.1`, `F-021.2`, … These are
line anchors, not separate IDs. They exist so a sibling can say *exactly* which
clause it does not yet satisfy — without them, a status of "partial" carries no
information.

### IDs are never reused

A retired feature keeps its file and its number forever.

- **Withdrawn** — capability removed from the product. Body is replaced by a
  short tombstone; set `status: withdrawn`. Sibling `STATUS.md` rows stay, so a
  platform still shipping the code has a standing reminder to remove it.
- **Superseded** — rewritten under a new ID. Old file gets
  `superseded-by: F-0NN`; new file gets `supersedes: [F-0MM]`.
- **Split** — one requirement becomes two. Old file gets `status: split` and
  points at both successors, which take fresh numbers from the counter. Never
  `F-021a`.

## Feature file template

Copy this. Five headings, then stop.

```markdown
---
id: F-0NN
title: <short title>
area: <one of the block names above>
status: active
origin: <web | ios | android>
related: []
---

# F-0NN — <short title>

## Requirement

- **F-0NN.1** <what the user shall be able to do, platform-neutral>
- **F-0NN.2** …

## Acceptance

- <a concrete case that distinguishes correct from incorrect>

## Web client

**Status:** <implemented | partial | not implemented | n/a>
**Code:** `path/to/file.py`

**Known gaps:** <inconsistencies found but not yet fixed — record, don't hide>

## History

- YYYY-MM-DD — <what changed and why>
```

`origin` records which client the requirement came from. Several features here
originated on iOS and are not implemented on the web; that is expected and is
exactly what the KB is for.

`## Known gaps` is where a discovered inconsistency gets written down rather
than lost. Recording a gap is always in scope; fixing it is a separate decision.

`## History` is append-only, one dated line per change. It is the only place
that answers "when did this requirement change, and why" — which is what a
sibling agent needs when it finds its port out of date.

## Status vocabulary

Both here and in sibling `STATUS.md` files, status is one of exactly:

| Value | Meaning |
|---|---|
| `implemented` | Satisfies every clause |
| `partial` | Built, but a clause is missing — **name the clause** |
| `deviates` | Works, but knowingly differs — **cite the clause** |
| `not implemented` | Nothing built yet |
| `n/a` | Does not apply to this platform — **give a reason** |
| `blocked` | Cannot proceed — **name the blocker** |

## Keeping INDEX.md honest

If `INDEX.md` and a feature file disagree, **the feature file wins** — fix the
row. A stale row is therefore never load-bearing.

A row with no file is **normal** — that is a reserved ID. The drift that hurts
is a file with no row, or a link that does not resolve. From this directory:

```bash
# files with no INDEX row — must be empty
comm -23 <(ls features algorithm | grep -oE '^F-[0-9]{3}' | sort -u) \
         <(grep -oE '^\| `F-[0-9]{3}' INDEX.md | grep -oE 'F-[0-9]{3}' | sort -u)

# INDEX links that do not resolve — must be empty
grep -oE '\]\((features|algorithm)/[^)]+\)' INDEX.md | tr -d ']()' \
  | while read -r p; do [ -f "$p" ] || echo "MISSING: $p"; done
```

The `propagate-to-siblings` skill runs these at the start of every propagation.
