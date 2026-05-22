from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid email or password."
    default_code = "invalid_credentials"


class AccountDisabled(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "This account has been disabled."
    default_code = "account_disabled"


class PendingSessionExpired(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "2FA session expired or invalid. Please log in again."
    default_code = "session_expired"


class InvalidTOTPCode(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid or expired 2FA code."
    default_code = "invalid_totp"


class TwoFAAlreadyEnabled(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Two-factor authentication is already enabled."
    default_code = "2fa_already_enabled"


class TwoFANotEnabled(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Two-factor authentication is not enabled."
    default_code = "2fa_not_enabled"


class SetupRequired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Call /auth/2fa/setup/ first to generate a TOTP secret."
    default_code = "setup_required"


class InvalidRefreshToken(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Refresh token is invalid or has expired."
    default_code = "invalid_refresh_token"


class RateLimited(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Too many requests. Please try again later."
    default_code = "rate_limited"


class EmailAlreadyVerified(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This account is already verified."
    default_code = "email_already_verified"


class PasswordMismatch(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Passwords do not match."
    default_code = "password_mismatch"
