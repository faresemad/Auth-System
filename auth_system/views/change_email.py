from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..conf import auth_settings
from ..serializers.email import ChangeEmailSerializer
from ..services.email_service import EmailService
from ..services.redis_service import PendingEmailService
from ..utils import get_or_create_2fa

User = get_user_model()


@extend_schema(tags=["auth"], request=ChangeEmailSerializer)
class ChangeEmailRequestView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangeEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = ChangeEmailSerializer(data=request.data)
        if serializer.is_valid():
            new_email = serializer.validated_data["new_email"]
            PendingEmailService().store(request.user.pk, new_email)
            EmailService.send_email_change_verification(request.user, new_email)
            return Response(
                {"detail": "Verification email sent to the new address."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["auth"], request=None)
class ChangeEmailConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = None

    def get(self, request, *args, **kwargs):
        uidb64 = request.query_params.get("uid")
        token = request.query_params.get("token")

        if not uidb64 or not token:
            return Response(
                {"error": "Missing parameters."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            svc = PendingEmailService()
            new_email = svc.get(user.pk)
            if not new_email:
                return Response(
                    {"error": "Verification session expired. Please request again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.email = new_email
            user.save(update_fields=["email"])
            svc.delete(user.pk)
            twofa = get_or_create_2fa(user)
            twofa.token_version += 1
            twofa.save(update_fields=["token_version"])
            return Response(
                {"detail": "Email updated successfully."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST
            )
