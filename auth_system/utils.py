from .models import TwoFactor


def get_or_create_2fa(user):
    twofa, _ = TwoFactor.objects.get_or_create(user=user)
    return twofa
