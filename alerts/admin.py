from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'scan_result', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('user__username', 'user__email', 'subject', 'message')
    readonly_fields = ('sent_at',)
