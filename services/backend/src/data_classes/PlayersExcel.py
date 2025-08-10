import statistics
import traceback

from pydantic import BaseModel
import pandas as pd

from data_classes import Player
from utils import this_file_dir


class PlayersExcel:
    """Player Dataframe"""

    def __init__(self):
        # Read the excel file into a pandas DataFrame
        self.df = pd.read_excel(
            f"{this_file_dir()}/../../players.xlsx",
            sheet_name="players",
            index_col="Player",
        )

    def get_player(self, player_name: str) -> Player:
        try:
            player_data = self.df.loc[player_name].to_dict()
            player = Player(
                name=player_name,
                offense=player_data["Offense (1-5)"],
                distribution=player_data["Distribution (1 - 5)"],
                defense=player_data["Defense (1-5)"],
                injury_handicap=player_data["Injury/Handicap (0 - 1)"],
            )
        except Exception as e:
            # Get the full traceback as a string
            tb_str = traceback.format_exc()
            raise Exception(
                f"Error Retrieving '{player_name}': {str(e)}\n\nFull traceback:\n{tb_str}"
            )
        return player
