# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    RegisterView,
    UploadDocumentView,
    AnalyzeDocumentView,
    GetTextView,
    DeleteDocumentView,
)

urlpatterns = [
    path("v1/auth/register/", RegisterView.as_view(), name="register_user"),
    path("v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("v1/docs/", UploadDocumentView.as_view(), name="upload_doc"),
    path("v1/docs/<int:doc_id>/analyze/", AnalyzeDocumentView.as_view(), name="analyze_doc"),
    path("v1/docs/<int:doc_id>/text/", GetTextView.as_view(), name="get_text"),
    path("v1/docs/<int:doc_id>/", DeleteDocumentView.as_view(), name="delete_doc"),
]
