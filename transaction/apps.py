from django.apps import AppConfig


class TransactionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "transaction"
    verbose_name = "Gestion des Paiments (Paiements, Remboursements, etc.)"
