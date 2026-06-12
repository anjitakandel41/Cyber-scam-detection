from django.contrib import admin

from .models import ScanResult


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'classification', 'risk_score', 'report_file', 'timestamp')
    list_filter = ('classification', 'timestamp')
    search_fields = ('user__username', 'user__email', 'input')
    readonly_fields = ('timestamp',)
