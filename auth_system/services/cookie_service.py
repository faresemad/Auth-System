from django.http import HttpResponse

from ..conf import auth_settings


class CookieService:
    @staticmethod
    def set_auth_cookies(
        response: HttpResponse,
        access_token: str,
        refresh_token: str,
    ) -> None:
        access_max_age = int(auth_settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds())
        refresh_max_age = int(auth_settings.JWT_REFRESH_TOKEN_LIFETIME.total_seconds())

        response.set_cookie(
            auth_settings.JWT_ACCESS_COOKIE_NAME,
            access_token,
            max_age=access_max_age,
            httponly=auth_settings.JWT_COOKIE_HTTPONLY,
            secure=auth_settings.JWT_COOKIE_SECURE,
            samesite=auth_settings.JWT_COOKIE_SAMESITE,
        )
        # Refresh token is scoped to the refresh endpoint so it isn't sent with
        # every request, minimising the exposure window.
        response.set_cookie(
            auth_settings.JWT_REFRESH_COOKIE_NAME,
            refresh_token,
            max_age=refresh_max_age,
            httponly=auth_settings.JWT_COOKIE_HTTPONLY,
            secure=auth_settings.JWT_COOKIE_SECURE,
            samesite=auth_settings.JWT_COOKIE_SAMESITE,
            path="/api/auth/refresh/",
        )

    @staticmethod
    def clear_auth_cookies(response: HttpResponse) -> None:
        response.delete_cookie(auth_settings.JWT_ACCESS_COOKIE_NAME)
        response.delete_cookie(
            auth_settings.JWT_REFRESH_COOKIE_NAME,
            path="/api/auth/refresh/",
        )
