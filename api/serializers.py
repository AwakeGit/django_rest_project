from django.contrib.auth.models import User
from rest_framework import serializers
from api.services import create_user


class UserRegistrationSerializer(serializers.Serializer):
    """Сериализатор для регистрации пользователя."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate_username(self, value: str) -> str:
        """
        Проверяет, что имя пользователя уникально.

        :param value: Введённое имя пользователя.
        :return: Имя пользователя, если проверка прошла успешно.
        :raises serializers.ValidationError: Если пользователь с таким именем уже существует.
        """

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    def create(self, validated_data: dict) -> User:
        """
        Создаёт нового пользователя на основе проверенных данных.

        :param validated_data: Проверенные данные пользователя.
        :return: Созданный объект пользователя.
        """
        return create_user(
            username=validated_data["username"], password=validated_data["password"]
        )
