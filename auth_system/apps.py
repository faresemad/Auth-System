from django.apps import AppConfig


class AuthSystemConfig(AppConfig):
    name = "auth_system"
    label = "auth_system"
    verbose_name = "Authentication System"

    def ready(self):
        import auth_system.openapi  # noqa: F401
