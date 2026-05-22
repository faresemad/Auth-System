from rest_framework.throttling import AnonRateThrottle

from .conf import LOGIN_THROTTLE_RATES


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"

    def allow_request(self, request, view):
        rate = LOGIN_THROTTLE_RATES.get(self.scope)
        if rate is None:
            return True
        self.rate = rate
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)


class SignupRateThrottle(AnonRateThrottle):
    scope = "signup"

    def allow_request(self, request, view):
        rate = LOGIN_THROTTLE_RATES.get(self.scope)
        if rate is None:
            return True
        self.rate = rate
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = "password_reset"

    def allow_request(self, request, view):
        rate = LOGIN_THROTTLE_RATES.get(self.scope)
        if rate is None:
            return True
        self.rate = rate
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)


class Verify2FARateThrottle(AnonRateThrottle):
    scope = "verify_2fa"

    def allow_request(self, request, view):
        rate = LOGIN_THROTTLE_RATES.get(self.scope)
        if rate is None:
            return True
        self.rate = rate
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)
