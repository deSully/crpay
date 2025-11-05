from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from entity.views.login import EntityLoginView
from entity.views.token_refresh import TokenRefreshView
from entity.views.register import RegisterView
from entity.views.logout import admin_logout_view

# Définition du schéma pour la documentation Swagger (PUBLIC - sans authentification)
schema_view = get_schema_view(
    openapi.Info(
        title="CRPAY Payment Gateway API",
        default_version="v0",
        description="""
# 🚀 Bienvenue sur l'API CRPAY

API de paiement permettant d'initier et suivre des transactions de paiement mobile.

## � Démarrage rapide

### 1️⃣ Créer votre compte (Self-service)
**Nouveau partenaire ?** Inscrivez-vous directement depuis le Swagger :
- `POST /api/v0/auth/register/` - Créez votre compte en 30 secondes
- Vous recevrez immédiatement vos tokens JWT

### 2️⃣ Authentification
L'API utilise **JWT (JSON Web Tokens)** pour l'authentification :
- **S'inscrire** : `POST /api/v0/auth/register/` (nouveau partenaire)
- **Se connecter** : `POST /api/v0/auth/login/` (partenaire existant)
- **Rafraîchir le token** : `POST /api/v0/auth/refresh/`
- **Utiliser le token** : 
  1. Cliquez sur 🔒 **Authorize** en haut à droite
  2. Entrez : `Bearer votre_access_token_ici` (avec le mot "Bearer" et un espace)
  3. Cliquez sur **Authorize** puis **Close**

### 3️⃣ Effectuer un paiement
1. Créez une transaction : `POST /api/v0/payments/`
2. Consultez le statut : `GET /api/v0/payments/{uuid}/`
3. Recevez les callbacks sur votre webhook (optionnel)

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
    path("admin/logout/", admin_logout_view, name="admin-logout"),  # Custom logout avant admin/ pour override
    path("admin/", admin.site.urls),
    
    # API v0 - Authentication
    path("api/v0/auth/register/", RegisterView.as_view(), name="api-register"),
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
