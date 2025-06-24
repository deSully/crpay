import asyncio
import csv
from datetime import timedelta

from django.contrib import admin, messages
from django.db import models
from django.db.models import Avg, Count, Sum
from django.db.models.functions import ExtractHour, TruncDate
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.dateparse import parse_date
from django.utils.html import format_html
from django.utils.timezone import now
from django_json_widget.widgets import JSONEditorWidget
from rangefilter.filters import DateRangeFilter

from transaction.models import Transaction
from transaction.utils import ExternalTransactionDispatcher

from .models import InTouchLog

admin.site.site_header = "CRPAY-ADMIN"
admin.site.site_title = "CRPAY-ADMIN"
admin.site.index_title = ""


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_filter = (("created_at", DateRangeFilter), "status", "purpose")
    search_fields = ("reference", "purpose", "details")
    readonly_fields = ("uuid", "created_at", "updated_at")
    list_per_page = 20

    list_display = (
        "ref_fr",
        "montant_fr",
        "colored_status",
        "libelle_fr",
        "date_creation_fr",
    )

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget(mode="view")},
    }

    def ref_fr(self, obj):
        return obj.reference

    ref_fr.short_description = "Référence"

    def montant_fr(self, obj):
        return f"{obj.amount:,.0f} XOF".replace(",", " ")

    montant_fr.short_description = "Montant"

    def libelle_fr(self, obj):
        return obj.purpose

    libelle_fr.short_description = "Libellé"

    def date_creation_fr(self, obj):
        return obj.created_at.strftime("%d/%m/%Y à %H:%M")

    date_creation_fr.short_description = "Date de création"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if hasattr(user, "entity") and user.entity.entity_type == "INTERNAL":
            return qs
        return qs.filter(entity=user)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Liste des paiements"
        extra_context["custom_stats_link"] = "/admin/transaction/transaction/stats/"
        extra_context["custom_stats_title"] = "Statistiques des transactions"
        extra_context["custom_stats_description"] = (
            "Consultez les statistiques des transactions sur une période donnée. "
            "Vous pouvez filtrer par date et par type de transaction."
        )
        extra_context["custom_stats_help_text"] = (
            "Sélectionnez une période pour afficher les statistiques des transactions. "
            "Vous pouvez également filtrer par type de transaction."
        )
        extra_context["subtitle"] = "Gérer les transactions de l'application"
        extra_context["description"] = (
            "Cette section vous permet de gérer les transactions effectuées dans l'application. "
            "Vous pouvez consulter les détails des transactions, exporter des données et accéder aux statistiques."
        )
        extra_context["help_text"] = (
            "Pour ajouter une nouvelle transaction, utilisez l'API. "
            "Pour consulter les transactions existantes, utilisez les filtres disponibles."
        )
        return super().changelist_view(request, extra_context=extra_context)

    def colored_status(self, obj):
        color_map = {
            "SUCCESS": "green",
            "PENDING": "orange",
            "FAILED": "red",
        }
        color = color_map.get(obj.status, "black")
        return format_html(
            '<span style="display: inline-block; padding: 2px 8px; border-radius: 12px; background-color: {}; color: white; font-weight: bold;">{}</span>',
            color,
            obj.status,
        )

    colored_status.short_description = "Statut"
    colored_status.admin_order_field = "status"

    @admin.action(description="Exporter la sélection en CSV")
    def export_as_csv(modeladmin, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'

        writer = csv.writer(response)
        writer.writerow(["ID", "Référence", "Montant", "Date"])  # adapte les champs
        for obj in queryset:
            writer.writerow(
                [obj.uuid, obj.reference, obj.amount, obj.created_at]
            )  # adapte aussi

        return response

    actions = [export_as_csv]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "stats/",
                self.admin_site.admin_view(self.transaction_stats_view),
                name="transaction-stats",
            ),
        ]
        return custom_urls + urls

    def transaction_stats_view(self, request):
        # Récupérer filtre période (dates au format YYYY-MM-DD)
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        purposes_selected = request.GET.getlist("purposes")

        today = now().date()

        # Dates par défaut : 30 jours avant aujourd’hui à aujourd’hui inclus
        if start_date_str:
            start_date = parse_date(start_date_str)
        else:
            start_date = today - timedelta(days=30)

        if end_date_str:
            end_date = parse_date(end_date_str)
        else:
            end_date = today

        # Filtrer les transactions sur la période (inclusif)
        qs = Transaction.objects.filter(created_at__date__range=[start_date, end_date])

        if purposes_selected:
            qs = qs.filter(purpose__in=purposes_selected)

        # Résumé des montants
        total_amount_paid = qs.aggregate(total=Sum("amount"))["total"] or 0
        avg_amount_paid = qs.aggregate(avg=Avg("amount"))["avg"] or 0

        # Total aujourd’hui (indépendamment du filtre)
        total_today = (
            Transaction.objects.filter(created_at__date=today).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        # 1. Paiments par jour
        tx_per_day = (
            qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("uuid"), sum_amount=Sum("amount"))
            .order_by("date")
        )
        labels_days = [entry["date"].strftime("%Y-%m-%d") for entry in tx_per_day]
        counts_days = [entry["count"] for entry in tx_per_day]
        sums_days = [entry["sum_amount"] or 0 for entry in tx_per_day]

        # Cumulatif montants par jour
        cumulative_amounts = []
        cum_sum = 0
        for s in sums_days:
            cum_sum += s
            cumulative_amounts.append(round(cum_sum, 2))

        # Moyenne montants par jour (déjà faite globalement, mais on peut aussi la calculer par jour)
        avg_amounts_per_day = round(total_amount_paid / max(len(sums_days), 1), 2)

        # 2. Paiments par purpose
        tx_per_purpose = (
            qs.values("purpose")
            .annotate(count=Count("uuid"), sum_amount=Sum("amount"))
            .order_by("-count")
        )
        labels_purpose = [entry["purpose"] for entry in tx_per_purpose]
        counts_purpose = [entry["count"] for entry in tx_per_purpose]
        amounts_per_purpose = [
            entry["sum_amount"] or 0 for entry in tx_per_purpose
        ]  # Montants totaux par purpose

        # Top 5 purposes
        top5 = tx_per_purpose[:5]
        top5_purposes_labels = [entry["purpose"] for entry in top5]
        top5_purposes_counts = [entry["count"] for entry in top5]

        # 3. Statuts (success, failed, pending)
        status_counts = (
            qs.values("status").annotate(count=Count("uuid")).order_by("status")
        )
        labels_status = [entry["status"] for entry in status_counts]
        counts_status = [entry["count"] for entry in status_counts]

        # 4. Paiments par heure (0-23)
        tx_per_hour = (
            qs.annotate(hour=ExtractHour("created_at"))
            .values("hour")
            .annotate(count=Count("uuid"))
            .order_by("hour")
        )
        # On veut les 24 heures, même celles à 0 transaction
        counts_by_hour = {entry["hour"]: entry["count"] for entry in tx_per_hour}
        labels_hours = [str(h) for h in range(24)]
        counts_hours = [counts_by_hour.get(h, 0) for h in range(24)]

        context = dict(
            self.admin_site.each_context(request),
            labels_days=labels_days,
            counts_days=counts_days,
            labels_purpose=labels_purpose,
            counts_purpose=counts_purpose,
            amounts_per_purpose=[f"{amount:.2f}" for amount in amounts_per_purpose],
            labels_status=labels_status,
            counts_status=counts_status,
            total_amount_paid=f"{total_amount_paid:.2f}",
            avg_amount_paid=f"{avg_amount_paid:.2f}",
            total_today=f"{total_today:.2f}",
            currency="XOF",  # adapte ta monnaie ici si besoin
            title="",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            purposes=[
                "Carte grise",
                "Assurance",
                "Permis de conduire",
                "Vignette",
                "Autre",
            ],
            purposes_selected=purposes_selected,
            cumulative_amounts=cumulative_amounts,
            avg_amounts_per_day=avg_amounts_per_day,
            top5_purposes_labels=top5_purposes_labels,
            top5_purposes_counts=top5_purposes_counts,
            labels_hours=labels_hours,
            counts_hours=counts_hours,
        )
        return TemplateResponse(request, "admin/transaction/stats.html", context)


@admin.register(InTouchLog)
class InTouchLogAdmin(admin.ModelAdmin):
    list_display = (
        "reference_transaction",
        "statut",
        "colored_http_status",
        "envoye_le",
        "recu_le",
    )

    def reference_transaction(self, obj):
        return obj.transaction

    reference_transaction.short_description = "Référence transaction"

    def statut(self, obj):
        return obj.status

    statut.short_description = "Statut"

    def envoye_le(self, obj):
        return obj.sent_at.strftime("%d/%m/%Y à %H:%M") if obj.sent_at else "-"

    envoye_le.short_description = "Envoyé le"

    def recu_le(self, obj):
        return (
            obj.callback_received_at.strftime("%d/%m/%Y à %H:%M")
            if obj.callback_received_at
            else "-"
        )

    recu_le.short_description = "Reçu le"

    list_per_page = 20
    ordering = ("-sent_at",)
    list_filter = ("status", "sent_at", "callback_received_at")
    search_fields = ("transaction__reference",)
    readonly_fields = (
        "transaction",
        "sent_at",
        "callback_received_at",
        "http_status",
        "status",
    )
    actions = ["relancer_envoi_intouch"]

    fieldsets = (
        (None, {"fields": ("transaction", "status", "http_status")}),
        ("Horodatages", {"fields": ("sent_at", "callback_received_at")}),
        (
            "Payloads",
            {
                "classes": ("collapse",),
                "fields": ("request_payload", "response_payload"),
            },
        ),
    )

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget(mode="view")},
    }

    def colored_http_status(self, obj):
        color = "gray"
        if obj.http_status is None:
            color = "lightgray"
            text = "N/A"
        elif 200 <= obj.http_status < 300:
            color = "green"
            text = str(obj.http_status)
        elif 400 <= obj.http_status < 500:
            color = "orange"
            text = str(obj.http_status)
        elif 500 <= obj.http_status < 600:
            color = "red"
            text = str(obj.http_status)
        else:
            text = str(obj.http_status)

        return format_html(
            '<span style="display: inline-block; padding: 2px 8px; border-radius: 12px; background-color: {}; color: white; font-weight: bold;">{}</span>',
            color,
            text,
        )

    colored_http_status.short_description = "HTTP Status"
    colored_http_status.admin_order_field = "http_status"

    def is_interne(self, request):
        return (
            hasattr(request.user, "entity_type")
            and request.user.entity.entity_type == "INTERNAL"
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.is_interne(request):
            return qs
        return qs.none()  # retournera une page vide

    def has_view_permission(self, request, obj=None):
        return self.is_interne(request)

    def transaction_reference(self, obj):
        return obj.transaction.reference

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Liste des transactions InTouch"
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description="Relancer l'envoi à InTouch")
    def relancer_envoi_intouch(self, request, queryset):
        count = 0
        for log in queryset:
            dispatcher = ExternalTransactionDispatcher(log.transaction)
            response = asyncio.run(dispatcher.dispatch())

            if response.status_code == 200:
                count += 1
                messages.success(
                    request,
                    f"Transaction {log.transaction.reference} renvoyée avec succès.",
                )
            else:
                messages.error(
                    request,
                    f"Erreur lors de l’envoi de {log.transaction.reference} (HTTP {response.status_code})",
                )
        if count:
            messages.info(request, f"{count} transaction(s) relancée(s) avec succès.")

    transaction_reference.short_description = "Référence transaction"
