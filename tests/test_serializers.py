"""Tests for serializers."""

from django.test import TestCase

from auth_system.serializers.password import ChangePasswordSerializer, PasswordResetConfirmSerializer
from auth_system.serializers.email import ChangeEmailSerializer


class PasswordSerializerTest(TestCase):
    def test_change_password_mismatch_raises_exception(self):
        serializer = ChangePasswordSerializer(data={
            "old_password": "old",
            "new_password": "NewPass123!",
            "confirm_password": "DifferentPass!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("Passwords do not match", str(serializer.errors))

    def test_password_reset_confirm_mismatch(self):
        serializer = PasswordResetConfirmSerializer(data={
            "password": "NewPass123!",
            "confirm_password": "DifferentPass!",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("Passwords do not match", str(serializer.errors))


class EmailSerializerTest(TestCase):
    def test_change_email_invalid(self):
        serializer = ChangeEmailSerializer(data={"new_email": "not-an-email"})
        self.assertFalse(serializer.is_valid())
