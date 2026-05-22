from django.urls import path

from .views.change_email import ChangeEmailConfirmView, ChangeEmailRequestView
from .views.change_password import ChangePasswordView
from .views.login import LoginView
from .views.logout import LogoutView
from .views.password_reset import PasswordResetConfirmView, PasswordResetRequestView
from .views.refresh import TokenRefreshView
from .views.signup import SignupView
from .views.twofa.backup_codes import BackupCodesView
from .views.twofa.disable import Disable2FAView
from .views.twofa.enable import Enable2FAView
from .views.twofa.setup import Setup2FAView
from .views.twofa.verify import Verify2FALoginView
from .views.verify import VerifyAccountView

app_name = "auth_system"

urlpatterns = [
    # Core auth
    path("signup/", SignupView.as_view(), name="signup"),
    path("verify-account/", VerifyAccountView.as_view(), name="verify-account"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Password management
    path(
        "password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"
    ),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    # Email management
    path("change-email/", ChangeEmailRequestView.as_view(), name="change-email-request"),
    path(
        "change-email-confirm/",
        ChangeEmailConfirmView.as_view(),
        name="change-email-confirm",
    ),
    # 2FA management (all require authentication)
    path("2fa/setup/", Setup2FAView.as_view(), name="2fa-setup"),
    path("2fa/enable/", Enable2FAView.as_view(), name="2fa-enable"),
    path("2fa/disable/", Disable2FAView.as_view(), name="2fa-disable"),
    # 2FA login flow (public — uses Redis session_token)
    path("2fa/verify-login/", Verify2FALoginView.as_view(), name="2fa-verify-login"),
    # Backup code management (requires authentication)
    path("2fa/backup-codes/", BackupCodesView.as_view(), name="2fa-backup-codes"),
]
