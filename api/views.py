# api/views.py
import json
import logging
import os

import requests
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from api.serializers import UserRegistrationSerializer

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")

logger = logging.getLogger("api")


class RegisterView(generics.CreateAPIView):
    """
    Представление для регистрации нового пользователя.
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Получаем пользователя по username из ответа сериализатора
        user = User.objects.get(username=response.data["username"])

        # Генерируем токены
        refresh = RefreshToken.for_user(user)
        token_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        # Объединяем данные ответа сериализатора с токенами
        return Response({**response.data, **token_data}, status=status.HTTP_201_CREATED)


class UploadDocumentView(APIView):
    """
    Представление для загрузки документа.
    """

    permission_classes = [IsAuthenticated]  # Проверка JWT токена

    def post(self, request):
        logger.info("Получен запрос на загрузку файла в прокси.")
        file_obj = request.FILES.get("file")
        if not file_obj:
            logger.error("Файл не передан.")
            return Response(
                {"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Принят файл: {file_obj.name}, размер: {file_obj.size}")

        upload_url = f"{FASTAPI_URL}/documents"
        logger.info(f"Отправка файла в FastAPI: {upload_url}")

        response = requests.post(
            upload_url, files={"file": (file_obj.name, file_obj.read())}
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


class AnalyzeDocumentView(APIView):
    """
    Анализ документа:
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, doc_id):
        if not doc_id:
            return Response(
                {"message": "doc_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        analyze_url = f"{FASTAPI_URL}/documents/{doc_id}/analyze"
        logger.info(f"Отправка запроса на анализ {doc_id} в FastAPI: {analyze_url}")

        response = requests.post(analyze_url)
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


class GetTextView(APIView):
    """Получение текста документа:"""

    permission_classes = [IsAuthenticated]

    def get(self, request, doc_id):
        text_url = f"{FASTAPI_URL}/documents/{doc_id}/text/"
        logger.info(f"Запрос на получение текста {doc_id} в FastAPI: {text_url}")

        response = requests.get(text_url)
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


class DeleteDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, doc_id):
        if not doc_id:
            return Response(
                {"message": "doc_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        delete_url = f"{FASTAPI_URL}/documents/{doc_id}"
        logger.info(f"Запрос на удаление doc_id={doc_id} в FastAPI: {delete_url}")

        response = requests.delete(delete_url)
        logger.info(
            f"Ответ от FastAPI на удаление: статус={response.status_code}, тело={response.text}"
        )

        if response.status_code in [200, 204]:
            return Response(
                {"message": "Документ успешно удален."},
                status=status.HTTP_200_OK,
            )
        else:
            error_message = response.json().get("message", "Unknown error.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )
