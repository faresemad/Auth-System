from rest_framework import serializers


class Verify2FALoginSerializer(serializers.Serializer):
    session_token = serializers.UUIDField()
    code = serializers.CharField(
        min_length=6,
        max_length=8,
        trim_whitespace=True,
        help_text="6-digit TOTP code or 8-character backup code.",
    )


class Setup2FASerializer(serializers.Serializer):
    """Response shape returned by Setup2FAView."""

    secret = serializers.CharField(read_only=True)
    qr_code = serializers.CharField(read_only=True)
    otpauth_uri = serializers.CharField(read_only=True)


class Enable2FASerializer(serializers.Serializer):
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        trim_whitespace=True,
        help_text="6-digit TOTP code from your authenticator app.",
    )


class Disable2FASerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        trim_whitespace=True,
        help_text="6-digit TOTP code confirming the disable request.",
    )


class BackupCodeSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
        help_text="Current account password required to regenerate backup codes.",
    )
