from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..authentication import CookieJWTAuthentication
from ..conf import auth_settings
from ..services import CookieService, JWTService


@extend_schema(tags=["auth"], request=None)
class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Blacklists the refresh token and clears both auth cookies. Requires a
    valid access token in the access_token cookie.
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request):
        refresh_token = request.COOKIES.get(auth_settings.JWT_REFRESH_COOKIE_NAME)
        if refresh_token:
            JWTService.blacklist_token(refresh_token)

        response = Response(
            {"detail": "Logged out successfully."}, status=status.HTTP_200_OK
        )
        CookieService.clear_auth_cookies(response)
        return response
