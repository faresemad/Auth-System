from django.contrib.auth import update_session_auth_hash
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..conf import auth_settings
from ..serializers.password import ChangePasswordSerializer
from ..utils import get_or_create_2fa


@extend_schema(tags=["auth"], request=ChangePasswordSerializer)
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"old_password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()

            if auth_settings.UPDATE_SESSION_AUTH_HASH:
                update_session_auth_hash(request, user)

            twofa = get_or_create_2fa(user)
            twofa.token_version += 1
            twofa.save(update_fields=["token_version"])

            return Response(
                {"detail": "Password updated successfully."}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
