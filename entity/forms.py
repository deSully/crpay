from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import AppUser


class AppUserCreationForm(UserCreationForm):
    class Meta:
        model = AppUser
        fields = ("email", "username", "entity")

class AppUserChangeForm(UserChangeForm):
    class Meta:
        model = AppUser
        fields = ("email", "username", "entity")