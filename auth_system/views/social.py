from urllib.parse import urlencode

from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from social_django.utils import psa

    # from social_django.views import _do_login
except ImportError:
    psa = None

from ..conf import auth_settings
from ..services import CookieService, JWTService, PendingSessionService
from ..utils import get_or_create_2fa


class SocialLoginURLView(APIView):
    """
    GET /api/auth/social/<provider>/login/
    Returns the URL where the frontend should redirect the user to start the OAuth flow.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, provider):
        if not psa:
            return Response(
                {"detail": "social-auth-app-django is not installed."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        from django.urls import reverse

        # Determine the begin URL from python-social-auth
        begin_url = request.build_absolute_uri(reverse("social:begin", args=[provider]))
        return Response({"url": begin_url})


@psa("social:complete")
def custom_social_complete(request, backend, *args, **kwargs):
    """
    Handles the callback from the identity provider.
    Authenticates the user and returns a redirect to the frontend with JWT cookies.
    """
    try:
        user = request.backend.complete(user=request.user, *args, **kwargs)
    except Exception as e:
        return HttpResponseRedirect(
            f"{auth_settings.SOCIAL_AUTH_ERROR_REDIRECT_URL}?error={str(e)}"
        )

    if not user:
        return HttpResponseRedirect(
            f"{auth_settings.SOCIAL_AUTH_ERROR_REDIRECT_URL}?error=AuthFailed"
        )

    if not user.is_active:
        return HttpResponseRedirect(
            f"{auth_settings.SOCIAL_AUTH_ERROR_REDIRECT_URL}?error=AccountDisabled"
        )

    # Handle 2FA handoff
    twofa = get_or_create_2fa(user)
    if getattr(twofa, "is_2fa_enabled", False):
        session_token = PendingSessionService().create_session(user.pk)
        query = urlencode({"requires_2fa": "true", "session_token": session_token})
        return HttpResponseRedirect(
            f"{auth_settings.SOCIAL_AUTH_SUCCESS_REDIRECT_URL}?{query}"
        )

    # No 2FA, issue tokens
    tokens = JWTService.generate_tokens(user)
    response = HttpResponseRedirect(auth_settings.SOCIAL_AUTH_SUCCESS_REDIRECT_URL)
    CookieService.set_auth_cookies(response, tokens["access"], tokens["refresh"])
    return response


class SocialCallbackView(APIView):
    """
    GET /api/auth/social/<provider>/complete/
    Receives the callback from the OAuth/SAML provider and processes it.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, provider, *args, **kwargs):
        if not psa:
            return Response(
                {"detail": "social-auth-app-django is not installed."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        return custom_social_complete(request, provider, *args, **kwargs)

    def post(self, request, provider, *args, **kwargs):
        # Some providers (like SAML/ADFS) use POST for the callback
        if not psa:
            return Response(
                {"detail": "social-auth-app-django is not installed."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        return custom_social_complete(request, provider, *args, **kwargs)
