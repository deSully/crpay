from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models


class Entity(models.Model):
    ENTITY_TYPE_CHOICES = [
        ("MERCHANT", "Service Seller"),
        ("CLIENT", "API Client"),
        ("INTERNAL", "Internal System"),
    ]

    id = models.AutoField(primary_key=True)
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
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.entity_type})"

    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"

class AppUser(AbstractUser):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name="users")

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.entity.name})"

    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
