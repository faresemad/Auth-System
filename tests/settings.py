SECRET_KEY = "test-secret-key-not-for-production"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "auth_system",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

AUTHENTICATION_BACKENDS = [
    "auth_system.authentication.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "auth_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

AUTH_SYSTEM = {
    "JWT_COOKIE_SECURE": False,
    "REDIS_URL": "redis://127.0.0.1:6379/0",
}

FRONTEND_URL = "http://localhost:3000"
DEFAULT_FROM_EMAIL = "noreply@test.com"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "auth_system.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
