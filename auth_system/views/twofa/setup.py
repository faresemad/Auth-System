from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...authentication import CookieJWTAuthentication
from ...exceptions import TwoFAAlreadyEnabled
from ...services import TOTPService
from ...utils import get_or_create_2fa


@extend_schema(tags=["2fa"], request=None)
class Setup2FAView(APIView):
    """
    POST /api/auth/2fa/setup/

    Generates a TOTP secret and provisioning QR code without activating 2FA.
    The client must save the secret in their authenticator app then call
    /api/auth/2fa/enable/ with a valid TOTP code to complete setup.
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    template_name = "authentication/setup_2fa.html"
    serializer_class = None

    # change this to False if you want JSON only
    render_template = False

    def post(self, request):
        user = request.user

        twofa = get_or_create_2fa(user)

        if twofa.is_2fa_enabled:
            raise TwoFAAlreadyEnabled()

        secret = TOTPService.generate_secret()

        twofa.totp_secret = secret
        twofa.save(update_fields=["totp_secret"])

        data = {
            "secret": secret,
            "qr_code": TOTPService.generate_qr_code_base64(user.email, secret),
            "otpauth_uri": TOTPService.get_provisioning_uri(user.email, secret),
        }

        if self.render_template:
            return render(
                request,
                self.template_name,
                data,
            )

        return Response(
            data,
            status=status.HTTP_200_OK,
        )
