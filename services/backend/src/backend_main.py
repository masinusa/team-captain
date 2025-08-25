from io import BytesIO

from fastapi import FastAPI, Response

from api_models import HealthCheckResponse, TeamSelectionRequest, TeamSelectionResponse, TeamAPIModel
from data_models import Player, Team
from algorithm import select_teams
from visualizations import create_visualization

description = """
Team Captain helps you pick balanced teams for your next pickup soccer game!
"""

app = FastAPI(
    title="Team Captain",
    description=description,
    summary="Pick balanced teams for your next pickup soccer game",
    version="0.0.1",
    contact={
        "name": "masinusa",
        "url": "https://github.com/masinusa",
        "email": "masinusa@gmail.com",
    }
)


@app.get("/", tags=["System Health"])
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="Running")


@app.post("/select_teams", tags=["Team Selection"])
async def select_teams_api(request: TeamSelectionRequest) -> TeamSelectionResponse:
    team1, team2 = select_teams(request.players)
    return TeamSelectionResponse(team1=team1.players, team2=team2.players)

@app.post("/visualize_team", tags=["Team Visualization"],
    responses = {
        200: {
            "content": {"image/png": {}}
        }
    },
    response_class=Response
)
# For call signature, referred to this stackoverflow post: https://stackoverflow.com/questions/55873174/how-do-i-return-an-image-in-fastapi
async def visualize_team_route(team: TeamAPIModel):
    team = Team(players=team.players)
    matplotlib_figure = create_visualization(team)

    # Save figure to a BytesIO buffer
    buf = BytesIO()
    matplotlib_figure.savefig(buf, format="png")
    buf.seek(0)
        
    return Response(content=buf.getvalue(), media_type="image/png")