from typing import Literal

from pydantic import BaseModel, Field, conlist

from data_models import Player


class HealthCheckResponse(BaseModel):
    status: Literal["Running"]

class TeamSelectionRequest(BaseModel):
    players: conlist(Player, min_length=4) = Field(..., description="List of players (minimum 4)")


class TeamSelectionResponse(BaseModel):
    team1: list[Player]
    team2: list[Player]

class TeamAPIModel(BaseModel):
    players: list[Player]