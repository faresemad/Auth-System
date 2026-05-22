from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...authentication import CookieJWTAuthentication
from ...exceptions import InvalidCredentials, InvalidTOTPCode, TwoFANotEnabled
from ...serializers import Disable2FASerializer
from ...services import TOTPService
from ...utils import get_or_create_2fa


@extend_schema(tags=["2fa"])
class Disable2FAView(APIView):
    """
    POST /api/auth/2fa/disable/

    Disables 2FA after verifying both the current password and a live TOTP
    code. This dual check prevents an attacker who hijacks the session from
    silently disabling 2FA.
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = Disable2FASerializer

    def post(self, request):
        user = request.user

        twofa = get_or_create_2fa(user)

        if not twofa.is_2fa_enabled:
            raise TwoFANotEnabled()

        serializer = Disable2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not user.check_password(serializer.validated_data["password"]):
            raise InvalidCredentials()

        if not TOTPService.verify_code(
            twofa.totp_secret, serializer.validated_data["code"]
        ):
            raise InvalidTOTPCode()

        twofa.is_2fa_enabled = False
        twofa.totp_secret = ""
        twofa.backup_codes = []
        twofa.save(update_fields=["is_2fa_enabled", "totp_secret", "backup_codes"])

        return Response(
            {"detail": "Two-factor authentication disabled."},
            status=status.HTTP_200_OK,
        )
