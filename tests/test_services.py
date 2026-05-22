"""Tests for services (without Redis — unit tests only)."""

from django.test import TestCase

from auth_system.services.totp_service import TOTPService


class TOTPServiceTest(TestCase):
    def test_generate_secret_length(self):
        secret = TOTPService.generate_secret()
        self.assertTrue(len(secret) > 10)

    def test_generate_and_verify_code(self):
        secret = TOTPService.generate_secret()
        totp = __import__("pyotp").TOTP(secret)
        code = totp.now()
        self.assertTrue(TOTPService.verify_code(secret, code))

    def test_verify_invalid_code(self):
        secret = TOTPService.generate_secret()
        self.assertFalse(TOTPService.verify_code(secret, "000000"))

    def test_generate_backup_codes_count(self):
        codes = TOTPService.generate_backup_codes()
        self.assertEqual(len(codes), 10)

    def test_consume_backup_code_valid(self):
        codes = ["CODE1", "CODE2", "CODE3"]
        is_valid, updated = TOTPService.consume_backup_code(codes, "code1")
        self.assertTrue(is_valid)
        self.assertNotIn("CODE1", updated)
        self.assertEqual(len(updated), 2)

    def test_consume_backup_code_invalid(self):
        codes = ["CODE1", "CODE2"]
        is_valid, updated = TOTPService.consume_backup_code(codes, "WRONG")
        self.assertFalse(is_valid)
        self.assertEqual(len(updated), 2)
