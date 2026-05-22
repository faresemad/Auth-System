from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ...exceptions import InvalidTOTPCode, PendingSessionExpired
from ...serializers import Verify2FALoginSerializer
from ...services import CookieService, JWTService, PendingSessionService, TOTPService
from ...throttles import Verify2FARateThrottle
from ...utils import get_or_create_2fa

User = get_user_model()


@extend_schema(tags=["2fa"])
class Verify2FALoginView(APIView):
    """
    POST /api/auth/2fa/verify-login/

    Second step of the 2FA login flow. Accepts the session_token issued by
    LoginView together with either a 6-digit TOTP code or an 8-char backup
    code.  On success the session is deleted from Redis and JWT cookies are set.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = Verify2FALoginSerializer
    throttle_classes = [Verify2FARateThrottle]

    def post(self, request):
        serializer = Verify2FALoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_token = str(serializer.validated_data["session_token"])
        code = serializer.validated_data["code"]

        session_svc = PendingSessionService()
        user_pk = session_svc.get_user_pk(session_token)
        if not user_pk:
            raise PendingSessionExpired()

        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            raise PendingSessionExpired()

        twofa = get_or_create_2fa(user)

        # --- TOTP path ---
        if TOTPService.verify_code(twofa.totp_secret, code):
            session_svc.delete_session(session_token)
            tokens = JWTService.generate_tokens(user)
            response = Response(
                {"detail": "Login successful."},
                status=status.HTTP_200_OK,
            )
            CookieService.set_auth_cookies(
                response, tokens["access"], tokens["refresh"]
            )
            return response

        # --- Backup code path ---
        is_valid, updated_codes = TOTPService.consume_backup_code(
            twofa.backup_codes, code
        )
        if is_valid:
            session_svc.delete_session(session_token)
            twofa.backup_codes = updated_codes
            twofa.save(update_fields=["backup_codes"])
            tokens = JWTService.generate_tokens(user)
            response = Response(
                {
                    "detail": "Login successful.",
                    "warning": "Backup code used.",
                    "backup_codes_remaining": len(updated_codes),
                },
                status=status.HTTP_200_OK,
            )
            CookieService.set_auth_cookies(
                response, tokens["access"], tokens["refresh"]
            )
            return response

        raise InvalidTOTPCode()
