from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.password import (
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
)
from ..services.email_service import EmailService
from ..throttles import PasswordResetRateThrottle
from ..utils import get_or_create_2fa

User = get_user_model()


@extend_schema(tags=["auth"], request=PasswordResetSerializer)
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
                EmailService.send_password_reset_email(user)
            except User.DoesNotExist:
                pass
            return Response(
                {
                    "detail": "If an account with that email exists, we have sent a password reset link."
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["auth"], request=PasswordResetConfirmSerializer)
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if not uidb64 or not token:
            return Response(
                {"error": "Missing uid or token."}, status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.is_valid():
            try:
                uid = urlsafe_base64_decode(uidb64).decode()
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None

            if user is not None and default_token_generator.check_token(user, token):
                user.set_password(serializer.validated_data["password"])
                user.save()
                twofa = get_or_create_2fa(user)
                twofa.token_version += 1
                twofa.save(update_fields=["token_version"])
                return Response(
                    {"detail": "Password has been reset successfully."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Invalid or expired token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
