import io
import json
import sys
import unittest
from pathlib import Path
from urllib import error


SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"
sys.path.insert(0, str(SRC))

from cloud_sync import (  # noqa: E402
    AuthenticationError,
    FirebaseSyncClient,
    SyncConfig,
    SyncNotConfigured,
    SyncProtocolError,
    SyncTimeoutError,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class CloudSyncTests(unittest.TestCase):
    config = SyncConfig(firebase_api_key="firebase-key", sync_url="https://sync.example/v1/players/sync")

    def test_sign_up_uses_identity_toolkit_and_returns_memory_session(self):
        requests = []

        def opener(req, timeout):
            requests.append((req, timeout))
            return FakeResponse(
                {
                    "idToken": "id-token",
                    "refreshToken": "refresh-token",
                    "expiresIn": "3600",
                    "localId": "firebase-user",
                    "email": "captain@example.com",
                }
            )

        session = FirebaseSyncClient(self.config, opener=opener, clock=lambda: 100).sign_up(
            "captain@example.com", "not-persisted"
        )

        self.assertEqual(session, {
            "id_token": "id-token",
            "refresh_token": "refresh-token",
            "user_id": "firebase-user",
            "expires_at": 3640,
            "email": "captain@example.com",
        })
        request, timeout = requests[0]
        self.assertEqual(timeout, 10)
        self.assertEqual(
            request.full_url,
            "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=firebase-key",
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            json.loads(request.data),
            {
                "email": "captain@example.com",
                "password": "not-persisted",
                "returnSecureToken": True,
            },
        )

    def test_expired_session_refreshes_only_during_explicit_sync(self):
        requests = []
        payload = {"schema_version": 1, "exported_at": "2026-01-01T00:00:00Z", "players": [], "games": []}

        def opener(req, timeout):
            requests.append(req)
            if "securetoken.googleapis.com" in req.full_url:
                self.assertEqual(
                    req.data,
                    b"grant_type=refresh_token&refresh_token=old-refresh-token",
                )
                return FakeResponse(
                    {
                        "id_token": "new-id-token",
                        "refresh_token": "new-refresh-token",
                        "expires_in": "3600",
                        "user_id": "firebase-user",
                    }
                )
            self.assertEqual(req.full_url, self.config.sync_url)
            self.assertEqual(req.get_header("Authorization"), "Bearer new-id-token")
            self.assertEqual(json.loads(req.data), payload)
            return FakeResponse(payload)

        canonical, refreshed = FirebaseSyncClient(
            self.config, opener=opener, clock=lambda: 100
        ).sync_players(
            {
                "id_token": "old-id-token",
                "refresh_token": "old-refresh-token",
                "user_id": "firebase-user",
                "email": "captain@example.com",
                "expires_at": 100,
            },
            payload,
        )

        self.assertEqual(canonical, payload)
        self.assertEqual(refreshed["id_token"], "new-id-token")
        self.assertEqual(refreshed["email"], "captain@example.com")
        self.assertEqual(len(requests), 2)

    def test_firebase_auth_failures_are_safe_authentication_errors(self):
        def opener(req, timeout):
            raise error.HTTPError(
                req.full_url,
                400,
                "bad request",
                {},
                io.BytesIO(b'{"error":{"message":"INVALID_PASSWORD"}}'),
            )

        with self.assertRaisesRegex(AuthenticationError, "Email or password is incorrect"):
            FirebaseSyncClient(self.config, opener=opener).sign_in("captain@example.com", "wrong")

    def test_timeout_is_distinct_and_sync_payload_is_checked(self):
        client = FirebaseSyncClient(self.config, opener=lambda req, timeout: (_ for _ in ()).throw(TimeoutError()))
        valid_session = {
            "id_token": "id-token",
            "refresh_token": "refresh-token",
            "user_id": "firebase-user",
            "expires_at": 9999999999,
        }

        with self.assertRaises(SyncTimeoutError):
            client.sync_players(valid_session, {"schema_version": 1, "players": [], "games": []})
        with self.assertRaises(SyncProtocolError):
            client.sync_players(valid_session, {"schema_version": 2, "players": [], "games": []})

    def test_configuration_is_checked_only_when_action_requires_it(self):
        config = SyncConfig.from_env({})
        with self.assertRaises(SyncNotConfigured):
            FirebaseSyncClient(config).send_password_reset("captain@example.com")


if __name__ == "__main__":
    unittest.main()
