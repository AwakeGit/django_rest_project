from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import RegisterView


urlpatterns = [
    path("v1/auth/register/", RegisterView.as_view(), name="register_user"),
    path("v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]
