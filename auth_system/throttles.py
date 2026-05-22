from rest_framework.throttling import AnonRateThrottle

from .conf import LOGIN_THROTTLE_RATES


class _BaseCustomThrottle(AnonRateThrottle):
    def get_rate(self):
        return None

    def allow_request(self, request, view):
        rate = LOGIN_THROTTLE_RATES.get(self.scope)
        if rate is None:
            return True
        self.rate = rate
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)


class LoginRateThrottle(_BaseCustomThrottle):
    scope = "login"


class SignupRateThrottle(_BaseCustomThrottle):
    scope = "signup"


class PasswordResetRateThrottle(_BaseCustomThrottle):
    scope = "password_reset"


class Verify2FARateThrottle(_BaseCustomThrottle):
    scope = "verify_2fa"
