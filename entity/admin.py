from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import AppUserCreationForm, AppUserChangeForm

from .models import AppUser, Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "type_entite",
        "code",
        "telephone",
        "pays",
        "date_creation",
        "actif",
        "id_entite",
    )

    def nom(self, obj):
        return obj.name

    nom.short_description = "Nom"

    def type_entite(self, obj):
        return obj.entity_type

    type_entite.short_description = "Type d’entité"

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

    list_filter = ("entity_type", "is_active", "country")
    search_fields = ("email", "name", "code", "phone")
    ordering = ("-created_at",)

    readonly_fields = ("created_at",)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Liste des entités (Marchands, Clients, Partenaires)"
        return super().changelist_view(request, extra_context=extra_context)

    def is_internal(self, request):
        return (
            hasattr(request.user, "entity")
            and request.user.entity.entity_type == "INTERNAL"
        )

    def has_add_permission(self, request):
        return self.is_internal(request)

    def has_change_permission(self, request, obj=None):
        return self.is_internal(request)

    def has_delete_permission(self, request, obj=None):
        return self.is_internal(request)


@admin.register(AppUser)
class AppUserAdmin(UserAdmin):
    add_form = AppUserCreationForm
    form = AppUserChangeForm
    model = AppUser

    list_display = ("email", "username", "entity", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "entity")
    search_fields = ("email", "username", "entity__name")
    ordering = ("-date_joined",)

    fieldsets = (
        ("Identifiants", {"fields": ("username", "email", "password")}),
        ("Données personnelles", {"fields": ("entity",)}),
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
        ("Dates importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "entity",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Liste des Agents (Utilisateurs de l’application)"
        extra_context["subtitle"] = "Gérer les utilisateurs de l'application"
        extra_context["description"] = (
            "Cette section vous permet de gérer les utilisateurs de l'application, "
            "y compris les agents et les administrateurs."
        )
        extra_context["help_text"] = (
            "Pour ajouter un nouvel utilisateur, cliquez sur 'Ajouter un utilisateur'. "
            "Pour modifier ou supprimer un utilisateur existant, utilisez les actions disponibles."
        )
        return super().changelist_view(request, extra_context=extra_context)
