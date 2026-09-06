# Requirements index

Every allocated ID, whether or not its file has been written yet. Rows without
a file are reserved: the ID is fixed, the requirement is known, and the entry
gets written the first time someone touches that area.

If this table and a feature file disagree, **the feature file wins** — fix the
row here.

`Web` is the status of *this* repo's Streamlit client. Sibling status lives in
each sibling's `docs/knowledge-base/STATUS.md`; it is deliberately not mirrored
here, because a column that cannot be updated in the same commit as the fact it
describes is the first thing to rot.

## Next free ID — increment in the same commit that creates the file

```
F-0xx player management ....... 007
F-02x team generation ......... 026
F-04x games & history ......... 045
F-06x settings & privacy ...... 062
F-08x platform & runtime ...... 085
F-1xx algorithm ............... 105
```

## Features

| ID | Title | Origin | Web | File |
|---|---|---|---|---|
| `F-001` | Player roster | web | implemented | [features/F-001-player-roster.md](features/F-001-player-roster.md) |
| `F-002` | Add a player | web | implemented | [features/F-002-add-player.md](features/F-002-add-player.md) |
| `F-003` | Edit a player | web | implemented | — |
| `F-004` | Delete a player | web | implemented | — |
| `F-005` | Search / filter the player list | ios | not implemented | — |
| `F-006` | Player identity, aliases, and duplicate merge | web | not implemented | [features/F-006-player-identity-and-aliases.md](features/F-006-player-identity-and-aliases.md) |
| `F-020` | Player selection for a split | web | implemented | [features/F-020-player-selection.md](features/F-020-player-selection.md) |
| `F-021` | Team generation | web | implemented | [features/F-021-team-generation.md](features/F-021-team-generation.md) |
| `F-022` | Pitch visualization | web | implemented | — |
| `F-023` | Enlarge a pitch diagram | ios | not implemented | — |
| `F-024` | Copy teams as text | ios | not implemented | — |
| `F-025` | Copy a pitch image | ios | not implemented | — |
| `F-040` | Save a game | ios | not implemented | — |
| `F-041` | Per-player goal tracking | ios | not implemented | — |
| `F-042` | Game history list | ios | not implemented | — |
| `F-043` | Game detail view | ios | not implemented | — |
| `F-044` | Game notes | ios | not implemented | — |
| `F-060` | Privacy toggles | ios | not implemented | — |
| `F-061` | Theme / palette parity | web | implemented | — |
| `F-080` | Local persistence | web | implemented | — |
| `F-081` | Offline operation | web | implemented | — |
| `F-082` | Connectivity monitoring | ios | not implemented | — |
| `F-083` | Cloud backup and sync | web | not implemented | [features/F-083-cloud-backup-and-sync.md](features/F-083-cloud-backup-and-sync.md) |
| `F-084` | Record-level merge sync | — | not implemented | — |

## Algorithm

| ID | Title | Origin | Web | File |
|---|---|---|---|---|
| `F-100` | Player scoring model | web | implemented | [algorithm/F-100-player-scoring-model.md](algorithm/F-100-player-scoring-model.md) |
| `F-101` | Team selection procedure | web | implemented | [algorithm/F-101-team-selection-procedure.md](algorithm/F-101-team-selection-procedure.md) |
| `F-102` | Team aggregates | web | implemented | — |
| `F-103` | Formation / position mapping | web | implemented | — |
| `F-104` | Roster size validation | web | partial | — |

## Where the web client is behind

Eleven of the twenty-six requirements above originated on iOS and have no web
implementation: `F-005`, `F-023`, `F-024`, `F-025`, `F-040`–`F-044`, `F-060`,
`F-082`. That is not a defect list — it is the current shape of the product,
recorded so it stays visible.
