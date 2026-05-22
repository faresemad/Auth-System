from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from ..exceptions import InvalidRefreshToken
from ..utils import get_or_create_2fa


class JWTService:
    @staticmethod
    def generate_tokens(user) -> dict[str, str]:
        twofa = get_or_create_2fa(user)
        refresh = RefreshToken.for_user(user)
        refresh["token_version"] = twofa.token_version
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def refresh_access_token(refresh_token_str: str) -> str:
        """Generate a fresh access token from an existing refresh token."""
        try:
            refresh = RefreshToken(refresh_token_str)
            return str(refresh.access_token)
        except TokenError as exc:
            raise InvalidRefreshToken() from exc

    @staticmethod
    def blacklist_token(refresh_token_str: str) -> None:
        """
        Blacklist a refresh token on logout.
        Silently skipped if token_blacklist app is not installed or token is malformed.
        """
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
        except Exception:
            pass
