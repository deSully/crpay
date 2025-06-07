from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from entity.models import Entity


class EntityLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        code = request.data.get("code")
        entity_id = request.data.get("entity_id")

        if not code or not entity_id:
            return Response(
                {"error": "Le code et l'entity_id sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entity = Entity.objects.get(code=code, entity_id=entity_id)
        except Entity.DoesNotExist:
            return Response(
                {"error": "Entité non trouvée ou identifiants invalides."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if entity.entity_type not in ["CLIENT", "INTERNAL"]:
            return Response(
                {"error": "Cette entité n'est pas autorisée à se connecter via l'API."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not entity.is_active:
            return Response(
                {"error": "Le compte est inactif."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(entity)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "entity": {
                    "code": entity.code,
                    "name": entity.name,
                    "email": entity.email,
                    "phone": entity.phone,
                    "entity_type": entity.entity_type,
                    "is_active": entity.is_active,
                    "date_joined": entity.date_joined,
                    "last_login": entity.last_login,
                    "created_at": entity.created_at,
                    "username": entity.username,
                },
            },
            status=status.HTTP_200_OK,
        )
