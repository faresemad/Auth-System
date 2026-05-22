from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class EmailService:
    @staticmethod
    def send_verification_email(user, request=None):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # In a real app, this would be a frontend URL
        # For now, we'll assume a placeholder or a reverse lookup if it was a Django template view
        # But since it's an API, the frontend should handle the token and send it to our verify endpoint
        verification_link = (
            f"{settings.FRONTEND_URL}/verify-account?uid={uid}&token={token}"
        )

        subject = "Verify your account"
        message = (
            f"Please click the link below to verify your account:\n{verification_link}"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_password_reset_email(user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_link = (
            f"{settings.FRONTEND_URL}/password-reset-confirm?uid={uid}&token={token}"
        )

        subject = "Password Reset Request"
        message = f"Please click the link below to reset your password:\n{reset_link}"

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_email_change_verification(user, new_email):
        # We can use the same token generator or a custom one
        # For email change, we might want to store the pending email in Redis or a model
        # Let's use a simple approach for now or just a token that encodes the new email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # We need to pass the new email too, maybe as a query param or encoded in token
        # To keep it simple, let's just use the token and assume the verify endpoint
        # knows which email to change to (e.g. from a session or another Redis key)
        verification_link = f"{settings.FRONTEND_URL}/verify-email-change?uid={uid}&token={token}&new_email={new_email}"

        subject = "Verify your new email address"
        message = f"Please click the link below to verify your new email address:\n{verification_link}"

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [new_email],
            fail_silently=False,
        )
