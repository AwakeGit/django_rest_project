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
    Если токен невалиден — возвращаем 401.
    Иначе пропускаем к основной логике.
    """

    @wraps(func)
    async def wrapped(self, request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response({"error": "Token not provided."}, status=401)

        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            return Response({"error": "Token not provided."}, status=401)

        try:
            # Проверяем/декодируем токен БЕЗ обращения к БД
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            # Если нужно: можно здесь вытащить user_id = payload["user_id"] и т.д.
            logger.info(f"JWT payload: {payload}")
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token has expired"}, status=401)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=401)

        # Если всё ок — передаём управление в основную функцию
        return await func(self, request, *args, **kwargs)

    return wrapped
