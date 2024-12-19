from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
import logging

logger = logging.getLogger("api")


class CreateTokenView(APIView):
    """
    Создает токен для пользователя. Если пользователь не существует, он будет создан.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            logger.warning("Не указаны имя пользователя или пароль.")
            return Response(
                {"detail": "Username and password are required."}, status=400
            )

        try:
            user = User.objects.filter(username=username).first()

            if not user:
                with transaction.atomic():
                    hashed_password = make_password(password)
                    user = User.objects.create(
                        username=username, password=hashed_password
                    )
                logger.info(f"Создан новый пользователь: {username}")

            elif not check_password(password, user.password):
                return Response({"detail": "Invalid credentials."}, status=401)

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            )

        except Exception as e:
            logger.error(f"Ошибка при создании токена: {e}")
            return Response({"detail": "Internal server error."}, status=500)
