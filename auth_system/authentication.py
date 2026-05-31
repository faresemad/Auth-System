from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError

from .conf import auth_settings
from .utils import get_or_create_2fa


class EmailAuthBackend(ModelBackend):
    """
    Authenticates against Django's user database using ``email`` as the
    username field.  This is the backend that ``LoginView`` relies on because
    it calls ``authenticate(request, email=…, password=…)``.

    Add to ``AUTHENTICATION_BACKENDS`` in your settings:

    .. code-block:: python

        AUTHENTICATION_BACKENDS = [
            "auth_system.authentication.EmailAuthBackend",
            "django.contrib.auth.backends.ModelBackend",
        ]
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None:
            email = kwargs.get("username")
        if email is None or password is None:
            return None
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(Q(email=email) | Q(username=email) | Q(pk=email))
        except UserModel.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


class CookieJWTAuthentication(JWTAuthentication):
    """
    Reads the JWT access token from an HttpOnly cookie instead of the
    Authorization header. Falls back gracefully (returns None) so views that
    allow unauthenticated access still work.

    Also validates the ``token_version`` claim against the stored version on
    ``TwoFactor`` — this invalidates all existing tokens when the user changes
    their password or email.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get(auth_settings.JWT_ACCESS_COOKIE_NAME)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError:
            return None

        user = self.get_user(validated_token)

        twofa = get_or_create_2fa(user)
        token_version = validated_token.get("token_version", 0)
        if token_version != twofa.token_version:
            return None

        return user, validated_token
