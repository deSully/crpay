from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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
    model = AppUser
    list_display = ("email", "username", "entity", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "entity")
    search_fields = ("email", "username", "entity__name")
    ordering = ("-date_joined",)

    fieldsets = (
        ("Identifiants", {"fields": ("username", "email", "password")}),
        ("Données personnelles", {"fields": ("entity", "phone")}),
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
                    "phone",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
