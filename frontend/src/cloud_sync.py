"""Optional cloud sync: AWS Cognito for auth, S3 for storage.

Nothing in this module is called unless the user explicitly signs in and
clicks sync — the rest of the app never depends on it (F-081, offline
operation). Config comes entirely from environment variables so the app
works with sync unconfigured (raises SyncNotConfigured) until the AWS
resources from infra/aws_cloud_sync/provision.py exist and their IDs are
exported.
"""
import json
import os

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "")
COGNITO_IDENTITY_POOL_ID = os.getenv("COGNITO_IDENTITY_POOL_ID", "")
SYNC_BUCKET = os.getenv("SYNC_BUCKET", "")


class SyncNotConfigured(RuntimeError):
    """Raised when the AWS sync environment variables haven't been set yet."""


def _require_config() -> None:
    missing = [
        name
        for name, val in [
            ("COGNITO_USER_POOL_ID", COGNITO_USER_POOL_ID),
            ("COGNITO_APP_CLIENT_ID", COGNITO_APP_CLIENT_ID),
            ("COGNITO_IDENTITY_POOL_ID", COGNITO_IDENTITY_POOL_ID),
            ("SYNC_BUCKET", SYNC_BUCKET),
        ]
        if not val
    ]
    if missing:
        raise SyncNotConfigured(
            "Cloud sync isn't set up yet (missing: " + ", ".join(missing) + "). "
            "Run infra/aws_cloud_sync/provision.py and export the values it prints."
        )


def sign_in(email: str, password: str) -> dict:
    """Authenticate against the Cognito User Pool and exchange the result for
    scoped, temporary AWS credentials from the Identity Pool.

    Returns a session dict meant to live only in st.session_state for the
    duration of the browser session; nothing here is written to disk.
    """
    _require_config()
    idp = boto3.client("cognito-idp", region_name=AWS_REGION)
    auth_result = idp.initiate_auth(
        ClientId=COGNITO_APP_CLIENT_ID,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": email, "PASSWORD": password},
    )["AuthenticationResult"]
    id_token = auth_result["IdToken"]

    identity = boto3.client("cognito-identity", region_name=AWS_REGION)
    login_key = f"cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
    identity_id = identity.get_id(
        IdentityPoolId=COGNITO_IDENTITY_POOL_ID,
        Logins={login_key: id_token},
    )["IdentityId"]
    creds = identity.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins={login_key: id_token},
    )["Credentials"]

    return {
        "identity_id": identity_id,
        "access_key": creds["AccessKeyId"],
        "secret_key": creds["SecretKey"],
        "session_token": creds["SessionToken"],
    }


def _s3_client(session: dict):
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=session["access_key"],
        aws_secret_access_key=session["secret_key"],
        aws_session_token=session["session_token"],
    )


def _object_key(session: dict) -> str:
    # The bucket's IAM policy scopes each identity to exactly this prefix
    # (arn:...:bucket/users/${cognito-identity.amazonaws.com:sub}/*), so a
    # signed-in user can never read or write another user's data.
    return f"users/{session['identity_id']}/players.json"


def sync_upload(session: dict, payload: dict) -> None:
    """Upload a JSON-serializable payload to this user's scoped S3 prefix."""
    body = json.dumps(payload, indent=2).encode("utf-8")
    _s3_client(session).put_object(
        Bucket=SYNC_BUCKET,
        Key=_object_key(session),
        Body=body,
        ContentType="application/json",
    )


def sync_download(session: dict) -> dict:
    """Download this user's synced payload. Returns {} if nothing was synced yet."""
    client = _s3_client(session)
    try:
        obj = client.get_object(Bucket=SYNC_BUCKET, Key=_object_key(session))
    except client.exceptions.NoSuchKey:
        return {}
    return json.loads(obj["Body"].read().decode("utf-8"))
