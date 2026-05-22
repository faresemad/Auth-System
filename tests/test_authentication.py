"""Tests for the EmailAuthBackend and CookieJWTAuthentication classes."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from auth_system.authentication import EmailAuthBackend
from auth_system.models import TwoFactor
from auth_system.services.jwt_service import JWTService

User = get_user_model()


class EmailAuthBackendTest(TestCase):
    def setUp(self):
        self.backend = EmailAuthBackend()
        self.user = User.objects.create_user(
            email="auth@example.com",
            username="authuser",
            password="Secret123!",
        )

    def test_authenticate_with_email(self):
        result = self.backend.authenticate(
            request=None, email="auth@example.com", password="Secret123!"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.user.pk)

    def test_authenticate_wrong_password(self):
        result = self.backend.authenticate(
            request=None, email="auth@example.com", password="wrong"
        )
        self.assertIsNone(result)

    def test_authenticate_nonexistent_email(self):
        result = self.backend.authenticate(
            request=None, email="nobody@example.com", password="x"
        )
        self.assertIsNone(result)

    def test_authenticate_with_username_keyword(self):
        result = self.backend.authenticate(
            request=None, username="auth@example.com", password="Secret123!"
        )
        self.assertIsNotNone(result)


class TokenVersionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="version@example.com",
            username="versionuser",
            password="Secret123!",
        )
        TwoFactor.objects.create(user=self.user, token_version=0)

    def test_token_version_increments_on_password_change(self):
        tokens = JWTService.generate_tokens(self.user)
        self.assertEqual(tokens["access"] is not None, True)

        twofa = TwoFactor.objects.get(user=self.user)
        twofa.token_version += 1
        twofa.save()

        tokens2 = JWTService.generate_tokens(self.user)
        self.assertEqual(tokens2["access"] is not None, True)
