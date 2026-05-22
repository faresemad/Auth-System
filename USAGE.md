# Usage Guide

Complete walkthrough for integrating `django-auth-system` into a Django project.

---

## Table of Contents

1. [Quick Start — New Project](#quick-start--new-project)
2. [User Model Setup](#user-model-setup)
3. [Full Settings Reference](#full-settings-reference)
4. [Frontend Integration](#frontend-integration)
5. [API by Feature](#api-by-feature)
6. [2FA Flow Walkthrough](#2fa-flow-walkthrough)
7. [Error Handling](#error-handling)
8. [Django Admin](#django-admin)
9. [Extending the Package](#extending-the-package)

---

## Quick Start — New Project

### 1. Create a Django project

```bash
pip install django djangorestframework djangorestframework-simplejwt drf-spectacular redis pyotp qrcode
pip install django-auth-system

django-admin startproject myproject
cd myproject
python manage.py startapp accounts
```

### 2. Create a compatible User model

Write this in `accounts/models.py`:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
```

In `myproject/settings.py`:

```python
AUTH_USER_MODEL = "accounts.User"
```

### 3. Install the app

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    # Your apps
    "accounts",
    "auth_system",
]
```

### 4. Configure settings

```python
from datetime import timedelta

AUTH_SYSTEM = {
    "JWT_ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "JWT_REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "JWT_ACCESS_COOKIE_NAME": "access_token",
    "JWT_REFRESH_COOKIE_NAME": "refresh_token",
    "JWT_COOKIE_SECURE": False,          # True in production with HTTPS
    "JWT_COOKIE_SAMESITE": "Lax",
    "JWT_COOKIE_HTTPONLY": True,
    "REDIS_URL": "redis://127.0.0.1:6379/0",
    "PENDING_SESSION_TTL": 300,
    "PENDING_EMAIL_TTL": 3600,
    "TOTP_ISSUER_NAME": "MyApp",
    "BACKUP_CODES_COUNT": 10,
    "UPDATE_SESSION_AUTH_HASH": False,
    "LOGIN_THROTTLE_RATES": {
        "login": "10/min",
        "signup": "5/min",
        "password_reset": "5/min",
        "verify_2fa": "10/min",
    },
}

AUTHENTICATION_BACKENDS = [
    "auth_system.authentication.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "auth_system.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

FRONTEND_URL = "http://localhost:3000"   # Your SPA URL
DEFAULT_FROM_EMAIL = "noreply@myapp.com"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # dev only
```

### 5. Wire URLs

```python
# myproject/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("auth_system.urls")),
]
```

### 6. Migrate & run

```bash
python manage.py makemigrations accounts
python manage.py migrate
python manage.py runserver
```

---

## User Model Setup

The package expects your `AUTH_USER_MODEL` to have at minimum:

| Field / Method | Required | Used by |
|---|---|---|
| `email` | Yes | Login, signup, password reset |
| `password` | Yes | Every auth operation |
| `is_active` | Yes | Account disabled check, verification |
| `is_verified` | Recommended | VerifyAccountView sets it to `True` |
| `username` | Recommended | Admin display fallback |
| `get_full_name()` | Optional | Admin display |
| `check_password()` | Built-in | Password validation |

### Using Django's default User

If you use Django's default `auth.User`, note:
- The default model uses `username` as the identifier, not `email`. The `EmailAuthBackend` handles this for login, but you'll need to ensure the signup flow works.
- The `SignupSerializer` calls `User.objects.create_user()` which handles `username` + `email`.
- `is_verified` is not a field on the default model — the signup view sets it but the migration won't create it. Add it via a proxy model or a migration:

```python
# accounts/migrations/XXXX_add_is_verified.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("auth", "XXXX_migration_number")]
    operations = [
        migrations.AddField(
            model_name="user",
            name="is_verified",
            field=models.BooleanField(default=False),
        ),
    ]
```

### Recommended User model

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
```

---

## Full Settings Reference

### `AUTH_SYSTEM` dictionary

| Key | Default | Description |
|---|---|---|
| `JWT_ACCESS_TOKEN_LIFETIME` | `timedelta(minutes=15)` | How long the access cookie lives |
| `JWT_REFRESH_TOKEN_LIFETIME` | `timedelta(days=7)` | How long the refresh cookie lives |
| `JWT_ACCESS_COOKIE_NAME` | `"access_token"` | Cookie name for the access JWT |
| `JWT_REFRESH_COOKIE_NAME` | `"refresh_token"` | Cookie name for the refresh JWT |
| `JWT_COOKIE_SECURE` | `True` | Set `False` for local dev over HTTP |
| `JWT_COOKIE_SAMESITE` | `"Lax"` | SameSite policy for auth cookies |
| `JWT_COOKIE_HTTPONLY` | `True` | Prevents JS access to cookies |
| `REDIS_URL` | `"redis://127.0.0.1:6379/0"` | Redis connection string |
| `PENDING_SESSION_TTL` | `300` | 2FA handoff window in seconds |
| `PENDING_SESSION_PREFIX` | `"auth:pending:"` | Redis key prefix for 2FA sessions |
| `PENDING_EMAIL_TTL` | `3600` | Email change window in seconds |
| `TOTP_ISSUER_NAME` | `"AuthSystem"` | Issuer shown in authenticator apps |
| `BACKUP_CODES_COUNT` | `10` | Number of backup codes generated |
| `UPDATE_SESSION_AUTH_HASH` | `False` | Call `update_session_auth_hash` on password change |
| `LOGIN_THROTTLE_RATES` | (see below) | Per-endpoint rate limits |

Default throttle rates:

```python
LOGIN_THROTTLE_RATES = {
    "login": "10/min",
    "signup": "5/min",
    "password_reset": "5/min",
    "verify_2fa": "10/min",
}
```

Set a value to `None` to disable throttling for that endpoint.

### Standard Django settings required

```python
AUTH_USER_MODEL = "accounts.User"
FRONTEND_URL = "https://myapp.com"          # Used in email verification links
DEFAULT_FROM_EMAIL = "noreply@myapp.com"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
```

---

## Frontend Integration

All authentication is cookie-based. The server sets `HttpOnly` cookies — your frontend does **not** need to store or manage tokens in JavaScript.

### Signup

```js
// POST /api/auth/signup/
fetch("/api/auth/signup/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    username: "user",
    password: "Str0ng!Pass123",
    confirm_password: "Str0ng!Pass123",
    first_name: "John",
    last_name: "Doe",
  }),
});
// Response 201: { "detail": "User created successfully. ..." }
```

### Verify Email (link from email)

```
GET /api/auth/verify-account/?uid=<base64>&token=<token>
// Response 200: { "detail": "Account verified successfully." }
```

### Login

```js
// POST /api/auth/login/
fetch("/api/auth/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "...", password: "..." }),
  credentials: "include",                // ← send/receive cookies
});
// Response 200: cookies set automatically
```

If 2FA is enabled, the response is:

```json
{ "requires_2fa": true, "session_token": "uuid-string" }
```

### Authenticated Requests

Once logged in, the `access_token` cookie is automatically sent with every request (if `credentials: "include"` is set). No `Authorization` header needed.

```js
fetch("/api/auth/change-password/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ old_password: "...", new_password: "...", confirm_password: "..." }),
  credentials: "include",
});
```

### Token Refresh

The refresh cookie is scoped to `/api/auth/refresh/` and is sent automatically.

```js
// POST /api/auth/refresh/  (no body needed)
fetch("/api/auth/refresh/", {
  method: "POST",
  credentials: "include",
});
// Response 200: new access_token cookie set
```

**Recommended:** Call refresh before every request or when you get a 401:

```js
async function authFetch(url, options = {}) {
  let resp = await fetch(url, { ...options, credentials: "include" });
  if (resp.status === 401) {
    const refreshResp = await fetch("/api/auth/refresh/", {
      method: "POST",
      credentials: "include",
    });
    if (refreshResp.ok) {
      resp = await fetch(url, { ...options, credentials: "include" });
    }
  }
  return resp;
}
```

---

## API by Feature

### Account Management

| Action | Method | Path | Body / Params |
|---|---|---|---|
| Signup | POST | `/api/auth/signup/` | `{ email, username, password, confirm_password, first_name?, last_name? }` |
| Verify email | GET | `/api/auth/verify-account/` | `?uid=<base64>&token=<token>` |
| Login | POST | `/api/auth/login/` | `{ email, password }` |
| Logout | POST | `/api/auth/logout/` | _(cookie only)_ |
| Refresh token | POST | `/api/auth/refresh/` | _(cookie only)_ |

### Password

| Action | Method | Path | Body |
|---|---|---|---|
| Request reset | POST | `/api/auth/password-reset/` | `{ email }` |
| Confirm reset | POST | `/api/auth/password-reset-confirm/` | `{ uid, token, password, confirm_password }` |
| Change password | POST | `/api/auth/change-password/` | `{ old_password, new_password, confirm_password }` |

### Email

| Action | Method | Path | Body / Params |
|---|---|---|---|
| Request change | POST | `/api/auth/change-email/` | `{ new_email }` |
| Confirm change | GET | `/api/auth/change-email-confirm/` | `?uid=<base64>&token=<token>` |

### 2FA

| Action | Method | Path | Body |
|---|---|---|---|
| Setup (get QR) | POST | `/api/auth/2fa/setup/` | _(none)_ |
| Enable | POST | `/api/auth/2fa/enable/` | `{ code }` |
| Disable | POST | `/api/auth/2fa/disable/` | `{ password, code }` |
| Verify login (2FA) | POST | `/api/auth/2fa/verify-login/` | `{ session_token, code }` |
| List backup codes | GET | `/api/auth/2fa/backup-codes/` | _(none)_ |
| Regenerate codes | POST | `/api/auth/2fa/backup-codes/` | `{ password }` |

---

## 2FA Flow Walkthrough

### Step 1: Generate TOTP Secret

Authenticated user calls:

```http
POST /api/auth/2fa/setup/
Cookie: access_token=<jwt>
```

Response:

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBOR...",
  "otpauth_uri": "otpauth://totp/AuthSystem:user@example.com?secret=..."
}
```

The user scans the QR code with Google Authenticator / Authy, or enters the secret manually.

### Step 2: Enable 2FA

```http
POST /api/auth/2fa/enable/
Cookie: access_token=<jwt>
Content-Type: application/json

{ "code": "123456" }
```

On success:

```json
{
  "detail": "Two-factor authentication enabled.",
  "backup_codes": ["A1B2C3D4", "E5F6G7H8", "..."]
}
```

**Store the backup codes.** They are returned only once.

### Step 3: Login with 2FA

```
POST /api/auth/login/              →  { "requires_2fa": true,
                                         "session_token": "uuid" }
POST /api/auth/2fa/verify-login/   →  Set-Cookie: access_token=...
   { session_token, code }            Set-Cookie: refresh_token=...
```

The `code` field accepts either:
- A 6-digit TOTP code from the authenticator app
- An 8-character backup code (case-insensitive)

### Step 4: Disable 2FA

```http
POST /api/auth/2fa/disable/
Cookie: access_token=<jwt>
Content-Type: application/json

{ "password": "current-password", "code": "123456" }
```

Requires both the current password **and** a TOTP code to prevent an attacker with a stolen session from disabling 2FA.

---

## Error Handling

All errors follow DRF conventions. A typical error response:

```json
{
  "field_name": ["Error message."]
}
```

Or for general errors:

```json
{
  "detail": "Error message."
}
```

### Common error codes

| HTTP Status | Code | Meaning |
|---|---|---|
| 400 | `invalid_totp` | Wrong or expired 2FA code |
| 400 | `setup_required` | Must call `/2fa/setup/` before `/2fa/enable/` |
| 400 | `2fa_already_enabled` | Cannot enable what is already on |
| 400 | `2fa_not_enabled` | Cannot disable what is already off |
| 400 | `password_mismatch` | `password` and `confirm_password` don't match |
| 401 | `invalid_credentials` | Wrong email or password |
| 401 | `session_expired` | 2FA session token is invalid or expired |
| 401 | `invalid_refresh_token` | Refresh cookie is invalid or expired |
| 403 | `account_disabled` | Account is inactive |
| 429 | `rate_limited` | Too many requests to this endpoint |

### Handling token refresh failure

When both the access token and refresh token expire, the user must log in again. Your frontend should redirect to the login page:

```js
const resp = await fetch("/api/auth/some-endpoint/", { credentials: "include" });
if (resp.status === 401) {
  const refreshResp = await fetch("/api/auth/refresh/", { method: "POST", credentials: "include" });
  if (!refreshResp.ok) {
    window.location.href = "/login";
  }
}
```

---

## Django Admin

The `TwoFactor` model is registered with a full-featured admin interface at `/admin/auth_system/twofactor/`.

Features:
- List view with 2FA status badges (green ✓ / red ✗)
- Search by email, username, name
- Filter by enabled status and dates
- Masked TOTP secret (only last 4 chars visible)
- Backup codes displayed with copy-friendly `<code>` tags
- Bulk actions: enable 2FA, disable 2FA, clear backup codes

---

## Extending the Package

### Override a view

```python
# myapp/views.py
from auth_system.views.login import LoginView
from auth_system.exceptions import InvalidCredentials


class CustomLoginView(LoginView):
    def post(self, request):
        # Custom logic before or after login
        response = super().post(request)
        # Add extra data to the response
        if response.status_code == 200:
            response.data["user_role"] = request.user.role
        return response
```

```python
# myapp/urls.py
from django.urls import path
from myapp.views import CustomLoginView

urlpatterns = [
    path("api/auth/login/", CustomLoginView.as_view(), name="login"),
]
```

### Use your own serializer

```python
from auth_system.serializers.login import LoginSerializer


class ExtendedLoginSerializer(LoginSerializer):
    device_id = serializers.CharField(write_only=True)
```

### Customize email templates

Subclass `EmailService` and override the `send_*` methods:

```python
from auth_system.services.email_service import EmailService
from django.template.loader import render_to_string


class CustomEmailService(EmailService):
    @staticmethod
    def send_verification_email(user, request=None):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        html = render_to_string("emails/verify.html", {"uid": uid, "token": token})
        send_mail("Verify", "", "noreply@myapp.com", [user.email], html_message=html)
```

Then monkey-patch or use a custom login view that references your service.

### Disable throttling

```python
AUTH_SYSTEM = {
    "LOGIN_THROTTLE_RATES": {
        "login": None,           # unlimited login attempts
        "signup": None,
        "password_reset": None,
        "verify_2fa": None,
    },
}
```
