from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import transaction


def create_user(username: str, password: str) -> User:
    """
    Создаёт нового пользователя в транзакции.
    """
    with transaction.atomic():
        user = User.objects.create(username=username, password=make_password(password))
    return user
