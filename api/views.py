import logging
import os

import httpx
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from drfasyncview import AsyncAPIView
from api.decorators import token_required
from api.serializers import UserRegistrationSerializer

# Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# URL FastAPI
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")


class RegisterView(generics.CreateAPIView):
    """
    Представление для регистрации пользователя.
    CreateAPIView для создания нового пользователя и генерации токенов.
    """

    # Права доступа
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs) -> Response:
        """
        Метод для обработки запроса на регистрацию.

        Генерирует access и refresh

        :param request: HTTP запрос, содержащий данные регистрации.
        :return: HTTP ответ с данными пользователя и токенами.
        """
        logger.info("Получен запрос на регистрацию.")

        # Создание пользователя
        response = super().create(request, *args, **kwargs)

        logger.info(f"Пользователь {response.data['username']} зарегистрирован.")
        # Получение пользователя
        user = User.objects.get(username=response.data["username"])

        # Генерация токенов
        refresh = RefreshToken.for_user(user)
        logger.info("Токены успешно сгенерированы.")
        token_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        logger.info(f"Токены успешно добавлены в ответ. {token_data}")
        # Добавление токенов в ответ
        return Response({**response.data, **token_data}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class UploadDocumentView(AsyncAPIView):
    """
    Представление для загрузки документа.
    """

    @token_required
    async def post(self, request, *args, **kwargs) -> Response:
        """
        Загрузка документа.

        :param request: HTTP запрос с загружаемым файлом.
        :return: HTTP ответ с результатом загрузки.
        """
        logger.info("Получен запрос на загрузку файла (async).")
        # Получение файла
        file_obj = request.FILES.get("file")

        # Проверка, что файл был загружен
        if not file_obj:
            return Response(
                {"message": "Файл не загружен."}, status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Принят файл: {file_obj.name}, размер: {file_obj.size}")
        # Ссылка на загрузку
        upload_url = f"{FASTAPI_URL}documents"
        logger.info(f"Отправка файла в FastAPI: {upload_url}")

        # Чтение содержимого файла
        content = file_obj.read()
        file_obj.seek(0)

        # Отправка запроса
        async with httpx.AsyncClient() as client:
            logger.info("TEST")
            response = await client.post(
                upload_url,
                files={"file": (file_obj.name, content)},
            )

        logger.info(
            f"Ответ от FastAPI: статус={response.status_code}, тело={response.text}"
        )

        # Обработка ответа
        if response.status_code in [200, 201]:
            data = response.json()
            doc_id = data.get("id")
            # Проверка, что id был получен
            if not doc_id:
                return Response(
                    {"message": "ID документа не получен."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {"id": doc_id, "message": "Документ успешно загружен."},
                status=status.HTTP_201_CREATED,
            )
        else:
            error_message = response.json().get("message", "Ошибка загрузки.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )


@method_decorator(csrf_exempt, name="dispatch")
class AnalyzeDocumentView(AsyncAPIView):
    """
    Представление для анализа документа.
    """

    @token_required
    async def post(self, request, doc_id: int, *args, **kwargs) -> Response:
        """
        Анализ документа.

        :param request: HTTP запрос.
        :param doc_id: ID документа.
        :return: HTTP ответ с результатом анализа.
        """

        # Проверка, что ID документа был получен
        if not doc_id:
            return Response(
                {"message": "ID документа не получен."}, status=status.HTTP_400_BAD_REQUEST
            )

        analyze_url = f"{FASTAPI_URL}documents/{doc_id}/analyze"
        logger.info(f"Отправка запроса на анализ {doc_id} в FastAPI: {analyze_url}")

        # Отправка запроса
        async with httpx.AsyncClient() as client:
            response = await client.post(analyze_url)

        logger.info(
            f"Ответ от FastAPI на анализ: статус={response.status_code}, тело={response.text}"
        )

        # Обработка ответа
        if response.status_code in [200, 201]:
            return Response(
                {"message": "Документ успешно отправлен на анализ."},
                status=status.HTTP_200_OK,
            )
        else:
            error_message = response.json().get("message", "Ошибка анализа.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )


@method_decorator(csrf_exempt, name="dispatch")
class GetTextView(AsyncAPIView):
    """
    Представление для получения текста документа.
    """

    @token_required
    async def get(self, request, doc_id: int, *args, **kwargs) -> Response:
        """
        Получение текста документа.

        :param request: HTTP запрос.
        :param doc_id: ID документа.
        :return: HTTP ответ с текстом документа.
        """

        text_url = f"{FASTAPI_URL}documents/{doc_id}/text"
        logger.info(f"Запрос на получение текста {doc_id} в FastAPI: {text_url}")

        # Отправка запроса
        async with httpx.AsyncClient() as client:
            response = await client.get(text_url)

        logger.info(
            f"Ответ от FastAPI: статус={response.status_code}, тело={response.text}"
        )

        # Обработка ответа
        if response.status_code in [200, 201]:
            data = response.json()
            text = data.get("text", "Текст недоступен.")
            return Response(
                {"text": text, "message": "Текст успешно получен."},
                status=status.HTTP_200_OK,
            )
        else:
            error_message = response.json().get("message", "Ошибка получения текста.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )


@method_decorator(csrf_exempt, name="dispatch")
class DeleteDocumentView(AsyncAPIView):
    """
    Представление для удаления документа.
    """

    @token_required
    async def delete(self, request, doc_id: int, *args, **kwargs) -> Response:
        """
        Удаление документа.

        :param request: HTTP запрос.
        :param doc_id: ID документа.
        :return: HTTP ответ с результатом удаления.
        """

        # Проверка, что ID документа был получен
        if not doc_id:
            return Response(
                {"message": "ID документа не получен."}, status=status.HTTP_400_BAD_REQUEST
            )

        delete_url = f"{FASTAPI_URL}documents/{doc_id}"
        logger.info(f"Запрос на удаление doc_id={doc_id} в FastAPI: {delete_url}")

        # Отправка запроса
        async with httpx.AsyncClient() as client:
            response = await client.delete(delete_url)

        logger.info(
            f"Ответ от FastAPI на удаление: статус={response.status_code}, тело={response.text}"
        )

        # Обработка ответа
        if response.status_code in [200, 204]:
            return Response(
                {"message": "Документ успешно удален."}, status=status.HTTP_200_OK
            )
        else:
            error_message = response.json().get("message", "Ошибка удаления.")
            return Response(
                {"message": f"Error from FastAPI: {error_message}"},
                status=response.status_code,
            )
