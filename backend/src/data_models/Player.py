import statistics

from pydantic import BaseModel, Field
import pandas as pd


class Player(BaseModel):
    name: str
    offense: int = Field(ge=0, le=5)
    distribution: int = Field(ge=0, le=5)
    defense: int = Field(ge=0, le=5)
    injury_handicap: float = Field(ge=-3.0, le=3.0)

    @property
    def offense_defense_ratio(self) -> float:
        """Ratio of offensive score to defensive score"""
        if self.defense == 0:
            return 0
        else:
            return float(self.offense / self.defense)

    @property
    def overall_score(self) -> float:
        """average of all scores"""
        return statistics.mean(
            [self.offense, (self.distribution - self.injury_handicap), self.defense]
        )
