import base64
import io
import secrets

import pyotp
import qrcode

from ..conf import auth_settings


class TOTPService:
    @staticmethod
    def generate_secret() -> str:
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(email: str, secret: str) -> str:
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=auth_settings.TOTP_ISSUER_NAME,
        )

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Accept codes from the current and adjacent windows (+/-30 s drift)."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)

    @staticmethod
    def generate_qr_code_base64(email: str, secret: str) -> str:
        """Return a base64-encoded PNG of the TOTP provisioning QR code."""
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=email,
            issuer_name=auth_settings.TOTP_ISSUER_NAME,
        )
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    @staticmethod
    def generate_backup_codes() -> list[str]:
        count = auth_settings.BACKUP_CODES_COUNT
        return [secrets.token_hex(4).upper() for _ in range(count)]

    @staticmethod
    def consume_backup_code(
        backup_codes: list[str],
        code: str,
    ) -> tuple[bool, list[str]]:
        """
        Validate and remove a backup code in one step.
        Returns (is_valid, updated_codes).
        """
        normalized = code.upper()
        if normalized in backup_codes:
            return True, [c for c in backup_codes if c != normalized]
        return False, backup_codes
