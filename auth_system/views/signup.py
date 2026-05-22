from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.signup import SignupSerializer
from ..services.email_service import EmailService
from ..throttles import SignupRateThrottle


@extend_schema(tags=["auth"], request=SignupSerializer)
class SignupView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer
    throttle_classes = [SignupRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            EmailService.send_verification_email(user, request)
            return Response(
                {
                    "detail": "User created successfully. Please check your email to verify your account."
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
