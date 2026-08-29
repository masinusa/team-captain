# team-captain

Algorithmically choose your soccer teams.

This is the **web** client (Streamlit) and the project's documentation hub.
It runs entirely locally/offline — the team-selection algorithm executes
in-process, with no server to reach.

Sibling repos, each a native app with their own local implementation of the
same algorithm (see [docs/algorithm_spec.md](docs/algorithm_spec.md)):
- [team-captain-ios](https://github.com/masinusa/team-captain-ios) — native SwiftUI
- [team-captain-android](https://github.com/masinusa/team-captain-android) — native Kotlin

See [docs/system_architecture.md](docs/system_architecture.md) for the overall
architecture.

## Running locally

```
make install
make run
```

Or directly:
```
pip install -r frontend/docker/requirements.txt
cd frontend/src && streamlit run Game_Time.py
```
