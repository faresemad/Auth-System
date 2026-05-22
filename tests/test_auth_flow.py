"""End-to-end tests for the core authentication flow."""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class SignupLoginFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse("auth_system:signup")
        self.login_url = reverse("auth_system:login")
        self.verify_url = reverse("auth_system:verify-account")
        self.refresh_url = reverse("auth_system:token-refresh")
        self.logout_url = reverse("auth_system:logout")

        self.user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Str0ng!Pass123",
            "confirm_password": "Str0ng!Pass123",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_full_signup_login_refresh_logout_flow(self):
        # ── Signup ──────────────────────────────────────────────
        resp = self.client.post(self.signup_url, self.user_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("User created successfully", resp.data["detail"])

        user = User.objects.get(email=self.user_data["email"])
        self.assertFalse(user.is_active)
        self.assertFalse(getattr(user, "is_verified", False))

        # ── Verify email ─────────────────────────────────────────
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        resp = self.client.get(self.verify_url, {"uid": uid, "token": token})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("verified", resp.data["detail"])

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)

        # ── Login ────────────────────────────────────────────────
        resp = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password"]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.cookies)
        self.assertIn("refresh_token", resp.cookies)

        access_cookie = resp.cookies["access_token"]
        self.assertTrue(access_cookie.value.startswith("eyJ"))  # JWT header

        # ── Refresh ──────────────────────────────────────────────
        self.client.cookies.clear()
        # Manually set the refresh cookie for the refresh request
        self.client.cookies["refresh_token"] = resp.cookies["refresh_token"]
        resp = self.client.post(self.refresh_url, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", resp.cookies)

        # ── Logout ───────────────────────────────────────────────
        self.client.cookies.clear()
        self.client.cookies["access_token"] = resp.cookies["access_token"]
        self.client.cookies["refresh_token"] = resp.cookies["refresh_token"]
        resp = self.client.post(self.logout_url, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("Logged out", resp.data["detail"])

    def test_signup_passwords_mismatch(self):
        data = {**self.user_data, "confirm_password": "different"}
        resp = self.client.post(self.signup_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_credentials(self):
        resp = self.client.post(
            self.login_url,
            {"email": "none@x.com", "password": "wrong"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_invalid_token(self):
        resp = self.client.get(
            self.verify_url, {"uid": "invalid", "token": "bad-token"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_request(self):
        user = User.objects.create_user(
            email="reset@example.com",
            username="resetuser",
            password="OldPass123!",
        )
        resp = self.client.post(
            reverse("auth_system:password-reset-request"),
            {"email": user.email},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_flow(self):
        user = User.objects.create_user(
            email="reset2@example.com",
            username="resetuser2",
            password="OldPass123!",
        )
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        resp = self.client.post(
            reverse("auth_system:password-reset-confirm"),
            {
                "uid": uid,
                "token": token,
                "password": "NewStr0ng!Pass",
                "confirm_password": "NewStr0ng!Pass",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStr0ng!Pass"))
