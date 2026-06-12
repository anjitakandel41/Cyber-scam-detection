from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    search_fields = ('user__username', 'user__email', 'message', 'response')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
