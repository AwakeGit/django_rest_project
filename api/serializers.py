from django.contrib.auth.models import User
from rest_framework import serializers
from api.services import create_user


class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User already exists.")
        return value

    def create(self, validated_data):
        return create_user(
            username=validated_data["username"], password=validated_data["password"]
        )
