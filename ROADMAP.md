# Roadmap & Missing Functionality

This document tracks gaps in the current release and planned improvements.

---

## Bugs Fixed in This Release

- [x] **`disable.py`** — Inverted condition: `if twofa.is_2fa_enabled` now reads `if not twofa.is_2fa_enabled` so `TwoFANotEnabled` is raised correctly when 2FA is not enabled.
- [x] **`backup_codes.py`** — Same inverted condition in both `get()` and `post()` methods.

---

## Implemented Features

### ✅ Email Authentication Backend

**File:** `auth_system/authentication.py`

Added `EmailAuthBackend` — authenticates users by email instead of username. Add to `AUTHENTICATION_BACKENDS`:

```python
AUTHENTICATION_BACKENDS = [
    "auth_system.authentication.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

### ✅ Rate Limiting / Account Lockout

**File:** `auth_system/throttles.py`

DRF `AnonRateThrottle` subclasses for login, signup, password reset, and 2FA verification endpoints. Configure via `AUTH_SYSTEM`:

```python
AUTH_SYSTEM = {
    "LOGIN_THROTTLE_RATES": {
        "login": "10/min",
        "signup": "5/min",
        "password_reset": "5/min",
        "verify_2fa": "10/min",
    },
}
```

### ✅ Secure Email Change (Redis-backed)

**Files:** `auth_system/services/redis_service.py`, `auth_system/views/change_email.py`

Pending new emails are stored in Redis keyed by `user_pk` with a 1-hour TTL instead of being passed as a query parameter. The confirm endpoint reads from Redis.

### ✅ Session Invalidation on Password / Email Change

**Files:** `auth_system/models.py`, `auth_system/services/jwt_service.py`, `auth_system/authentication.py`

Added `token_version` field to the `TwoFactor` model. JWT tokens embed this version. When password or email changes, the version is incremented, immediately invalidating all existing tokens.

Run migration:
```bash
python manage.py migrate auth_system
```

### ✅ Configurable `update_session_auth_hash`

**Setting:** `AUTH_SYSTEM["UPDATE_SESSION_AUTH_HASH"]` (default `False`)

When enabled, `ChangePasswordView` calls `update_session_auth_hash(request, user)` to keep session-based clients logged in.

### ✅ Consistent Password Validation Errors

**File:** `auth_system/serializers/password.py`

Mismatch errors now use the `PasswordMismatch` exception with a consistent `"Passwords do not match."` message, rather than inconsistent field-level messages.

---

## Missing Core Functionality

### 1. User Model Customisation

The package assumes a `User` model with at minimum: `email`, `password`, `is_active`, `get_full_name()`, `username`, `change_email()`.

- `SignupSerializer` calls `User.objects.create_user()` and sets `is_active` — this field exists on Django's default `AbstractUser`.
- **Fix:** Provide a recommended abstract base user model, or document exactly what fields/methods are expected.

### 2. URL Prefix Helper

The URLs are hard-coded to the paths defined in `urls.py`. You can already use Django's `include()` with a prefix:

```python
urlpatterns = [
    path("api/auth/", include("auth_system.urls")),
]
```

### 3. OAuth2 / Social Auth

No support for Google, GitHub, or other social login providers.

- Consider integrating `django-allauth` or `social-auth-app-django`.

### 4. No Test Suite

The package has zero tests. Every endpoint is untested.

- DRF's `APITestCase` / `APIClient` should be used.
- Need at minimum: signup → verify → login → refresh → logout flow tests.

### 5. Missing `.env` / Settings Documentation

`REDIS_URL`, `FRONTEND_URL`, `EMAIL_*` are all hard dependencies but their setup is undocumented.

---

## Enhancement Opportunities

| Feature | Description |
|---|---|
| **WebAuthn / Passkeys** | Passwordless FIDO2 authentication as a 2FA alternative |
| **Magic Link Login** | Passwordless email-based login |
| **Session Management UI** | List and revoke active sessions per user |
| **Email Templates** | Customisable HTML email templates instead of plaintext |
| **Audit Log** | Log all auth events (login, 2fa, password change, etc.) |
| **Cookie Path Config** | Make `path` for refresh cookie configurable via `AUTH_SYSTEM` settings |
| **Concurrent 2FA Sessions** | Support multiple pending 2FA sessions per user (currently one overwrites) |
| **Django Ninja Support** | Add a `ninja`-based router as an alternative to DRF |
| **Async Email Backend** | Use Django's `EmailBackend` with Celery / RQ / huey for non-blocking sends |

---

## Contribution

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

Please make sure existing (and new) tests pass before submitting.
