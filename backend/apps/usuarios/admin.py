from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.usuarios.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "rol", "is_active")
    list_filter = ("rol", "is_active", "is_staff")
    fieldsets = DjangoUserAdmin.fieldsets + (("Rol", {"fields": ("rol",)}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Rol", {"fields": ("rol",)}),)
