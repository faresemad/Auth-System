from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..conf import auth_settings
from ..exceptions import InvalidRefreshToken
from ..services import JWTService


@extend_schema(tags=["auth"], request=None)
class TokenRefreshView(APIView):
    """
    POST /api/auth/refresh/

    Issues a new access token from the refresh token cookie. The refresh
    token itself is not rotated; only the access token cookie is updated.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = None

    def post(self, request):
        refresh_token = request.COOKIES.get(auth_settings.JWT_REFRESH_COOKIE_NAME)
        if not refresh_token:
            raise InvalidRefreshToken()

        new_access = JWTService.refresh_access_token(refresh_token)

        response = Response({"detail": "Token refreshed."}, status=status.HTTP_200_OK)
        response.set_cookie(
            auth_settings.JWT_ACCESS_COOKIE_NAME,
            new_access,
            max_age=int(auth_settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
            httponly=auth_settings.JWT_COOKIE_HTTPONLY,
            secure=auth_settings.JWT_COOKIE_SECURE,
            samesite=auth_settings.JWT_COOKIE_SAMESITE,
        )
        return response
