from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models


class Entity(AbstractUser):
    ENTITY_TYPE_CHOICES = [
        ("MERCHANT", "Service Seller"),
        ("CLIENT", "API Client"),
        ("INTERNAL", "Internal System"),
    ]

    email = models.EmailField(unique=True)
    entity_id = models.UUIDField(default=uuid4, editable=False, unique=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    entity_type = models.CharField(
        max_length=10, choices=ENTITY_TYPE_CHOICES, default="CLIENT"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.name or self.username} ({self.entity_type})"

    class Meta:
        verbose_name = "Entité"  # nom singulier plus humain
        verbose_name_plural = "Entités"
