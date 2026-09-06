"""Optional account and manual cloud-sync settings."""

import streamlit as st

from backup import export_payload
from cloud_sync import AuthenticationError, CloudSyncError, configured_client
from player_database import restore_players


SESSION_KEY = "cloud_sync_session"
ENABLED_KEY = "cloud_sync_enabled"


def _show_error(error: CloudSyncError) -> None:
    st.error(str(error))


def _authenticate(action: str, email: str, password: str) -> None:
    try:
        client = configured_client()
        session = client.sign_up(email, password) if action == "sign_up" else client.sign_in(email, password)
        st.session_state[SESSION_KEY] = session
        st.success(f"Signed in as {session['email']}.")
    except CloudSyncError as error:
        _show_error(error)


def _sync_now() -> None:
    try:
        canonical_payload, session = configured_client().sync_players(
            st.session_state[SESSION_KEY], export_payload()
        )
        added, updated = restore_players(canonical_payload["players"])
        st.session_state[SESSION_KEY] = session
        st.success(f"Sync complete: {added} player(s) added and {updated} updated locally.")
    except AuthenticationError as error:
        _show_error(error)
    except CloudSyncError as error:
        _show_error(error)
    except (TypeError, ValueError, AttributeError):
        st.error("Cloud sync returned player data that could not be applied safely.")


def _password_reset_form() -> None:
    with st.expander("Reset password"):
        with st.form("cloud_sync_password_reset"):
            email = st.text_input("Email address", key="cloud_sync_reset_email")
            submitted = st.form_submit_button("Send password reset email")
        if submitted:
            try:
                configured_client().send_password_reset(email)
                st.success("If that email has an account, a password reset email has been sent.")
            except CloudSyncError as error:
                _show_error(error)


def main() -> None:
    st.title("Settings")
    st.subheader("Optional cloud sync")
    st.write(
        "Cloud sync is optional. Your roster stays available locally, and no data is sent "
        "unless you sign in and select Sync now."
    )

    enabled = st.checkbox("Enable cloud sync", key=ENABLED_KEY)
    if not enabled:
        st.session_state.pop(SESSION_KEY, None)
        st.info("Cloud sync is off. Local roster features continue to work normally.")
        return

    session = st.session_state.get(SESSION_KEY)
    if isinstance(session, dict):
        email = session.get("email", "your account")
        st.success(f"Signed in as {email}.")
        col_sync, col_sign_out = st.columns(2)
        with col_sync:
            if st.button("Sync now", type="primary"):
                _sync_now()
        with col_sign_out:
            if st.button("Sign out"):
                st.session_state.pop(SESSION_KEY, None)
                st.success("Signed out. Your local roster was not changed.")
        _password_reset_form()
        return

    sign_up_tab, sign_in_tab = st.tabs(["Sign up", "Sign in"])
    with sign_up_tab:
        with st.form("cloud_sync_sign_up"):
            email = st.text_input("Email address", key="cloud_sync_sign_up_email")
            password = st.text_input("Password", type="password", key="cloud_sync_sign_up_password")
            submitted = st.form_submit_button("Sign up")
        if submitted:
            _authenticate("sign_up", email, password)

    with sign_in_tab:
        with st.form("cloud_sync_sign_in"):
            email = st.text_input("Email address", key="cloud_sync_sign_in_email")
            password = st.text_input("Password", type="password", key="cloud_sync_sign_in_password")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            _authenticate("sign_in", email, password)

    _password_reset_form()


if __name__ == "__main__":
    main()
