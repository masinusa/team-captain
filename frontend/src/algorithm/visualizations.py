from typing import List, Literal, Tuple, Dict, Any
import random
from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from pydantic import BaseModel, validate_call

from .data_models import Player, Team
from .utils import swap_items, swap_dict_keys


def pop_player(
    min_or_max: Literal["min", "max"],
    attribute: Literal[
        "offense",
        "defense",
        "overall_score",
        "offense_defense_ratio",
        "injury_handicap",
        "distribution",
    ],
):

    def _pop_player_with_attribute_func(players: List[Player]):
        if min_or_max == "min":
            func = min
        elif min_or_max == "max":
            func = max
        else:
            raise ValueError(f"Unsupported min_or_max value: {min_or_max}")

        player = func(players, key=lambda player: getattr(player, attribute))
        index = players.index(player)
        return players.pop(index)

    return _pop_player_with_attribute_func


def random_player():
    def _random_func(players: List[Player]):
        random.shuffle(players)
        return players.pop(0)

    return _random_func


class _PositionData(BaseModel):
    x: int
    y: int
    selection_function: Any


class _PlayerPositionMapping(BaseModel):
    player: Player
    position_data: _PositionData
    position: str


POSITION_DATA_INDEX = {
    "forward": _PositionData(
        x=40, y=70, selection_function=pop_player("max", "offense_defense_ratio")
    ),
    "left_mid": _PositionData(x=10, y=80, selection_function=random_player()),
    "right_mid": _PositionData(x=70, y=80, selection_function=random_player()),
    "cam": _PositionData(
        x=40, y=80, selection_function=pop_player("max", "offense_defense_ratio")
    ),
    "center_mid": _PositionData(
        x=40, y=85, selection_function=pop_player("max", "offense_defense_ratio")
    ),
    "cdm": _PositionData(
        x=40, y=90, selection_function=pop_player("max", "offense_defense_ratio")
    ),
    "center_back": _PositionData(
        x=40, y=105, selection_function=pop_player("min", "offense_defense_ratio")
    ),
    "left_back": _PositionData(
        x=20, y=100, selection_function=pop_player("min", "offense_defense_ratio")
    ),
    "right_back": _PositionData(
        x=60, y=100, selection_function=pop_player("min", "offense_defense_ratio")
    ),
    "goalkeeper": _PositionData(x=40, y=115, selection_function=random_player()),
}


TEAM_POSITION_MAPPINGS: Dict[int, List[str]] = {
    1: ["center_mid"],
    2: ["left_mid", "right_mid"],
    3: ["left_mid", "right_mid", "center_back"],
    4: ["left_back", "right_back", "left_mid", "right_mid"],
    5: ["left_back", "right_back", "left_mid", "right_mid", "center_mid"],
    6: ["left_back", "right_back", "left_mid", "right_mid", "center_mid", "forward"],
    7: [
        "left_back",
        "right_back",
        "left_mid",
        "right_mid",
        "center_mid",
        "forward",
        "goalkeeper",
    ],
    8: [
        "forward",
        "center_mid",
        "left_back",
        "right_back",
        "center_back",
        "left_mid",
        "right_mid",
        "goalkeeper",
    ],
    9: [
        "forward",
        "cam",
        "cdm",
        "center_back",
        "left_back",
        "right_back",
        "left_mid",
        "right_mid",
        "goalkeeper",
    ],
    10: [
        "forward",
        "cam",
        "center_mid", 
        "cdm",
        "center_back",
        "left_back",
        "right_back",
        "left_mid",
        "right_mid",
        "goalkeeper",
    ],
}


def _assign_positions(team: Team) -> List[_PlayerPositionMapping]:
    # Copy to avoid manipulating the original Team data
    players: List[Player] = team.players.copy()

    position_mappings: List[_PlayerPositionMapping] = []
    for position in TEAM_POSITION_MAPPINGS[team.size]:
        # print(f"assigning Position: {position}")
        position_data = POSITION_DATA_INDEX[position]
        # print(f"position_data: {position_data}")
        player: Player = position_data.selection_function(players)
        position_mappings.append(
            _PlayerPositionMapping(
                player=player, position_data=position_data, position=position
            )
        )
    return position_mappings


def _apply_additional_assignment_rules(
    position_mappings: List[_PlayerPositionMapping],
) -> None:
    """Additional nit-picky rules for a potentially more realistic formation"""

    # Consider offense_defense ratio when distinguishing the CAM vs. CDM
    positions_index = {pmapping.position: pmapping for pmapping in position_mappings}
    if all(
        position in positions_index.keys() for position in ["cam", "cdm"]
    ):  # Check this team has a CAM & CDM
        cam_player_ratio = positions_index["cam"].player.offense_defense_ratio
        cdm_player_ratio = positions_index["cdm"].player.offense_defense_ratio
        if cam_player_ratio < cdm_player_ratio:
            positions_index["cam"].player.position = "cdm"
            positions_index["cdm"].player.position = "cam"


def create_visualization(team: Team) -> matplotlib.figure.Figure:
    position_mappings: List[_PlayerPositionMapping] = _assign_positions(team)
    _apply_additional_assignment_rules(position_mappings)

    # Draw a Pitch
    pitch = VerticalPitch(pitch_color="grass", line_color="white", half=True)
    fig, ax = pitch.draw()

    # Plot player positions

    for pmapping in position_mappings:
        plt.scatter(
            pmapping.position_data.x, pmapping.position_data.y, color="blue", s=100
        )
        plt.annotate(
            pmapping.player.name,
            (pmapping.position_data.x, pmapping.position_data.y),
            textcoords="offset points",
            xytext=(6, 6),
            ha="center",
        )

    # Add labels and title
    plt.title("Soccer Player Positions")
    plt.legend()

    # Remove axis ticks
    plt.xticks([])
    plt.yticks([])

    # Show
    plt.gca().invert_yaxis()

    return plt

@validate_call
def visualize_team(team: Team):
    """Visualize the formation on the pitch"""

    pitch = create_visualization(team)
    pitch.show()
