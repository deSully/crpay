from django.contrib.auth import authenticate
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


class EntityLoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Authentification - Obtenir les tokens d'accès",
        operation_description="""
Authentifiez-vous avec vos identifiants pour obtenir les tokens JWT nécessaires aux appels API.

**Processus :**
1. Envoyez vos identifiants (username et password)
2. Recevez un **access token** (validité : 15 min) et un **refresh token** (validité : 1 jour)
3. Utilisez l'access token dans le header : `Authorization: Bearer <access_token>`

**Exemple de requête :**
```json
{
  "username": "votre_username",
  "password": "votre_password"
}
```

**Important :**
- Conservez le refresh token en sécurité pour renouveler l'access token
- L'access token doit être inclus dans toutes vos requêtes API
- Seules les entités de type CLIENT ou INTERNAL peuvent se connecter via l'API
""",
        tags=["🔐 Authentification"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username", "password"],
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Nom d'utilisateur"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Mot de passe"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Connexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                        "access": openapi.Schema(type=openapi.TYPE_STRING),
                        "entity": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "code": openapi.Schema(type=openapi.TYPE_STRING),
                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                "phone": openapi.Schema(type=openapi.TYPE_STRING),
                                "country": openapi.Schema(type=openapi.TYPE_STRING),
                                "entity_type": openapi.Schema(type=openapi.TYPE_STRING),
                                "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                "created_at": openapi.Schema(
                                    type=openapi.TYPE_STRING, format="date-time"
                                ),
                            },
                        ),
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "username": openapi.Schema(type=openapi.TYPE_STRING),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                                "date_joined": openapi.Schema(
                                    type=openapi.TYPE_STRING, format="date-time"
                                ),
                                "last_login": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    format="date-time",
                                    nullable=True,
                                ),
                            },
                        ),
                    },
                ),
            ),
            400: "Identifiants invalides ou compte inactif",
            403: "Entité non autorisée",
            404: "Entité liée non trouvée",
        },
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Le nom d'utilisateur et le mot de passe sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"error": "Identifiants invalides."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            return Response(
                {"error": "Le compte utilisateur est inactif."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entity = getattr(user, "entity", None)

        if entity is None:
            return Response(
                {"error": "Aucune entité liée à cet utilisateur."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if entity.entity_type not in ["CLIENT", "INTERNAL"]:
            return Response(
                {"error": "Cette entité n'est pas autorisée à se connecter via l'API."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not entity.is_active:
            return Response(
                {"error": "L'entité liée est inactivée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "entity": {
                    "code": entity.code,
                    "name": entity.name,
                    "phone": entity.phone,
                    "country": entity.country,
                    "entity_type": entity.entity_type,
                    "is_active": entity.is_active,
                    "created_at": entity.created_at,
                },
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "date_joined": user.date_joined,
                    "last_login": user.last_login,
                }
            },
            status=status.HTTP_200_OK,
        )
