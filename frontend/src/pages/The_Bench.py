import os
import base64

import streamlit as st

from player_database import add_player, list_players, delete_player, update_player

def database_view(st_context):
    st_context.header("Player Database")
    
    # Display all players in a table
    players = list_players()

    if players:
        # Use a larger dataframe in the main area with expanded width
        st.dataframe(players, use_container_width=True)
        
        player_names = [player["name"] for player in players]
    else:
        st.info("No players in the database. Use the sidebar to add players.")

def add_player_view(st_context, player_names: list[str]):
    st_context.subheader("Add New Player")

    # Input fields for player data
    player_name = st_context.text_input("Player Name")
    distribution = st_context.slider("Distribution Score", 0, 5, 2, step=1, key="add_distribution")
    offense = st_context.slider("Offense Score", 0, 5, 2, step=1, key="add_offense")
    defense = st_context.slider("Defense Score", 0, 5, 2, step=1, key="add_defense")
    modifier = st_context.slider("Modifier", -3.0, 3.0, 0.0, step=0.1, key="add_modifier")
    notes = st_context.text_area("Notes", "", key="add_notes")

    if st_context.button("Add Player"):
        if player_name.strip().lower() in [n.lower() for n in player_names]:
            st_context.error(f"A player named '{player_name}' already exists. Please use a different name.")
        else:
            add_player(player_name, distribution, offense, defense, modifier, notes)
            st.rerun()

def delete_player_view(st_context, player_names: list[str]):
    if not player_names:
        st_context.info("No players available to delete.")
        return
    st_context.subheader("Delete Player")
    player_to_delete = st_context.selectbox("Select player to delete:", player_names)
    if st_context.button("Delete Player"):
        delete_player(player_to_delete)
        st_context.rerun()

def edit_player_view(st_context, player_names: list[str]):
    if not player_names:
        st_context.info("No players available to edit.")
        return
    st_context.subheader("Edit Player")
    
    # Select player to edit
    player_to_edit = st_context.selectbox("Select player to edit:", player_names)
    
    # Get current player data
    players = list_players()
    player_data = next((p for p in players if p["name"] == player_to_edit), None)
    
    if player_data:
        # Input fields for updating scores
        distribution = st_context.slider(
            "Distribution Score", 
            0, 5, 
            int(player_data["distribution"]),
            step=1,
            key="edit_distribution"
        )
        offense = st_context.slider(
            "Offense Score", 
            0, 5, 
            int(player_data["offense"]),
            step=1,
            key="edit_offense"
        )
        defense = st_context.slider(
            "Defense Score", 
            0, 5, 
            int(player_data["defense"]),
            step=1,
            key="edit_defensive"
        )
        modifier = st_context.slider(
            "Modifier",
            -3.0, 3.0,
            float(player_data.get("modifier", 0.0)),
            step=0.1,
            key="edit_modifier"
        )
        notes = st_context.text_area(
            "Notes",
            player_data.get("notes", ""),
            key="edit_notes"
        )
        
        if st_context.button("Update Player"):
            update_player(player_to_edit, distribution, offense, defense, modifier, notes)
            st_context.rerun()

def main():
    st.title("The Bench")

    file_ = open("./bouncing_soccer_ball.gif", "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()

    # Add bouncing soccer ball gif, centered and with rounded edges
    st.sidebar.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="data:image/gif;base64,{data_url}" alt="bouncing soccer ball gif" '
        f'style="border-radius: 16px; width: 100px; height: 100px; object-fit: cover;">'
        f'</div>',
        unsafe_allow_html=True
    )

    

    # Main area shows the player database
    database_view(st)

    # Sidebar for player management
    with st.sidebar:
        
        # Create tabs in the sidebar
        add_tab, edit_tab, delete_tab = st.tabs(["Add", "Edit", "Delete"])
        
        # Get player names once to use in multiple tabs
        player_names = [player["name"] for player in list_players()]
        
        with add_tab:
            add_player_view(st, player_names)

        with edit_tab:
            edit_player_view(st, player_names)

        with delete_tab:
            delete_player_view(st, player_names)

if __name__ == "__main__":
    main()

