"""Optional Firebase-authenticated manual player sync.

This module has no import-time configuration or network activity.  Callers
create a client only after the user chooses an account or taps ``Sync now``;
the returned session belongs in ``st.session_state`` and must not be persisted.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib import error, parse, request as urlrequest


FIREBASE_IDENTITY_URL = "https://identitytoolkit.googleapis.com/v1"
FIREBASE_TOKEN_URL = "https://securetoken.googleapis.com/v1/token"
DEFAULT_TIMEOUT_SECONDS = 10


class CloudSyncError(RuntimeError):
    """Base class for errors safe to display to a user."""


class SyncNotConfigured(CloudSyncError):
    """Raised only when the user elects to use an unconfigured sync service."""


class AuthenticationError(CloudSyncError):
    """Firebase rejected authentication or the sync token."""


class SyncNetworkError(CloudSyncError):
    """The configured service could not be reached."""


class SyncTimeoutError(SyncNetworkError):
    """A cloud request exceeded the configured timeout."""


class SyncServiceError(CloudSyncError):
    """The sync service returned an unexpected non-authentication failure."""


class SyncProtocolError(CloudSyncError):
    """A service response did not match the expected protocol."""


@dataclass(frozen=True)
class SyncConfig:
    """Runtime configuration loaded only when an explicit cloud action occurs."""

    firebase_api_key: str
    sync_url: str | None = None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "SyncConfig":
        values = os.environ if environ is None else environ
        return cls(
            firebase_api_key=values.get("FIREBASE_API_KEY", "").strip(),
            sync_url=(
                values.get("PLAYER_SYNC_API_URL", "").strip()
                or values.get("SYNC_API_URL", "").strip()
                or None
            ),
        )

    def require_firebase(self) -> None:
        if not self.firebase_api_key:
            raise SyncNotConfigured(
                "Cloud sync is not configured. Ask the administrator to set FIREBASE_API_KEY."
            )

    def require_sync_url(self) -> str:
        if not self.sync_url:
            raise SyncNotConfigured(
                "Cloud sync is not configured. Ask the administrator to set PLAYER_SYNC_API_URL."
            )
        return self.sync_url


UrlOpener = Callable[..., Any]


class FirebaseSyncClient:
    """Firebase Identity Toolkit and GCP player-sync REST client."""

    def __init__(
        self,
        config: SyncConfig | None = None,
        *,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        opener: UrlOpener | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.config = config if config is not None else SyncConfig.from_env()
        self.timeout = timeout
        self._opener = opener if opener is not None else urlrequest.urlopen
        self._clock = clock

    def sign_up(self, email: str, password: str) -> dict[str, Any]:
        return self._firebase_auth("accounts:signUp", email, password)

    def sign_in(self, email: str, password: str) -> dict[str, Any]:
        return self._firebase_auth("accounts:signInWithPassword", email, password)

    def send_password_reset(self, email: str) -> None:
        self.config.require_firebase()
        self._post_json(
            f"{FIREBASE_IDENTITY_URL}/accounts:sendOobCode?key={self.config.firebase_api_key}",
            {"requestType": "PASSWORD_RESET", "email": email},
            auth_request=True,
        )

    def refresh_session(self, session: Mapping[str, Any]) -> dict[str, Any]:
        self.config.require_firebase()
        refresh_token = session.get("refresh_token")
        if not isinstance(refresh_token, str) or not refresh_token:
            raise AuthenticationError("Please sign in again before syncing.")
        response = self._post_form(
            f"{FIREBASE_TOKEN_URL}/token?key={self.config.firebase_api_key}",
            {"grant_type": "refresh_token", "refresh_token": refresh_token},
            auth_request=True,
        )
        return self._session_from_refresh_response(response, session)

    def sync_players(self, session: Mapping[str, Any], payload: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Synchronize one F-006 envelope and return the canonical payload and session."""
        _validate_player_payload(payload)
        active_session = dict(session)
        if _session_is_expired(active_session, self._clock()):
            active_session = self.refresh_session(active_session)
        id_token = active_session.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise AuthenticationError("Please sign in again before syncing.")
        response = self._post_json(
            self.config.require_sync_url(),
            dict(payload),
            headers={"Authorization": f"Bearer {id_token}"},
        )
        _validate_player_payload(response)
        return response, active_session

    def _firebase_auth(self, action: str, email: str, password: str) -> dict[str, Any]:
        self.config.require_firebase()
        response = self._post_json(
            f"{FIREBASE_IDENTITY_URL}/{action}?key={self.config.firebase_api_key}",
            {"email": email, "password": password, "returnSecureToken": True},
            auth_request=True,
        )
        return self._session_from_auth_response(response)

    def _post_json(
        self,
        url: str,
        payload: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        auth_request: bool = False,
    ) -> dict[str, Any]:
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return self._request(url, body, request_headers, auth_request=auth_request)

    def _post_form(self, url: str, payload: Mapping[str, str], *, auth_request: bool) -> dict[str, Any]:
        return self._request(
            url,
            parse.urlencode(payload).encode("utf-8"),
            {"Content-Type": "application/x-www-form-urlencoded"},
            auth_request=auth_request,
        )

    def _request(
        self, url: str, body: bytes, headers: Mapping[str, str], *, auth_request: bool
    ) -> dict[str, Any]:
        req = urlrequest.Request(url, data=body, headers=dict(headers), method="POST")
        try:
            with self._opener(req, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            try:
                response_body = exc.read().decode("utf-8", errors="replace")
                message = _error_message(response_body)
                if auth_request or exc.code in (401, 403):
                    raise AuthenticationError(message) from exc
                raise SyncServiceError(message) from exc
            finally:
                exc.close()
        except TimeoutError as exc:
            raise SyncTimeoutError("Cloud sync timed out. Try again when you are connected.") from exc
        except error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise SyncTimeoutError("Cloud sync timed out. Try again when you are connected.") from exc
            raise SyncNetworkError("Could not reach cloud sync. Check your connection and try again.") from exc
        except OSError as exc:
            raise SyncNetworkError("Could not reach cloud sync. Check your connection and try again.") from exc

        try:
            decoded = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise SyncProtocolError("Cloud sync returned an invalid response.") from exc
        if not isinstance(decoded, dict):
            raise SyncProtocolError("Cloud sync returned an invalid response.")
        return decoded

    def _session_from_auth_response(self, response: Mapping[str, Any]) -> dict[str, Any]:
        return _make_session(
            response,
            id_token_key="idToken",
            refresh_token_key="refreshToken",
            expires_key="expiresIn",
            user_id_key="localId",
            email_key="email",
            now=self._clock(),
        )

    def _session_from_refresh_response(
        self, response: Mapping[str, Any], previous: Mapping[str, Any]
    ) -> dict[str, Any]:
        session = _make_session(
            response,
            id_token_key="id_token",
            refresh_token_key="refresh_token",
            expires_key="expires_in",
            user_id_key="user_id",
            email_key=None,
            now=self._clock(),
        )
        session["email"] = previous.get("email", "")
        return session


def _make_session(
    response: Mapping[str, Any],
    *,
    id_token_key: str,
    refresh_token_key: str,
    expires_key: str,
    user_id_key: str,
    email_key: str | None,
    now: float,
) -> dict[str, Any]:
    id_token = response.get(id_token_key)
    refresh_token = response.get(refresh_token_key)
    user_id = response.get(user_id_key)
    expires_in = response.get(expires_key)
    if not all(isinstance(value, str) and value for value in (id_token, refresh_token, user_id, expires_in)):
        raise SyncProtocolError("Firebase returned an invalid sign-in response.")
    try:
        expires_at = now + max(0, int(expires_in) - 60)
    except ValueError as exc:
        raise SyncProtocolError("Firebase returned an invalid sign-in response.") from exc
    session: dict[str, Any] = {
        "id_token": id_token,
        "refresh_token": refresh_token,
        "user_id": user_id,
        "expires_at": expires_at,
    }
    if email_key:
        email = response.get(email_key)
        if not isinstance(email, str):
            raise SyncProtocolError("Firebase returned an invalid sign-in response.")
        session["email"] = email
    return session


def _session_is_expired(session: Mapping[str, Any], now: float) -> bool:
    expires_at = session.get("expires_at")
    return not isinstance(expires_at, (int, float)) or now >= expires_at


def _validate_player_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != 1 or payload.get("games") != []:
        raise SyncProtocolError("Cloud sync requires a version-1 player payload.")
    if not isinstance(payload.get("players"), list):
        raise SyncProtocolError("Cloud sync returned an invalid player payload.")


def _error_message(body: str) -> str:
    try:
        message = json.loads(body).get("error", {}).get("message")
    except (json.JSONDecodeError, AttributeError):
        message = None
    if not isinstance(message, str):
        return "Cloud sync could not complete. Try again later."
    firebase_messages = {
        "EMAIL_EXISTS": "An account already exists for that email address.",
        "EMAIL_NOT_FOUND": "Email or password is incorrect.",
        "INVALID_PASSWORD": "Email or password is incorrect.",
        "INVALID_LOGIN_CREDENTIALS": "Email or password is incorrect.",
        "INVALID_ID_TOKEN": "Your sign-in has expired. Please sign in again.",
        "TOKEN_EXPIRED": "Your sign-in has expired. Please sign in again.",
    }
    return firebase_messages.get(message, "Cloud sync could not complete. Try again later.")


def configured_client() -> FirebaseSyncClient:
    """Create a lazily configured client for an explicit user action."""
    return FirebaseSyncClient()


def sign_up(email: str, password: str) -> dict[str, Any]:
    """Sign up through a lazily configured default client."""
    return configured_client().sign_up(email, password)


def sign_in(email: str, password: str) -> dict[str, Any]:
    """Sign in through a lazily configured default client."""
    return configured_client().sign_in(email, password)


def refresh_session(session: Mapping[str, Any]) -> dict[str, Any]:
    """Refresh a Firebase session as part of an explicit sync operation."""
    return configured_client().refresh_session(session)


def send_password_reset(email: str) -> None:
    """Request a Firebase password-reset email."""
    configured_client().send_password_reset(email)


def sync_players(
    session: Mapping[str, Any], payload: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Synchronize a F-006 envelope through a lazily configured client."""
    return configured_client().sync_players(session, payload)
