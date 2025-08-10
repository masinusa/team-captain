import random
from typing import List, Tuple


from data_classes.PlayersExcel import PlayersExcel, Player
from data_classes.Team import Team
from utils import coin_flip

PLAYER_EXCEL = PlayersExcel()


def _balanced_partition(
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


def select_teams(players: List[Player]) -> Tuple[Team, Team]:
    """Greedy Team Balanced Partition problem solver"""

    # #### Retrieve list of all players and shuffle for potential randomness (unsure if shuffling actually helps at this stage) ###
    # all_players: List[Player] = [
    #     PLAYER_EXCEL.get_player(player_name) for player_name in player_names
    # ]
    random.shuffle(players)

    ### Optimize balance on a single player attribute ###
    team1, team2 = _balanced_partition(
        players=players, optimizing_attribute="offense_defense_ratio"
    )

    variance = lambda t1, t2: (
        abs(t1.average_od_ratio - t2.average_od_ratio)
        + (
            1.5 * abs(t1.average_distribution - t2.average_distribution)
        )  # Weigh distribution more heavily
        + abs(t1.average_overall_score - t2.average_overall_score)
    )

    min_var = variance(team1, team2)
    min_var_team1 = team1
    min_var_team2 = team2
    # # Try every combination of switching one player to minimize variance value
    # for team_1_player in team1.players:
    #     for team_2_player in team2.players:
    #         test_team1 = team1.copy()
    #         test_team2 = team2.copy()

    #         test_team1.remove_player(team_1_player.name)
    #         test_team2.remove_player(team_2_player.name)

    #         test_team1.add_player(team_2_player.name)
    #         test_team2.add_player(team_1_player.name)
    #         var = variance(test_team1, test_team2)

    #         if var < min_var:
    #             min_var = var
    #             min_var_team1, min_var_team2 = test_team1, test_team2

    # Get the two lowest distribution players to avoid being on the same team
    sorted_players_distribution = sorted(
        players, key=lambda player: getattr(player, "distribution"), reverse=True
    )  # highest to lowest
    first_lowest_distribution_player = sorted_players_distribution[
        -1
    ]  # Lowest distribution player
    second_lowest_distribution_player = sorted_players_distribution[
        -2
    ]  # Second-lowest distribution player

    # Try every combination of switching two players to minimize variance value
    teams_evaluated = 0
    t1p1_index, t1p2_index = 0, 0  # [1] Will get incremented immediatly
    while t1p1_index <= len(
        team1.players
    ):  # until all possible players have been swapped
        t1p2_index = (t1p2_index + 1) % len(team2.players)  # increment t2p2
        if t1p2_index == 0:
            t1p1_index += 1
            # print(
            #     f"Checking T1: {t1p1_index} against len(players): {len(team1.players)}"
            # )
            if t1p1_index == len(team1.players) - 1:
                break
            else:
                t1p2_index = t1p1_index + 1

        t2p1_index, t2p2_index = 0, 1

        while t2p1_index <= len(team2.players):
            if coin_flip(
                0.25
            ):  # Only review x% (0 - 1) of the possibilities to add some randomness
                teams_evaluated += 1
                # print(
                #     f"Swapping team1[{t1p1_index, t1p2_index}] with team2[{t2p1_index, t2p2_index}]"
                # )
                t1p1 = team1.players[t1p1_index]
                t1p2 = team1.players[t1p2_index]
                t2p1 = team2.players[t2p1_index]
                t2p2 = team2.players[t2p2_index]
                # print(
                #     f"Swapping team1[{t1p1.name}, {t1p2.name}] with team2[{t2p1.name}, {t2p2.name}]"
                # )
                test_team1 = team1.copy()
                test_team2 = team2.copy()
                test_team1.remove_player(t1p1)
                test_team1.remove_player(t1p2)
                test_team2.remove_player(t2p1)
                test_team2.remove_player(t2p2)

                test_team1.add_player(t2p1)
                test_team1.add_player(t2p2)
                test_team2.add_player(t1p1)
                test_team2.add_player(t1p2)
                # print(f"Team 1: {[player.name for player in test_team1.players]}")
                # print(f"Team 2: {[player.name for player in test_team2.players]}")
                # Don't allow the two lowest_rated players on the same team
                if (
                    test_team1.includes(first_lowest_distribution_player)
                    & test_team1.includes(second_lowest_distribution_player)
                ) or (
                    test_team2.includes(first_lowest_distribution_player)
                    & test_team2.includes(second_lowest_distribution_player)
                ):
                    pass
                else:
                    var = variance(test_team1, test_team2)
                    # print(f"Variance: {var}")
                    # print(test_team1.average_od_ratio)

                    if var < min_var:
                        min_var = var
                        min_var_team1, min_var_team2 = test_team1, test_team2

            t2p2_index = (t2p2_index + 1) % len(team2.players)  # increment t2p2
            if t2p2_index == 0:
                t2p1_index += 1
                # print(
                #     f"Checking: {t2p1_index} against len(players): {len(team2.players)}"
                # )
                if t2p1_index == len(team2.players) - 1:
                    break
                else:
                    t2p2_index = t2p1_index + 1

    print(f"Evaluated [{teams_evaluated}] teams")
    print(f"Final Variance: {min_var}")
    return min_var_team1, min_var_team2
