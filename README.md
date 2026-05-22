# django-auth-system

A pluggable Django authentication system with JWT cookies, email verification, password reset, and TOTP-based 2FA with backup codes.

Built on **Django REST Framework** + **SimpleJWT** — designed for cookie-based SPA / mobile clients.

---

## Features

- [x] **Signup** with email + password, auto-deactivate until email is verified
- [x] **Email verification** via token link
- [x] **Login** — returns JWT in HttpOnly cookies (or hands off to 2FA)
- [x] **Logout** — blacklists the refresh token, clears cookies
- [x] **Token refresh** — silent refresh via the refresh-token cookie
- [x] **Password reset** — request + confirm (token-based)
- [x] **Change password** — authenticated user changes own password
- [x] **Change email** — request + confirm (token-based)
- [x] **TOTP 2FA** — setup via QR code, enable/disable, backup codes
- [x] **Backup codes** — generate, list, consume, regenerate (10 codes by default)
- [x] **Pending session** — Redis-backed 2FA handoff (5-minute TTL)
- [x] **Django admin integration** — manage 2FA per user
- [x] **OpenAPI schema** — drf-spectacular extension for cookie-JWT auth
- [x] **Email authentication backend** — authenticate by email, not username
- [x] **Rate limiting** — login, signup, password-reset, and 2FA-verify throttles
- [x] **Session invalidation** — password/email change invalidates all existing JWT tokens
- [x] **Secure email change** — pending email stored in Redis, not in URL params
- [x] **Configurable session hash** — optional `update_session_auth_hash()` support

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.10+ |
| Django | 4.2+ |
| djangorestframework | 3.14+ |
| djangorestframework-simplejwt | 5.3+ |
| pyotp | 2.8+ |
| qrcode | 7.4+ |
| redis | 5.0+ |
| drf-spectacular | 0.27+ |

---

## Installation

```bash
pip install django-auth-system
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "auth_system",
    ...
]
```

Include the URLs:

```python
# urls.py
urlpatterns = [
    path("api/auth/", include("auth_system.urls")),
]
```

Run migrations:

```bash
python manage.py migrate auth_system
```

---

## Configuration

All settings live under the `AUTH_SYSTEM` dict in your `settings.py`:

```python
AUTH_SYSTEM = {
    # JWT
    "JWT_ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "JWT_REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "JWT_ACCESS_COOKIE_NAME": "access_token",
    "JWT_REFRESH_COOKIE_NAME": "refresh_token",
    "JWT_COOKIE_SECURE": True,          # set False for local dev over HTTP
    "JWT_COOKIE_SAMESITE": "Lax",
    "JWT_COOKIE_HTTPONLY": True,
    # Redis
    "REDIS_URL": "redis://127.0.0.1:6379/0",
    "PENDING_SESSION_TTL": 300,          # seconds (2FA handoff window)
    "PENDING_SESSION_PREFIX": "auth:pending:",
    "PENDING_EMAIL_TTL": 3600,           # seconds (email change window)
    # 2FA
    "TOTP_ISSUER_NAME": "AuthSystem",
    "BACKUP_CODES_COUNT": 10,
    # Session
    "UPDATE_SESSION_AUTH_HASH": False,   # set True for session-based auth clients
    # Rate limiting — set None to disable
    "LOGIN_THROTTLE_RATES": {
        "login": "10/min",
        "signup": "5/min",
        "password_reset": "5/min",
        "verify_2fa": "10/min",
    },
}
```

You also need standard Django settings:

```python
AUTH_USER_MODEL = "your_app.User"   # or django's default
FRONTEND_URL = "https://your-frontend.com"
DEFAULT_FROM_EMAIL = "noreply@your-domain.com"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
```

### Authentication backends

Add the custom **email-based** authentication backend (if your User model uses `email` as the unique identifier):

```python
AUTHENTICATION_BACKENDS = [
    "auth_system.authentication.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

### DRF settings

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "auth_system.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
```

### SimpleJWT (required for token blacklisting)

```python
INSTALLED_APPS += ["rest_framework_simplejwt.token_blacklist"]
```

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/signup/` | public | Create account |
| GET | `/api/auth/verify-account/?uid=&token=` | public | Verify email |
| POST | `/api/auth/login/` | public | Login (password) |
| POST | `/api/auth/logout/` | cookie JWT | Logout, blacklist token |
| POST | `/api/auth/refresh/` | refresh cookie | Refresh access token |
| POST | `/api/auth/password-reset/` | public | Request password reset |
| POST | `/api/auth/password-reset-confirm/` | public | Confirm password reset |
| POST | `/api/auth/change-password/` | cookie JWT | Change password |
| POST | `/api/auth/change-email/` | cookie JWT | Request email change |
| GET | `/api/auth/change-email-confirm/` | public | Confirm email change |
| POST | `/api/auth/2fa/setup/` | cookie JWT | Generate TOTP secret + QR |
| POST | `/api/auth/2fa/enable/` | cookie JWT | Enable 2FA (verify TOTP) |
| POST | `/api/auth/2fa/disable/` | cookie JWT | Disable 2FA (password + TOTP) |
| POST | `/api/auth/2fa/verify-login/` | public | Complete 2FA login step |
| GET | `/api/auth/2fa/backup-codes/` | cookie JWT | List backup codes |
| POST | `/api/auth/2fa/backup-codes/` | cookie JWT | Regenerate backup codes |

---

## Session Invalidation

Each user's `TwoFactor` record has a `token_version` field (default 0). Every JWT token embeds this version. When any of these events occur, the version is incremented and all existing JWT tokens become invalid:

- Password changed (via `change-password/` or `password-reset-confirm/`)
- Email changed (via `change-email-confirm/`)

This protects against token replay after sensitive account changes.

---

## 2FA Login Flow

```
┌──────────┐    POST /login/         ┌──────────┐
│          │  ──────────────────────► │          │
│  Client  │    {email, password}     │  Server  │
│          │  ◄────────────────────── │          │
└──────────┘    {requires_2fa: true,  └──────────┘
                  session_token: uuid}

┌──────────┐    POST /2fa/verify-login/  ┌──────────┐
│          │  ──────────────────────────► │          │
│  Client  │    {session_token, code}     │  Server  │
│          │  ◄────────────────────────── │          │
└──────────┘    Set-Cookie: access_token  └──────────┘
                 Set-Cookie: refresh_token
```

---

## Development

```bash
git clone https://github.com/your-username/django-auth-system
cd django-auth-system
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
```

### Running tests

```bash
pytest tests/ -v
```

Requires a local Redis instance on `127.0.0.1:6379` or override `REDIS_URL` in `tests/settings.py`.

---

## License

MIT
