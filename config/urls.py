# congif/urls.py
from django.contrib import admin
from django.urls import path, include


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path("admin/", admin.site.urls),
    path('sentry-debug/', trigger_error),
    path("api/", include("api.urls")),

]
