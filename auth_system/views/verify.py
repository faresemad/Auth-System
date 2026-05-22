from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..exceptions import EmailAlreadyVerified

User = get_user_model()


@extend_schema(tags=["auth"], request=None)
class VerifyAccountView(APIView):
    permission_classes = [AllowAny]
    serializer_class = None

    def get(self, request, *args, **kwargs):
        uidb64 = request.query_params.get("uid")
        token = request.query_params.get("token")

        if not uidb64 or not token:
            return Response(
                {"error": "Missing uid or token."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            if user.is_active:
                raise EmailAlreadyVerified()
            user.is_active = True
            user.save(update_fields=["is_active"])
            return Response(
                {"detail": "Account verified successfully."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST
            )
