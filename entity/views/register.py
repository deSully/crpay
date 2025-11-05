from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction

from entity.models import Entity, AppUser


class RegisterView(APIView):
    """
    Endpoint d'inscription self-service pour les nouveaux partenaires
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Créer un compte partenaire",
        operation_description="""
**Inscription self-service** pour les nouveaux partenaires.

Crée automatiquement :
- Une entité (partenaire)
- Un utilisateur administrateur lié à cette entité
- Retourne les tokens JWT pour commencer à utiliser l'API immédiatement

⚠️ **Important** : 
- Le `entity_code` doit être unique (ex: "MYCOMPANY")
- L'email doit être unique
- Après inscription, vous pouvez directement utiliser les tokens pour appeler l'API

**Exemple de requête :**
```json
{
  "entity_name": "Ma Super Boutique",
  "entity_code": "SUPERBOUTIQUE",
  "email": "admin@superboutique.com",
  "password": "MonMotDePasse123!",
  "phone": "+22570123456",
  "country": "Côte d'Ivoire"
}
```
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['entity_name', 'entity_code', 'email', 'password'],
            properties={
                'entity_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Nom de votre entreprise/partenaire',
                    example='Ma Super Boutique'
                ),
                'entity_code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Code unique pour votre entité (lettres majuscules sans espaces)',
                    example='SUPERBOUTIQUE'
                ),
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='Email de l\'administrateur (servira de login)',
                    example='admin@superboutique.com'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description='Mot de passe (minimum 8 caractères)',
                    example='MonMotDePasse123!'
                ),
                'phone': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Numéro de téléphone (optionnel)',
                    example='+22570123456'
                ),
                'country': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Pays (optionnel)',
                    example='Côte d\'Ivoire'
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="Compte créé avec succès",
                examples={
                    "application/json": {
                        "message": "Compte créé avec succès. Vous pouvez maintenant utiliser l'API.",
                        "entity": {
                            "entity_id": "123e4567-e89b-12d3-a456-426614174000",
                            "code": "SUPERBOUTIQUE",
                            "name": "Ma Super Boutique",
                            "entity_type": "CLIENT"
                        },
                        "user": {
                            "email": "admin@superboutique.com",
                            "username": "admin@superboutique.com"
                        },
                        "tokens": {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                        }
                    }
                }
            ),
            400: "Données invalides ou manquantes"
        },
        tags=["🔐 Authentification"]
    )
    def post(self, request):
        # Récupérer les données
        entity_name = request.data.get('entity_name')
        entity_code = request.data.get('entity_code')
        email = request.data.get('email')
        password = request.data.get('password')
        phone = request.data.get('phone')
        country = request.data.get('country')

        # Validation
        if not all([entity_name, entity_code, email, password]):
            return Response(
                {"error": "Les champs entity_name, entity_code, email et password sont requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier si l'entity_code existe déjà
        if Entity.objects.filter(code=entity_code).exists():
            return Response(
                {"error": f"Le code '{entity_code}' est déjà utilisé. Veuillez en choisir un autre."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier si l'email existe déjà
        if AppUser.objects.filter(email=email).exists():
            return Response(
                {"error": f"L'email '{email}' est déjà utilisé."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valider le mot de passe
        if len(password) < 8:
            return Response(
                {"error": "Le mot de passe doit contenir au moins 8 caractères."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Créer l'entity et l'utilisateur dans une transaction
        try:
            with transaction.atomic():
                # 1. Créer l'entité
                entity = Entity.objects.create(
                    name=entity_name,
                    code=entity_code.upper(),
                    phone=phone,
                    country=country,
                    entity_type="CLIENT",
                    is_active=True
                )

                # 2. Créer l'utilisateur admin
                user = AppUser.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    entity=entity,
                    is_staff=False,
                    is_superuser=False
                )

                # 3. Générer les tokens JWT
                refresh = RefreshToken.for_user(user)

                return Response(
                    {
                        "message": "Compte créé avec succès. Vous pouvez maintenant utiliser l'API.",
                        "entity": {
                            "entity_id": str(entity.entity_id),
                            "code": entity.code,
                            "name": entity.name,
                            "entity_type": entity.entity_type
                        },
                        "user": {
                            "email": user.email,
                            "username": user.username
                        },
                        "tokens": {
                            "access": str(refresh.access_token),
                            "refresh": str(refresh)
                        }
                    },
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la création du compte : {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
