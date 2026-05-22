from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import TwoFactor


@admin.register(TwoFactor)
class TwoFactorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_email",
        "user_name",
        "is_2fa_enabled_badge",
        "backup_codes_count",
        "has_totp_secret",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "user_email")

    list_filter = (
        "is_2fa_enabled",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__email",
        "user__username",
        "user__first_name",
        "user__last_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "masked_totp_secret",
        "backup_codes_pretty",
    )

    autocomplete_fields = ("user",)

    ordering = ("-created_at",)

    list_per_page = 25

    fieldsets = (
        (
            "User Information",
            {
                "fields": (
                    "user",
                    "is_2fa_enabled",
                )
            },
        ),
        (
            "Security",
            {
                "fields": (
                    "masked_totp_secret",
                    "backup_codes_pretty",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def user_name(self, obj):
        full_name = obj.user.get_full_name()

        if full_name:
            return full_name

        return obj.user.username

    user_name.short_description = "User"

    def is_2fa_enabled_badge(self, obj):
        if obj.is_2fa_enabled:
            color = "#16a34a"
            text = "Enabled"
        else:
            color = "#dc2626"
            text = "Disabled"

        return format_html(
            """
            <span style="
                background:{};
                color:white;
                padding:4px 10px;
                border-radius:12px;
                font-weight:bold;
                font-size:12px;
            ">
                {}
            </span>
            """,
            color,
            text,
        )

    is_2fa_enabled_badge.short_description = "2FA Status"

    def has_totp_secret(self, obj):
        return bool(obj.totp_secret)

    has_totp_secret.boolean = True
    has_totp_secret.short_description = "Has Secret"

    def backup_codes_count(self, obj):
        return len(obj.backup_codes or [])

    backup_codes_count.short_description = "Backup Codes"

    def masked_totp_secret(self, obj):
        if not obj.totp_secret:
            return "-"

        visible_chars = 4

        masked = (
            "*" * max(len(obj.totp_secret) - visible_chars, 0)
            + obj.totp_secret[-visible_chars:]
        )

        return mark_safe(f"<code>{masked}</code>")

    masked_totp_secret.short_description = "TOTP Secret"

    def backup_codes_pretty(self, obj):
        if not obj.backup_codes:
            return "-"

        html = "<br>".join(f"<code>{code}</code>" for code in obj.backup_codes)

        return mark_safe(html)

    backup_codes_pretty.short_description = "Backup Codes"

    actions = (
        "enable_2fa",
        "disable_2fa",
        "clear_backup_codes",
    )

    @admin.action(description="Enable 2FA for selected users")
    def enable_2fa(self, request, queryset):
        updated = queryset.update(is_2fa_enabled=True)

        self.message_user(
            request,
            f"{updated} users enabled successfully.",
        )

    @admin.action(description="Disable 2FA for selected users")
    def disable_2fa(self, request, queryset):
        updated = queryset.update(is_2fa_enabled=False)

        self.message_user(
            request,
            f"{updated} users disabled successfully.",
        )

    @admin.action(description="Clear backup codes")
    def clear_backup_codes(self, request, queryset):
        updated = queryset.update(backup_codes=[])

        self.message_user(
            request,
            f"Backup codes cleared for {updated} users.",
        )
