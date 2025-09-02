import os
import base64

import streamlit as st
import requests
from pydantic import validate_call, BaseModel, Field

from player_database import list_players, get_player

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

BACKEND_URL = f"http://{os.getenv("BACKEND_HOSTNAME")}:{os.getenv("BACKEND_PORT")}"  # Adjust URL as needed

@validate_call
def get_teams(selected_players: list[dict]) -> dict:
    """Fetch teams from the backend based on selected players."""
    target_url = BACKEND_URL + "/select_teams"
    try:
        # change the field name of each selected player from 'modifier' to 'injury_handicap'
        for player in selected_players:
            player["injury_handicap"] = player.pop("modifier", 0.0) 
        response = requests.post(target_url, json={"players": selected_players})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the server: {str(e)}")
        return {}

@validate_call
def visualize_team(team: list[dict]):
    """Fetch and display team visualizations from the backend for each team."""
    target_url = BACKEND_URL + "/visualize_team"

    try:
        response = requests.post(target_url, json={"players": team})
        response.raise_for_status()
        return response.content  # Return the image bytes
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch visualization for {team}: {str(e)}")
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
    player_names = [player["name"] for player in all_players]

    # Player selection
    st.header("Select Players")
    selected_players = st.multiselect(
        "Choose 2-18 players to split into teams:",
        options=player_names
    )

    # Validate selection
    num_selected = len(selected_players)
    st.write(f"Number of players selected: {num_selected}")
    if num_selected < 2:
        st.warning("Please select at least 2 players")
    elif num_selected > 18:
        st.error("Maximum 18 players allowed")
    else:
        if st.button("Split Teams"):
            # Convert selected player names to player data
            players = []
            for player_name in selected_players:
                player_data = get_player(player_name)
                if player_data:
                    players.append(player_data)
                else:
                    st.error(f"Could not retrieve data for player: {player_name}")
                    return
            
            # Send request to backend with player data
            teams = get_teams(players)
            if teams:
                # Display the teams
                col1, col2 = st.columns(2)
                st.subheader("Teams")
                with col1:
                    st.write("Team 1")
                    team_1 = teams.get("team1")
                    print(team_1)
                    visual = visualize_team(team_1)
                    st.image(visual, caption="Team 1 Visualization", use_container_width=True)
                    for player in team_1:
                        print(player)
                        st.write(player["name"])
                with col2:
                    st.write("Team 2")
                    team_2 = teams.get("team2")
                    visual = visualize_team(team_2)
                    st.image(visual, caption="Team 2 Visualization", use_container_width=True)
                    for player in team_2:
                        print(player)
                        st.write(player["name"])
                # Visualize teams after displaying names
                


if __name__ == "__main__":
    main()
