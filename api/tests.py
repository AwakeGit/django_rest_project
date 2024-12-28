from io import BytesIO

from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from django.urls import reverse
from rest_framework import status
import httpx
from unittest.mock import patch, MagicMock


# class RegisterViewTestCase(APITestCase):
#     def setUp(self):
#         self.register_url = reverse('register_user')
#         self.valid_user_data = {
#             "username": "testuser",
#             "password": "testpassword123",
#         }
#         self.invalid_user_data = {
#             "username": "",
#             "password": "short",
#         }
#
#     def test_register_user_success(self):
#         """
#         Проверяет успешную регистрацию пользователя.
#         """
#         response = self.client.post(self.register_url, self.valid_user_data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertIn("access", response.data)
#         self.assertIn("refresh", response.data)
#         self.assertTrue(User.objects.filter(username="testuser").exists())
#
#     def test_register_user_invalid_data(self):
#         """
#         Проверяет регистрацию с некорректными данными.
#         """
#         response = self.client.post(self.register_url, self.invalid_user_data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#     def test_register_existing_user(self):
#         """
#         Проверяет попытку регистрации уже существующего пользователя.
#         """
#         User.objects.create_user(**self.valid_user_data)
#         response = self.client.post(self.register_url, self.valid_user_data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DocumentViewTestCase(APITestCase):
    def setUp(self):
        # Регистрация пользователя и получение токена
        self.register_url = reverse('register_user')
        self.valid_user_data = {
            "username": "testuser",
            "password": "testpassword123",
        }
        response = self.client.post(self.register_url, self.valid_user_data)
        self.token = response.data["access"]  # Сохраняем access-токен

        # URL для тестирования GetTextView и DeleteDocumentView
        self.get_text_url = reverse("get_text", kwargs={"doc_id": 123})
        self.delete_document_url = reverse("delete_doc", kwargs={"doc_id": 123})
        self.analyze_document_url = reverse("analyze_doc", kwargs={"doc_id": 123})
        self.upload_document_url = reverse("upload_doc")

        self.valid_file_data = {
            "file": (
                "testfile.txt",
                BytesIO(b"fake file content"),
                "text/plain",
            )
        }

    @patch("httpx.AsyncClient.post")
    def test_upload_document_success(self, mock_post):
        """
        Проверяет успешную загрузку документа.
        """
        # Эмулируем успешный ответ FastAPI
        mock_post.return_value = httpx.Response(
            status_code=201,
            json={"id": 123, "message": "Документ успешно загружен."},
        )

        response = self.client.post(
            self.upload_document_url,
            self.valid_file_data,
            format="multipart",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["id"], 123)
        self.assertEqual(response.data["message"], "Документ успешно загружен.")

    @patch("httpx.AsyncClient.post")
    def test_upload_document_missing_file(self, mock_post):
        """
        Проверяет попытку загрузки без файла.
        """
        response = self.client.post(
            self.upload_document_url,
            {},
            format="multipart",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Файл не загружен.")

    @patch("httpx.AsyncClient.post")
    def test_upload_document_error_from_fastapi(self, mock_post):
        """
        Проверяет обработку ошибки от FastAPI при загрузке.
        """
        # Эмулируем ошибку FastAPI
        mock_post.return_value = httpx.Response(
            status_code=500,
            json={"message": "Ошибка на стороне FastAPI"},
        )

        response = self.client.post(
            self.upload_document_url,
            self.valid_file_data,
            format="multipart",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("message", response.data)
        self.assertIn("Ошибка на стороне FastAPI", response.data["message"])

    @patch("httpx.AsyncClient.get")
    def test_get_text_success(self, mock_get):
        """
        Проверяет успешное получение текста документа.
        """
        mock_get.return_value = httpx.Response(
            status_code=200,
            json={"text": "Это текст документа"},
        )

        response = self.client.get(
            self.get_text_url,
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text", response.data)
        self.assertEqual(response.data["text"], "Это текст документа")

    @patch("httpx.AsyncClient.get")
    def test_get_text_error(self, mock_get):
        """
        Проверяет обработку ошибки FastAPI.
        """
        mock_get.return_value = httpx.Response(
            status_code=500,
            json={"message": "Ошибка на стороне FastAPI"},
        )

        response = self.client.get(
            self.get_text_url,
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("message", response.data)
        self.assertIn("Ошибка на стороне FastAPI", response.data["message"])

    @patch("httpx.AsyncClient.delete")
    def test_delete_document_success(self, mock_delete):
        """
        Проверяет успешное удаление документа.
        """
        mock_delete.return_value = httpx.Response(
            status_code=200,
            json={"message": "Документ успешно удален."},
        )

        response = self.client.delete(
            self.delete_document_url,
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Документ успешно удален.")

    @patch("httpx.AsyncClient.delete")
    def test_delete_document_error(self, mock_delete):
        """
        Проверяет обработку ошибки FastAPI при удалении.
        """
        mock_delete.return_value = httpx.Response(
            status_code=500,
            json={"message": "Ошибка на стороне FastAPI"},
        )

        response = self.client.delete(
            self.delete_document_url,
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("message", response.data)
        self.assertIn("Ошибка на стороне FastAPI", response.data["message"])

    @patch("httpx.AsyncClient.post")
    def test_analyze_document_success(self, mock_post):
        """
        Проверяет успешную отправку документа на анализ.
        """
        mock_post.return_value = httpx.Response(
            status_code=200,
            json={"message": "Документ успешно отправлен на анализ."},
        )

        response = self.client.post(
            self.analyze_document_url,
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Документ успешно отправлен на анализ.")

    @patch("httpx.AsyncClient.post")
    def test_analyze_document_error(self, mock_post):
        """
        Проверяет обработку ошибки FastAPI при анализе.
        """
        mock_post.return_value = httpx.Response(
            status_code=500,
            json={"message": "Ошибка на стороне FastAPI"},
        )

        response = self.client.post(
            self.analyze_document_url,
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("message", response.data)
        self.assertIn("Ошибка на стороне FastAPI", response.data["message"])
