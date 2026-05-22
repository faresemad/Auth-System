from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...authentication import CookieJWTAuthentication
from ...exceptions import InvalidCredentials, TwoFANotEnabled
from ...serializers import BackupCodeSerializer
from ...services import TOTPService
from ...utils import get_or_create_2fa


@extend_schema_view(
    get=extend_schema(tags=["2fa"], summary="List backup codes", responses={200: None}),
    post=extend_schema(tags=["2fa"], summary="Regenerate backup codes", request=BackupCodeSerializer),
)
class BackupCodesView(APIView):
    """
    GET  /api/auth/2fa/backup-codes/         — list remaining codes
    POST /api/auth/2fa/backup-codes/         — regenerate (requires password)
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get(self, request):
        user = request.user

        twofa = get_or_create_2fa(user)

        if not twofa.is_2fa_enabled:
            raise TwoFANotEnabled()

        return Response(
            {
                "backup_codes": twofa.backup_codes,
                "count": len(twofa.backup_codes),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Regenerate all backup codes. Irreversibly invalidates the old ones."""
        user = request.user
        twofa = get_or_create_2fa(user)

        if not twofa.is_2fa_enabled:
            raise TwoFANotEnabled()

        serializer = BackupCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not user.check_password(serializer.validated_data["password"]):
            raise InvalidCredentials()

        new_codes = TOTPService.generate_backup_codes()
        twofa.backup_codes = new_codes
        twofa.save(update_fields=["backup_codes"])

        return Response(
            {"detail": "Backup codes regenerated.", "backup_codes": new_codes},
            status=status.HTTP_200_OK,
        )
