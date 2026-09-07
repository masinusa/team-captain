import base64
import os
from datetime import date

import streamlit as st

from game_history import (
    add_note,
    delete_game,
    delete_note,
    get_game,
    list_games,
    player_goals,
    update_game,
)
from game_review_service import create_game_review_session

SELECTED_GAME_KEY = "game_history_selected_id"
DELETE_PENDING_KEY = "game_history_delete_pending"


def _roster_payload(players: list[dict]) -> list[dict]:
    """Send each player's four raw component scores from the frozen
    snapshot (F-045) -- offense, distribution, defense, modifier -- not a
    single collapsed ranking; the game-review service stores them
    independently so nothing server-side has to un-average them later."""
    return [
        {
            "name": player["name"],
            "offense": player["offense"],
            "distribution": player["distribution"],
            "defense": player["defense"],
            "modifier": player["injury_handicap"],
        }
        for player in players
    ]


def _result_caption(game: dict) -> str:
    matchup = f"{len(game['team1_players'])}v{len(game['team2_players'])}"
    if game["winner"] == 1:
        return f"{matchup} · Team 1 win"
    if game["winner"] == 2:
        return f"{matchup} · Team 2 win"
    return f"{matchup} · Tie"


def list_view(st_context):
    st_context.header("Game History")
    games = list_games()
    if not games:
        st_context.info("No games recorded yet. Save one from the Team Split page.")
        return

    for game in games:
        with st_context.container(border=True):
            col1, col2, col3 = st_context.columns([2, 2, 1])
            col1.write(game["date"])
            col2.write(f"{game['score1']} – {game['score2']} · {_result_caption(game)}")
            if col3.button("View", key=f"view_{game['id']}"):
                st.session_state[SELECTED_GAME_KEY] = game["id"]
                st.rerun()


def _roster_section(st_context, title: str, players: list[dict], game: dict):
    st_context.write(f"**{title}**")
    for player in players:
        goals = player_goals(game, player["id"])
        line = player["name"]
        if goals:
            line += f" — {goals} goal{'s' if goals != 1 else ''}"
        st_context.write(line)
        st_context.caption(
            f"O:{player['offense']} Dst:{player['distribution']} D:{player['defense']}"
        )


def _notes_section(st_context, game: dict):
    st_context.subheader("Notes")
    for note in game["notes"]:
        with st_context.container(border=True):
            st_context.write(note["text"])
            author = f"{note['author']} · " if note["author"] else ""
            st_context.caption(f"{author}{note['date']}")
            if st_context.button("Delete note", key=f"delete_note_{note['id']}"):
                delete_note(game["id"], note["id"])
                st.rerun()

    with st_context.form(f"add_note_form_{game['id']}"):
        text = st_context.text_area("Add a note")
        author = st_context.text_input("Author (optional)")
        if st_context.form_submit_button("Add Note"):
            try:
                add_note(game["id"], text, author)
                st.rerun()
            except ValueError as error:
                st_context.error(str(error))


def _edit_section(st_context, game: dict):
    st_context.subheader("Edit")
    with st_context.form(f"edit_game_form_{game['id']}"):
        game_date = st_context.date_input("Game date", value=date.fromisoformat(game["date"]))
        col1, col2 = st_context.columns(2)
        score1 = col1.number_input(
            "Team 1 score", min_value=0, max_value=99, value=game["score1"], step=1
        )
        score2 = col2.number_input(
            "Team 2 score", min_value=0, max_value=99, value=game["score2"], step=1
        )
        st_context.caption("Goals")
        goal_inputs = {}
        for player in game["team1_players"] + game["team2_players"]:
            goal_inputs[player["id"]] = st_context.number_input(
                f"{player['name']} goals",
                min_value=0,
                max_value=20,
                value=player_goals(game, player["id"]),
                step=1,
                key=f"edit_goal_{game['id']}_{player['id']}",
            )
        if st_context.form_submit_button("Save Changes"):
            try:
                update_game(game["id"], game_date, int(score1), int(score2), goal_inputs)
                st.rerun()
            except ValueError as error:
                st_context.error(str(error))


def _delete_section(st_context, game: dict):
    st_context.subheader("Delete")
    if st.session_state.get(DELETE_PENDING_KEY) != game["id"]:
        if st_context.button("Delete Game"):
            st.session_state[DELETE_PENDING_KEY] = game["id"]
            st.rerun()
        return
    st_context.warning("This cannot be undone.")
    confirm_col, cancel_col = st_context.columns(2)
    if confirm_col.button("Confirm Delete", type="primary"):
        delete_game(game["id"])
        st.session_state.pop(DELETE_PENDING_KEY, None)
        st.session_state.pop(SELECTED_GAME_KEY, None)
        st.rerun()
    if cancel_col.button("Cancel"):
        st.session_state.pop(DELETE_PENDING_KEY, None)
        st.rerun()


def _review_link_section(st_context, game: dict):
    st_context.subheader("Game Review")
    service_url = os.getenv("GAME_REVIEW_SERVICE_URL", "").strip()
    if not service_url:
        st_context.info("Set GAME_REVIEW_SERVICE_URL to create and share a Game Review link.")
        return
    if st_context.button("Create Game Review Link"):
        try:
            with st_context.spinner("Creating review link..."):
                link = create_game_review_session(
                    service_url,
                    date.fromisoformat(game["date"]),
                    score_team1=game["score1"],
                    score_team2=game["score2"],
                    team1_players=_roster_payload(game["team1_players"]),
                    team2_players=_roster_payload(game["team2_players"]),
                )
            st.session_state[f"game_review_link_{game['id']}"] = link
        except RuntimeError as exc:
            st_context.error(str(exc))
    if link := st.session_state.get(f"game_review_link_{game['id']}"):
        st_context.success("Game Review link created.")
        st_context.code(link, language=None)
        st_context.link_button("Open Game Review", link)


def detail_view(st_context, game: dict):
    if st_context.button("← Back to list"):
        st.session_state.pop(SELECTED_GAME_KEY, None)
        st.rerun()

    st_context.header(f"{game['score1']} – {game['score2']}")
    st_context.caption(f"{game['date']} · {_result_caption(game)}")

    col1, col2 = st_context.columns(2)
    with col1:
        _roster_section(st_context, "Team 1", game["team1_players"], game)
    with col2:
        _roster_section(st_context, "Team 2", game["team2_players"], game)

    _notes_section(st_context, game)
    _edit_section(st_context, game)
    _delete_section(st_context, game)
    _review_link_section(st_context, game)


def main():
    st.title("Game History")
    with open("./bouncing_soccer_ball.gif", "rb") as file:
        data_url = base64.b64encode(file.read()).decode("utf-8")
    st.sidebar.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="data:image/gif;base64,{data_url}" alt="bouncing soccer ball gif" '
        f'style="border-radius: 16px; width: 100px; height: 100px; object-fit: cover;">'
        "</div>",
        unsafe_allow_html=True,
    )

    selected_id = st.session_state.get(SELECTED_GAME_KEY)
    if selected_id:
        game = get_game(selected_id)
        if not game:
            st.session_state.pop(SELECTED_GAME_KEY, None)
            st.info("That game no longer exists.")
        else:
            detail_view(st, game)
            return

    list_view(st)


if __name__ == "__main__":
    main()
