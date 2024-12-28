# api/decorators.py
import jwt
import logging
from functools import wraps

from django.conf import settings
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def token_required(func):
    """
    Декоратор, который проверяет наличие и валидность JWT-токена
    в заголовке Authorization (формат 'Bearer <token>').

    :param func: Основная функция, которую нужно выполнить после проверки токена.
    :return: Ответ 401, если токен не предоставлен или невалиден. Иначе вызов функции.
    """

    @wraps(func)
    async def wrapped(self, request, *args, **kwargs):
        """
        Обёртка, проверяющая JWT-токен в запросе.

        :param self: Ссылка на объект класса.
        :param request: HTTP-запрос.
        :param args: Позиционные аргументы.
        :param kwargs: Именованные аргументы.
        :return: Ответ с ошибкой (401) или вызов функции.
        """

        # Проверяем наличие и валидность токена
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            logger.warning("Токен не предоставлен в заголовке.")
            return Response({"error": "Токен не предоставлен."}, status=401)

        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            logger.warning("Токен отсутствует в заголовке Authorization.")
            return Response({"error": "Токен не предоставлен."}, status=401)

        try:
            # Проверяем/декодируем токен БЕЗ обращения к БД
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            logger.info(f"JWT-пейлоад: {payload}")
        except jwt.ExpiredSignatureError:
            logger.error("Срок действия токена истёк.")
            return Response({"error": "Срок действия токена истёк."}, status=401)
        except jwt.InvalidTokenError:
            logger.error("Невалидный токен.")
            return Response({"error": "Невалидный токен."}, status=401)

        # Если токен валиден, передаём управление в основную функцию
        return await func(self, request, *args, **kwargs)

    return wrapped
