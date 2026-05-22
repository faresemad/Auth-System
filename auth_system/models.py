from django.conf import settings
from django.db import models


class TwoFactor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="twofa",
    )

    is_2fa_enabled = models.BooleanField(default=False)

    totp_secret = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    backup_codes = models.JSONField(
        default=list,
        blank=True,
    )

    token_version = models.PositiveIntegerField(
        default=0,
        help_text="Increment to invalidate all existing JWT tokens for this user.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_two_factor"
        verbose_name = "Two Factor Authentication"
        verbose_name_plural = "Two Factor Authentications"

    def __str__(self):
        return f"{self.user.email} - 2FA"
