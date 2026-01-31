from django.contrib import admin
from .models import InteractionLog

@admin.register(InteractionLog)
class InteractionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'mood', 'flagged', 'created_at')
    list_filter = ('scenario', 'flagged', 'mood')
    search_fields = ('user__username',)
