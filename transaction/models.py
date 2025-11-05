import uuid

from django.db import models

from entity.models import Entity


class Transaction(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "En attente"),
        ("SUCCESS", "Réussie"),
        ("FAILED", "Échouée"),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Identifiant")
    reference = models.CharField(max_length=255, unique=True, verbose_name="Référence")
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="transactions", verbose_name="Entité"
    )
    details = models.JSONField(blank=True, null=True, verbose_name="Détails")
    purpose = models.CharField(max_length=255, blank=True, null=True, verbose_name="Objet")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING", verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifiée le")

    def __str__(self):
        return f"{self.reference} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-created_at"]


class PaymentProviderLog(models.Model):
    STATUS_CHOICES = [
        ("SENT", "Envoyée"),
        ("RECEIVED", "Callback reçu"),
        ("SUCCESS", "Succès confirmé"),
        ("FAILED", "Échec confirmé"),
    ]

    transaction = models.OneToOneField(
        "Transaction", on_delete=models.CASCADE, related_name="provider_log", verbose_name="Transaction"
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Envoyé le")
    callback_received_at = models.DateTimeField(null=True, blank=True, verbose_name="Callback reçu le")

    request_payload = models.JSONField(verbose_name="Requête envoyée")
    response_payload = models.JSONField(null=True, blank=True, verbose_name="Réponse reçue")
    http_status = models.IntegerField(null=True, blank=True, verbose_name="Code HTTP")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SENT", verbose_name="Statut")
    provider = models.CharField(max_length=50, default="MPP", verbose_name="Provider", help_text="Nom du provider (MPP, InTouch, etc.)")

    def __str__(self):
        return f"Log [{self.provider}] pour {self.transaction.reference}"

    class Meta:
        verbose_name = "Journal d'appel provider"
        verbose_name_plural = "Journaux d'appels provider"
        ordering = ["-sent_at"]
