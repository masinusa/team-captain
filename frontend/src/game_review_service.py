"""HTTP client for the Game Review service (F-045)."""
import json
from datetime import date
from urllib import error, request as urlrequest


def create_game_review_session(
    service_url: str,
    game_date: date,
    score_team1: int | None = None,
    score_team2: int | None = None,
    team1_players: list[dict] | None = None,
    team2_players: list[dict] | None = None,
) -> str:
    """Create a Game Review session and return its shareable link.

    score_team1/score_team2/team1_players/team2_players are an all-or-nothing
    bundle -- the service stores them as a single frozen snapshot, so partial
    data isn't accepted. team1_players/team2_players entries are shaped
    {"name": str, "ranking": float | None}.
    """
    bundle = (score_team1, score_team2, team1_players, team2_players)
    payload: dict = {"game_date": game_date.isoformat()}
    if any(value is not None for value in bundle):
        if any(value is None for value in bundle):
            raise ValueError("Score and both rosters must be sent together, or not at all.")
        payload.update(
            score_team1=score_team1,
            score_team2=score_team2,
            team1_players=team1_players,
            team2_players=team2_players,
        )

    req = urlrequest.Request(
        f"{service_url.rstrip('/')}/sessions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=10) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(response_body).get("error", response_body)
        except json.JSONDecodeError:
            message = response_body
        raise RuntimeError(f"Game Review returned {exc.code}: {message}") from exc
    except (error.URLError, TimeoutError) as exc:
        raise RuntimeError("Could not reach the Game Review service.") from exc

    try:
        link = json.loads(response_body)["link"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError("Game Review returned an invalid session response.") from exc
    if not isinstance(link, str):
        raise RuntimeError("Game Review returned an invalid session link.")
    return link
