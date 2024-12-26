import logging
import os

import httpx
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken
from drfasyncview import AsyncAPIView
from api.decorators import token_required
from api.serializers import UserRegistrationSerializer
from django.core.cache import cache

from config import settings

logger = logging.getLogger("users")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")


class RegisterView(generics.CreateAPIView):
    """
    Оставляем регистрацию как есть: синхронная вьюха.
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Получаем пользователя по username
        user = User.objects.get(username=response.data["username"])

        # Генерируем токены
        refresh = RefreshToken.for_user(user)
        token_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        # Объединяем данные ответа сериализатора с токенами
        return Response({**response.data, **token_data}, status=status.HTTP_201_CREATED)


class CacheTestView(APIView):
    def get(self, request, key):
        """
        Получение данных из кэша по ключу.
        """
        data = cache.get(key)
        if data is None:
            return Response({"message": "Ключ не найден в кэше"}, status=404)
        return Response({"key": key, "value": data}, status=200)


@method_decorator(csrf_exempt, name="dispatch")
class UploadDocumentView(AsyncAPIView):
    """
    Асинхронное представление для загрузки документа в FastAPI.
    Используем drfasyncview.AsyncAPIView вместо стандартного APIView.
    """

    @token_required
    async def post(self, request, *args, **kwargs):
        logger.info("Получен запрос на загрузку файла (async).")
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Принят файл: {file_obj.name}, размер: {file_obj.size}")
        upload_url = f"{FASTAPI_URL}documents"
        logger.info(f"Отправка файла в FastAPI: {upload_url}")

        content = file_obj.read()
        file_obj.seek(0)

        async with httpx.AsyncClient() as client:
            logger.info("TEST")
            response = await client.post(
                upload_url,
                files={"file": (file_obj.name, content)},
            )

        logger.info(
            f"Ответ от FastAPI: статус={response.status_code}, тело={response.text}"
        )

        if response.status_code in [200, 201]:
            data = response.json()
            doc_id = data.get("id")
            if not doc_id:
                return Response(
                    {"message": "No id returned from FastAPI."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {"id": doc_id, "message": "File uploaded successfully."},
                status=status.HTTP_201_CREATED,
            )
        else:
            error_message = response.json().get("message", "Unknown error.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )


@method_decorator(csrf_exempt, name="dispatch")
class AnalyzeDocumentView(AsyncAPIView):
    """
    Асинхронное представление для анализа документа.
    """

    @token_required
    async def post(self, request, doc_id, *args, **kwargs):
        if not doc_id:
            return Response(
                {"message": "doc_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        analyze_url = f"{FASTAPI_URL}documents/{doc_id}/analyze"
        logger.info(f"Отправка запроса на анализ {doc_id} в FastAPI: {analyze_url}")

        async with httpx.AsyncClient() as client:
            response = await client.post(analyze_url)

        logger.info(
            f"Ответ от FastAPI на анализ: статус={response.status_code}, тело={response.text}"
        )

        if response.status_code in [200, 201]:
            return Response(
                {"message": "Документ успешно отправлен на анализ."},
                status=status.HTTP_200_OK,
            )
        else:
            error_message = response.json().get("message", "Unknown error.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )


@method_decorator(csrf_exempt, name="dispatch")
class GetTextView(AsyncAPIView):
    """
    Асинхронное представление для получения текста документа.
    """

    @token_required
    async def get(self, request, doc_id, *args, **kwargs):
        text_url = f"{FASTAPI_URL}documents/{doc_id}/text"
        logger.info(f"Запрос на получение текста {doc_id} в FastAPI: {text_url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(text_url)

        logger.info(
            f"Ответ от FastAPI: статус={response.status_code}, тело={response.text}"
        )

        if response.status_code in [200, 201]:
            data = response.json()
            text = data.get("text", "Текст недоступен.")
            return Response(
                {"text": text, "message": "Текст успешно получен."},
                status=status.HTTP_200_OK,
            )
        else:
            error_message = response.json().get("message", "Unknown error.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )


@method_decorator(csrf_exempt, name="dispatch")
class DeleteDocumentView(AsyncAPIView):
    """
    Асинхронное представление для удаления документа.
    """

    @token_required
    async def delete(self, request, doc_id, *args, **kwargs):
        if not doc_id:
            return Response(
                {"message": "doc_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        delete_url = f"{FASTAPI_URL}documents/{doc_id}"
        logger.info(f"Запрос на удаление doc_id={doc_id} в FastAPI: {delete_url}")

        async with httpx.AsyncClient() as client:
            response = await client.delete(delete_url)

        logger.info(
            f"Ответ от FastAPI на удаление: статус={response.status_code}, тело={response.text}"
        )

        if response.status_code in [200, 204]:
            return Response(
                {"message": "Документ успешно удален."}, status=status.HTTP_200_OK
            )
        else:
            error_message = response.json().get("message", "Unknown error.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )
