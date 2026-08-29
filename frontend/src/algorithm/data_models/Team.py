from typing import List
import statistics

from pydantic import BaseModel, validate_call

from . import Player


class Team(BaseModel):
    players: List[Player] = []

    def __init__(self, players: List[Player] = [], **kwargs):
        super().__init__(players=players.copy(), **kwargs)


    @validate_call
    def add_player(self, player: Player) -> None:
        self.players.append(player)

    @validate_call
    def remove_player(self, player: Player) -> None:
        try:
            # Find player location in list
            player_index = self.player_names.index(
                player.name
            )  # player.names Should have same indices as self.players
            del self.players[player_index]
        except Exception:
            raise ValueError(f"Error removing '{player.name}' from {self.player_names}")

    @validate_call
    def add_players(self, player_names: List[str | Player]):
        for player in player_names:
            self.add_player(player)

    @validate_call
    def remove_players(self, player_names: List[str | Player]):
        for player in player_names:
            self.remove_player(player)

    @property
    def size(self):
        return len(self.players)

    @property
    def average_od_ratio(self):
        ratios = [player.offense_defense_ratio for player in self.players]
        return statistics.mean(ratios)

    @property
    def average_distribution(self):
        distribution_scores = [player.distribution for player in self.players]
        return statistics.mean(distribution_scores)

    @property
    def average_overall_score(self):
        overall_scores = [player.overall_score for player in self.players]
        return statistics.mean(overall_scores)

    @property
    def player_names(self):
        return [player.name for player in self.players]

    def copy(self):
        return Team(self.players)

    def includes(self, player: Player | str) -> bool:
        if isinstance(player, Player):
            player_name: Player = player.name
        else:
            player_name = player
        for player in self.players:
            if player.name == player_name:
                return True
        return False
