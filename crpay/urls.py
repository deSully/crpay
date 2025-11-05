from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from entity.views.login import EntityLoginView
from entity.views.token_refresh import TokenRefreshView

# Définition du schéma pour la documentation Swagger (PUBLIC - sans authentification)
schema_view = get_schema_view(
    openapi.Info(
        title="CRPAY Payment Gateway API",
        default_version="v0",
        description="""
# 🚀 Bienvenue sur l'API CRPAY

API de paiement permettant d'initier et suivre des transactions de paiement mobile.

## 🔐 Authentification

L'API utilise **JWT (JSON Web Tokens)** pour l'authentification :

1. **Obtenir un token** : `POST /api/v0/auth/login/`
2. **Rafraîchir le token** : `POST /api/v0/auth/refresh/`
3. **Utiliser le token** : Ajouter `Authorization: Bearer <access_token>` dans les headers

## 📱 Flux de paiement

1. Authentifiez-vous avec vos identifiants
2. Créez une transaction : `POST /api/v0/payments/`
3. Consultez le statut : `GET /api/v0/payments/{uuid}/`
4. Recevez les callbacks sur votre webhook configuré

## 🌍 Environnements

- **Production** : `https://api.crpay.com` (à venir)
- **Sandbox** : `https://sandbox.crpay.com` (à venir)

## 📞 Support

Pour toute question, contactez-nous : support@crdigital.tech
        """,
        terms_of_service="https://crdigital.tech/terms/",
        contact=openapi.Contact(
            name="CRPAY Support",
            email="support@crdigital.tech",
            url="https://crdigital.tech"
        ),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # API v0 - Authentication
    path("api/v0/auth/login/", EntityLoginView.as_view(), name="api-login"),
    path("api/v0/auth/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    
    # API v0 - Resources  
    path("api/v0/payments/", include("transaction.urls")),
    
    # Application web (avec son propre login HTML)
    path("app/", include("app.urls")),
    
    # Documentation Swagger
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT[0])
