Each client is a fully independent, offline-capable app: it owns its local
player database and runs its own local implementation of the team-selection
algorithm (spec: [algorithm_spec.md](algorithm_spec.md)). There is no shared
network backend — nothing here calls out over the internet.

```mermaid
flowchart LR
    subgraph web[team-captain (this repo) - Web]
        SF[Streamlit App]
        SDB[(Player DB)]
        SA[Algorithm - Python]
    end
    subgraph ios[team-picker-ios]
        IF[SwiftUI App]
        IDB[(Player DB)]
        IA[Algorithm - Swift]
    end
    subgraph android[team-picker-android]
        AF[Kotlin App]
        ADB[(Player DB)]
        AA[Algorithm - Kotlin]
    end
```

Each platform's algorithm implementation must follow the same spec and pass
the same test fixtures (`tests/fixtures/algorithm_cases.json`, duplicated
into each repo) to guarantee consistent team-scoring behavior across
platforms — see [algorithm_spec.md](algorithm_spec.md) for details and the
rationale for independent native ports over a shared binary/runtime.
