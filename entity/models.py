from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models


class Entity(models.Model):
    ENTITY_TYPE_CHOICES = [
        ("MERCHANT", "Marchand"),
        ("CLIENT", "Client API"),
        ("INTERNAL", "Système interne"),
    ]

    id = models.AutoField(primary_key=True)
    entity_id = models.UUIDField(default=uuid4, editable=False, unique=True, verbose_name="Identifiant")
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Téléphone")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    code = models.CharField(max_length=50, unique=True, verbose_name="Code")
    name = models.CharField(max_length=255, verbose_name="Nom")
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name="Pays")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    entity_type = models.CharField(
        max_length=10, choices=ENTITY_TYPE_CHOICES, default="CLIENT", verbose_name="Type"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return f"{self.name} ({self.get_entity_type_display()})"

    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"

class AppUser(AbstractUser):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name="users", verbose_name="Partenaire")

    email = models.EmailField(unique=True, verbose_name="Email")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.entity.name})"

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
