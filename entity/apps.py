from django.apps import AppConfig


class EntityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "entity"
    verbose_name = "Gestion des Entités (Clients, Marchands, Internes)"
