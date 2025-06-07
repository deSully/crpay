from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Entity


@admin.register(Entity)
class EntityAdmin(UserAdmin):
    model = Entity

    list_display = (
        "email",
        "nom_utilisateur",
        "type_entite",
        "code_fr",
        "nom_fr",
        "telephone",
        "pays",
        "date_creation",
        "actif",
        "id_entite",
        "derniere_connexion",
    )

    def nom_utilisateur(self, obj):
        return obj.username

    nom_utilisateur.short_description = "Nom d'utilisateur"

    def type_entite(self, obj):
        return obj.entity_type

    type_entite.short_description = "Type d’entité"

    def code_fr(self, obj):
        return obj.code

    code_fr.short_description = "Code"

    def nom_fr(self, obj):
        return obj.name

    nom_fr.short_description = "Nom"

    def telephone(self, obj):
        return obj.phone

    telephone.short_description = "Téléphone"

    def pays(self, obj):
        return obj.country

    pays.short_description = "Pays"

    def date_creation(self, obj):
        return obj.created_at.strftime("%d/%m/%Y à %H:%M")

    date_creation.short_description = "Date de création"

    def actif(self, obj):
        return obj.is_active

    actif.short_description = "Actif"
    actif.boolean = True

    def id_entite(self, obj):
        return obj.entity_id

    id_entite.short_description = "ID entité"

    def derniere_connexion(self, obj):
        if obj.last_login:
            return obj.last_login.strftime("%d/%m/%Y à %H:%M")
        return "-"

    derniere_connexion.short_description = "Dernière connexion"

    list_filter = ("entity_type", "is_active", "is_staff", "is_superuser", "country")
    search_fields = ("email", "username", "name", "code", "phone")
    ordering = ("-created_at",)

    fieldsets = (
        ("Identifiants", {"fields": ("username", "email", "password")}),
        (
            "Informations personnelles",
            {"fields": ("name", "code", "entity_type", "phone", "country", "address")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates importantes", {"fields": ("last_login", "created_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "entity_type",
                    "code",
                    "name",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "last_login")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Liste des entités (Marchands, Clients, Partenaires)"
        return super().changelist_view(request, extra_context=extra_context)

    def is_internal(self, request):
        return (
            hasattr(request.user, "entity_type")
            and request.user.entity_type == "INTERNAL"
        )

    def has_add_permission(self, request):
        return self.is_internal(request)

    def has_change_permission(self, request, obj=None):
        return self.is_internal(request)

    def has_delete_permission(self, request, obj=None):
        return self.is_internal(request)
