from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView


class TokenRefreshView(BaseTokenRefreshView):
    """
    Vue personnalisée pour documenter le refresh token dans Swagger
    """
    
    @swagger_auto_schema(
        operation_summary="Rafraîchir le token d'accès",
        operation_description="""
Permet de rafraîchir un token d'accès expiré en utilisant le refresh token.

**Important :**
- Le refresh token a une durée de validité de 1 jour
- L'access token a une durée de validité de 15 minutes
- Après utilisation, l'ancien refresh token est blacklisté (sécurité)

**Utilisation :**
1. Envoyez votre refresh token obtenu lors du login
2. Recevez un nouveau access token
3. Utilisez ce nouveau token dans vos requêtes
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Le refresh token obtenu lors du login"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Token rafraîchi avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Nouveau token d'accès"
                        ),
                    },
                ),
            ),
            401: "Token invalide ou expiré",
        },
        tags=["🔐 Authentification"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
