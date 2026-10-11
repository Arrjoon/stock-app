"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.jwt import RoleTokenObtainPairView
from apps.accounts.views import MeView
from apps.companies.views import CompareView


@extend_schema(
    operation_id="health",
    tags=["Health"],
    summary="Liveness",
    auth=[],
    responses={
        200: inline_serializer(
            name="HealthResponse",
            fields={
                "status": serializers.CharField(),
                "service": serializers.CharField(),
            },
        )
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(_request):
    """Liveness probe for Docker and load balancers."""
    return Response({"status": "ok", "service": "stock-app"})


urlpatterns = [
    path("api/health/", health_check, name="health-check"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("admin/", admin.site.urls),
    path("api/auth/login/", RoleTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/admin/", include("apps.crawling.api_urls")),
    path("api/admin/users/", include("apps.accounts.urls")),
    path("api/companies/", include("apps.companies.urls")),
    path("api/news/", include("apps.news.urls")),
    path("api/compare/", CompareView.as_view(), name="compare"),
]
