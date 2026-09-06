import base64

import streamlit as st
from pydantic import validate_call

from player_database import list_players, get_player
from algorithm import select_teams, create_visualization, Player, Team

# Read the gif once at the top
file_ = open("./bouncing_soccer_ball.gif", "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()

# Set page configuration
st.set_page_config(
    page_title="Team Captain - Game Time",
    page_icon=f"data:image/gif;base64,{data_url}",
    layout="wide"
)

@validate_call
def get_teams(selected_players: list[dict]) -> dict:
    """Split the selected players into two balanced teams, entirely locally."""
    try:
        players = []
        for player in selected_players:
            player_data = dict(player)
            player_data["injury_handicap"] = player_data.pop("modifier", 0.0)
            players.append(Player(**player_data))
        team1, team2 = select_teams(players)
        return {
            "team1": [player.model_dump() for player in team1.players],
            "team2": [player.model_dump() for player in team2.players],
        }
    except ValueError as e:
        st.error(f"Could not split teams: {str(e)}")
        return {}

@validate_call
def visualize_team(team: list[dict]):
    """Render the pitch visualization for a team, entirely locally."""
    try:
        players = [Player(**player) for player in team]
        return create_visualization(Team(players=players))
    except ValueError as e:
        st.error(f"Failed to visualize team {team}: {str(e)}")
        return None


def main():
    st.title("Team Split") 
    
    # Add bouncing soccer ball gif, centered and with rounded edges
    st.sidebar.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="data:image/gif;base64,{data_url}" alt="bouncing soccer ball gif" '
        f'style="border-radius: 16px; width: 100px; height: 100px; object-fit: cover;">'
        f'</div>',
        unsafe_allow_html=True
    )

    
    # Get all players from the database
    all_players = list_players()
    player_options = {player["id"]: player["name"] for player in all_players}

    # Initialize session state for player selection persistence across page navigations.
    # Use a separate non-widget key so it survives navigation (Streamlit deletes widget keys on page change).
    if "persistent_selected_players" not in st.session_state:
        st.session_state.persistent_selected_players = []

    # Seed the widget key from persistent state when navigating back to this page.
    # Only do this when the widget key is absent (i.e. after a page navigation cleared it).
    # Mixing default= and key= causes Streamlit to conflict on every rerun, so we set the
    # session state directly instead.
    if "selected_players" not in st.session_state:
        valid_persistent = [
            player_id
            for player_id in st.session_state.persistent_selected_players
            if player_id in player_options
        ]
        st.session_state.selected_players = valid_persistent

    # Player selection
    st.header("Select Players")
    selected_players = st.multiselect(
        "Choose 2-18 players to split into teams:",
        options=list(player_options),
        format_func=lambda player_id: player_options[player_id],
        key="selected_players"
    )

    # Save selection to persistent (non-widget) state so it survives page navigation
    st.session_state.persistent_selected_players = selected_players

    # Validate selection
    num_selected = len(selected_players)
    st.write(f"Number of players selected: {num_selected}")
    if num_selected < 2:
        st.warning("Please select at least 2 players")
    elif num_selected > 20:
        st.error("Maximum 20 players allowed")
    else:
        if st.button("Split Teams"):
            # Convert selected player IDs to player data.
            players = []
            for player_id in selected_players:
                player_data = get_player(player_id)
                if player_data:
                    players.append(player_data)
                else:
                    st.error("Could not retrieve a selected player.")
                    return
            
            # Split the players into two balanced teams, entirely locally
            teams = get_teams(players)
            if teams:
                # Display the teams
                col1, col2 = st.columns(2)
                st.subheader("Teams")
                with col1:
                    st.write("Team 1")
                    team_1 = teams.get("team1")
                    visual = visualize_team(team_1)
                    if visual:
                        fig = visual.gcf()
                        st.pyplot(fig)
                        visual.close(fig)
                    player_names = [player["name"] for player in team_1]
                    st.markdown("<br>".join(player_names), unsafe_allow_html=True)
                with col2:
                    st.write("Team 2")
                    team_2 = teams.get("team2")
                    visual = visualize_team(team_2)
                    if visual:
                        fig = visual.gcf()
                        st.pyplot(fig)
                        visual.close(fig)
                    player_names = [player["name"] for player in team_2]
                    st.markdown("<br>".join(player_names), unsafe_allow_html=True)



if __name__ == "__main__":
    main()
