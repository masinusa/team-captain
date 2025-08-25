from typing import List, Tuple


from data_models import Team, Player


def balanced_partition(
    players: List[Player], optimizing_attribute: str
) -> Tuple[Team, Team]:
    """_summary_

    Args:
        players (List[Player]): _description_
        optimizing_attribute (str): _description_

    Returns:
        Tuple[Team, Team]: _description_

    Raises:
        ValueError: If the optimizing_attribute is not valid
    """

    sorted_players = sorted(
        players,
        key=lambda player: getattr(player, optimizing_attribute),
        reverse=True,
    )  # highest to lowest

    sum1 = 0
    sum2 = 0
    team1 = Team()
    team2 = Team()
    for player in sorted_players:
        if sum1 <= sum2:
            sum1 += getattr(player, optimizing_attribute)
            team1.add_player(player)
        else:
            sum2 += getattr(player, optimizing_attribute)
            team2.add_player(player)

    return team1, team2

