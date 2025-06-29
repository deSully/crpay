from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Définition du schéma pour la documentation Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="CRPAY API",
        default_version="v0",
        description="Documentation de l'API CRPAY",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="williams.stanley.desouza@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v0/entities/", include("entity.urls")),
    path("api/v0/payments/", include("transaction.urls")),
    path("app/", include("app.urls")),
    
    # Documentation Swagger
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(
        
        "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"
    ),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT[0])
