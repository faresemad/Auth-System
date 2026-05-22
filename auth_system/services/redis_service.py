import uuid

import redis

from ..conf import auth_settings


class PendingSessionService:
    """
    Short-lived Redis sessions that bridge credential validation and 2FA
    verification. The session token is issued after a successful password
    check and consumed (deleted) once the TOTP code is accepted.

    Key schema:  auth:pending:<uuid4>  →  "<user_pk>"
    TTL:         AUTH_SYSTEM['PENDING_SESSION_TTL'] seconds (default 300 s)
    """

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                auth_settings.REDIS_URL,
                decode_responses=True,
            )
        return self._client

    def _key(self, session_token: str) -> str:
        return f"{auth_settings.PENDING_SESSION_PREFIX}{session_token}"

    def create_session(self, user_pk) -> str:
        """Store user_pk under a fresh UUID token and return the token."""
        session_token = str(uuid.uuid4())
        self.client.set(
            self._key(session_token),
            str(user_pk),
            ex=auth_settings.PENDING_SESSION_TTL,
        )
        return session_token

    def get_user_pk(self, session_token: str) -> str | None:
        """Return the stored user_pk, or None if the session is missing/expired."""
        return self.client.get(self._key(session_token))

    def delete_session(self, session_token: str) -> None:
        """Consume the session token, preventing replay attacks."""
        self.client.delete(self._key(session_token))


class PendingEmailService:
    """
    Stores a pending email change in Redis so that the confirm endpoint can
    retrieve it without trusting a query-string parameter.

    Key schema:  "auth:pending-email:<user_pk>"  →  "<new_email>"
    TTL:         1 hour (3600 s)
    """

    PREFIX = "auth:pending-email:"
    TTL = 3600

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                auth_settings.REDIS_URL,
                decode_responses=True,
            )
        return self._client

    def _key(self, user_pk: int) -> str:
        return f"{self.PREFIX}{user_pk}"

    def store(self, user_pk: int, new_email: str) -> None:
        self.client.set(self._key(user_pk), new_email, ex=self.TTL)

    def get(self, user_pk: int) -> str | None:
        return self.client.get(self._key(user_pk))

    def delete(self, user_pk: int) -> None:
        self.client.delete(self._key(user_pk))
