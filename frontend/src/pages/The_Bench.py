import base64

import streamlit as st

from player_database import add_player, delete_player, list_players, update_player


def database_view(st_context):
    st_context.header("Player Database")
    players = list_players()
    if players:
        st.dataframe(players, use_container_width=True)
    else:
        st_context.info("No players in the database. Use the sidebar to add players.")


def add_player_view(st_context):
    st_context.subheader("Add New Player")
    player_name = st_context.text_input("Player Name")
    distribution = st_context.slider("Distribution Score", 1, 5, 2, step=1, key="add_distribution")
    offense = st_context.slider("Offense Score", 1, 5, 2, step=1, key="add_offense")
    defense = st_context.slider("Defense Score", 1, 5, 2, step=1, key="add_defense")
    modifier = st_context.slider("Modifier", -3.0, 3.0, 0.0, step=0.1, key="add_modifier")
    notes = st_context.text_area("Notes", "", key="add_notes")

    if st_context.button("Add Player"):
        try:
            add_player(player_name, distribution, offense, defense, modifier, notes)
            st.rerun()
        except ValueError as error:
            st_context.error(str(error))


def delete_player_view(st_context, players: list[dict]):
    if not players:
        st_context.info("No players available to delete.")
        return
    st_context.subheader("Delete Player")
    player = st_context.selectbox(
        "Select player to delete:",
        players,
        format_func=lambda player: player["name"],
    )
    if st_context.button("Delete Player"):
        try:
            delete_player(player["id"])
            st.rerun()
        except ValueError as error:
            st_context.error(str(error))


def edit_player_view(st_context, players: list[dict]):
    if not players:
        st_context.info("No players available to edit.")
        return
    st_context.subheader("Edit Player")
    player = st_context.selectbox(
        "Select player to edit:",
        players,
        format_func=lambda player: player["name"],
    )

    new_name = st_context.text_input("Player Name", value=player["name"], key="edit_name")
    distribution = st_context.slider(
        "Distribution Score", 1, 5, int(player["distribution"]), step=1, key="edit_distribution"
    )
    offense = st_context.slider(
        "Offense Score", 1, 5, int(player["offense"]), step=1, key="edit_offense"
    )
    defense = st_context.slider(
        "Defense Score", 1, 5, int(player["defense"]), step=1, key="edit_defensive"
    )
    modifier = st_context.slider(
        "Modifier", -3.0, 3.0, float(player["modifier"]), step=0.1, key="edit_modifier"
    )
    notes = st_context.text_area("Notes", player["notes"], key="edit_notes")

    if st_context.button("Update Player"):
        try:
            update_player(
                player["id"], new_name, distribution, offense, defense, modifier, notes
            )
            st.rerun()
        except ValueError as error:
            st_context.error(str(error))


def main():
    st.title("The Bench")
    with open("./bouncing_soccer_ball.gif", "rb") as file:
        data_url = base64.b64encode(file.read()).decode("utf-8")
    st.sidebar.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="data:image/gif;base64,{data_url}" alt="bouncing soccer ball gif" '
        f'style="border-radius: 16px; width: 100px; height: 100px; object-fit: cover;">'
        "</div>",
        unsafe_allow_html=True,
    )

    database_view(st)
    with st.sidebar:
        add_tab, edit_tab, delete_tab = st.tabs(["Add", "Edit", "Delete"])
        players = list_players()
        with add_tab:
            add_player_view(st)
        with edit_tab:
            edit_player_view(st, players)
        with delete_tab:
            delete_player_view(st, players)


if __name__ == "__main__":
    main()
