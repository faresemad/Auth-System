from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
