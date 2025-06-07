import uuid

from django.db import models

from entity.models import Entity


class Transaction(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=255, unique=True)
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="transactions"
    )
    details = models.JSONField(blank=True, null=True)
    purpose = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} - {self.status}"


class InTouchLog(models.Model):
    STATUS_CHOICES = [
        ("SENT", "Envoyée"),
        ("RECEIVED", "Callback reçu"),
        ("SUCCESS", "Succès confirmé"),
        ("FAILED", "Échec confirmé"),
    ]

    transaction = models.OneToOneField(
        "Transaction", on_delete=models.CASCADE, related_name="intouch_log"
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    callback_received_at = models.DateTimeField(null=True, blank=True)

    request_payload = models.JSONField()
    response_payload = models.JSONField(null=True, blank=True)
    http_status = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SENT")

    def __str__(self):
        return f"InTouchLog for {self.transaction.reference}"

    class Meta:
        verbose_name = "Trace des appels InTouch"
        verbose_name_plural = "Traces des appels InTouch"
        ordering = ["-sent_at"]
