import logging

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import transaction

logger = logging.getLogger(__name__)


def create_user(username: str, password: str) -> User:
    """
    Создаёт нового пользователя в транзакции.

    :param username: Имя пользователя для нового аккаунта.
    :param password: Пароль для нового пользователя (в незашифрованном виде).
    :return: Созданный объект пользователя.
    """
    try:
        with transaction.atomic():
            logger.info(f"Создание пользователя с именем '{username}'.")
            user = User.objects.create(
                username=username,
                password=make_password(password)
            )
            logger.info(f"Пользователь '{username}' успешно создан.")
        return user
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя '{username}': {e}")
        raise ValueError("Не удалось создать пользователя.")
