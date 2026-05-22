from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..exceptions import AccountDisabled, InvalidCredentials
from ..serializers import LoginSerializer
from ..services import CookieService, JWTService, PendingSessionService
from ..throttles import LoginRateThrottle
from ..utils import get_or_create_2fa


@extend_schema(tags=["auth"], request=LoginSerializer)
class LoginView(APIView):
    """
    POST /api/auth/login/

    Accepts email + password. Returns JWT cookies directly if 2FA is disabled,
    or a short-lived session_token when 2FA is required (pass that token to
    /api/auth/2fa/verify-login/).
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            raise InvalidCredentials()

        if not user.is_active:
            raise AccountDisabled()

        twofa = get_or_create_2fa(user)

        if getattr(twofa, "is_2fa_enabled", False):
            session_token = PendingSessionService().create_session(user.pk)
            return Response(
                {"requires_2fa": True, "session_token": session_token},
                status=status.HTTP_200_OK,
            )

        tokens = JWTService.generate_tokens(user)
        response = Response({"detail": "Login successful."}, status=status.HTTP_200_OK)
        CookieService.set_auth_cookies(response, tokens["access"], tokens["refresh"])
        return response
