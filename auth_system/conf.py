from datetime import timedelta

from django.test.signals import setting_changed

DEFAULTS: dict = {
    # JWT
    "JWT_ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "JWT_REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "JWT_ACCESS_COOKIE_NAME": "access_token",
    "JWT_REFRESH_COOKIE_NAME": "refresh_token",
    "JWT_COOKIE_SECURE": True,
    "JWT_COOKIE_SAMESITE": "Lax",
    "JWT_COOKIE_HTTPONLY": True,
    # Redis
    "REDIS_URL": "redis://127.0.0.1:6379/0",
    "PENDING_SESSION_TTL": 300,
    "PENDING_SESSION_PREFIX": "auth:pending:",
    "PENDING_EMAIL_TTL": 3600,
    # 2FA
    "TOTP_ISSUER_NAME": "AuthSystem",
    "BACKUP_CODES_COUNT": 10,
    # Session auth
    "UPDATE_SESSION_AUTH_HASH": False,
}

# ── Login rate limiting ─────────────────────────────────────────────
LOGIN_THROTTLE_RATES: dict[str, str | None] = {
    "login": "10/min",
    "signup": "5/min",
    "password_reset": "5/min",
    "verify_2fa": "10/min",
}


class _AuthSettings:
    """
    Lazy proxy over settings.AUTH_SYSTEM that merges user overrides with defaults.
    Attribute access triggers a single load; call .reload() to bust the cache.
    """

    def __init__(self, defaults: dict) -> None:
        self._defaults = defaults
        self._cached: dict | None = None

    def _load(self) -> dict:
        from django.conf import settings as django_settings

        return {**self._defaults, **getattr(django_settings, "AUTH_SYSTEM", {})}

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if self._cached is None:
            self._cached = self._load()
        try:
            return self._cached[name]
        except KeyError:
            raise AttributeError(f"AUTH_SYSTEM has no setting '{name}'")

    def reload(self) -> None:
        self._cached = None


auth_settings = _AuthSettings(DEFAULTS)


def _reload_on_change(*args, **kwargs) -> None:
    if kwargs.get("setting") == "AUTH_SYSTEM":
        auth_settings.reload()


setting_changed.connect(_reload_on_change)
