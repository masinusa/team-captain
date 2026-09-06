import base64

import streamlit as st

from player_database import (
    DUPLICATE_LIVE_NAMES,
    add_player,
    delete_player,
    list_players,
    merge_players,
    update_player,
)

MERGE_PENDING_KEY = "bench_merge_pending"


def duplicate_warning_view(st_context):
    """Surface names held by more than one live player (F-006.4).

    Until these are merged the database cannot enforce name uniqueness, and the
    only other signal is a RuntimeWarning at import that no user ever sees.
    """
    if not DUPLICATE_LIVE_NAMES:
        return
    names = ", ".join(f"'{name}'" for name in DUPLICATE_LIVE_NAMES)
    st_context.warning(
        f"More than one player shares {names}. Use the Merge tab in the sidebar "
        "to combine them; name uniqueness stays unenforced until you do."
    )


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
    aliases_text = st_context.text_area(
        "Aliases (one per line)",
        "\n".join(player["aliases"]),
        key="edit_aliases",
        help="Other names this player is known by. Searchable, and never used "
        "to match players automatically.",
    )

    if st_context.button("Update Player"):
        try:
            update_player(
                player["id"],
                new_name,
                distribution,
                offense,
                defense,
                modifier,
                notes,
                aliases=aliases_text.splitlines(),
            )
            st.rerun()
        except ValueError as error:
            st_context.error(str(error))


def merge_player_view(st_context, players: list[dict]):
    if len(players) < 2:
        st_context.info("At least two players are needed to merge.")
        return
    st_context.subheader("Merge Players")
    st_context.caption(
        "Combine two records for the same person. The kept player keeps its "
        "ratings; the other becomes an alias and is archived."
    )

    winner = st_context.selectbox(
        "Keep this player:",
        players,
        format_func=lambda player: player["name"],
        key="merge_winner",
    )
    losers = [player for player in players if player["id"] != winner["id"]]
    loser = st_context.selectbox(
        "Merge this one into it:",
        losers,
        format_func=lambda player: player["name"],
        key="merge_loser",
    )

    pending = st.session_state.get(MERGE_PENDING_KEY)
    confirming = pending == (winner["id"], loser["id"])

    if not confirming:
        if st_context.button("Review merge"):
            st.session_state[MERGE_PENDING_KEY] = (winner["id"], loser["id"])
            st.rerun()
        return

    # Spell out the outcome before committing. Merging cannot be undone from the
    # UI, and the Delete tab's lack of any confirmation is not a precedent worth
    # matching for something this destructive.
    absorbed = [loser["name"]] + loser["aliases"]
    gained = [
        alias
        for alias in absorbed
        if alias.strip().lower() != winner["name"].strip().lower()
        and alias.strip().lower() not in {a.lower() for a in winner["aliases"]}
    ]
    st_context.markdown(
        f"**Keeping** {winner['name']} "
        f"(D{winner['distribution']} O{winner['offense']} F{winner['defense']}, "
        f"modifier {winner['modifier']:+.1f})\n\n"
        f"**Archiving** {loser['name']} "
        f"(D{loser['distribution']} O{loser['offense']} F{loser['defense']}, "
        f"modifier {loser['modifier']:+.1f})"
    )
    if gained:
        st_context.markdown("Aliases gained: " + ", ".join(f"`{a}`" for a in gained))
    if loser["notes"]:
        st_context.caption(f"The archived note will be lost: {loser['notes']!r}")
    st_context.warning("This cannot be undone from the app.")

    confirm_column, cancel_column = st_context.columns(2)
    if confirm_column.button("Merge", type="primary"):
        try:
            merge_players(winner["id"], loser["id"])
            st.session_state.pop(MERGE_PENDING_KEY, None)
            st.rerun()
        except ValueError as error:
            st.session_state.pop(MERGE_PENDING_KEY, None)
            st_context.error(str(error))
    if cancel_column.button("Cancel"):
        st.session_state.pop(MERGE_PENDING_KEY, None)
        st.rerun()


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

    duplicate_warning_view(st)
    database_view(st)
    with st.sidebar:
        add_tab, edit_tab, merge_tab, delete_tab = st.tabs(
            ["Add", "Edit", "Merge", "Delete"]
        )
        players = list_players()
        with add_tab:
            add_player_view(st)
        with edit_tab:
            edit_player_view(st, players)
        with merge_tab:
            merge_player_view(st, players)
        with delete_tab:
            delete_player_view(st, players)


if __name__ == "__main__":
    main()
