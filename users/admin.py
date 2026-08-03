from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, RememberedDevice


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = UserAdmin.list_filter + ('role',)


@admin.register(RememberedDevice)
class RememberedDeviceAdmin(admin.ModelAdmin):
    """Read-only audit view. Delete a row to revoke a browser's view-only access."""

    list_display = ('user', 'created_at', 'last_seen_at', 'expires_at', 'revoked')
    list_filter = ('revoked',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = (
        'user', 'token_hash', 'auth_hash', 'user_agent',
        'created_at', 'last_seen_at', 'expires_at',
    )

    def has_add_permission(self, request):
        return False
