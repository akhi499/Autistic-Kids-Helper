from django.contrib import admin
from .models import InteractionLog, UserProfile, PracticeSession, PracticeSessionMessage


@admin.register(InteractionLog)
class InteractionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'mood', 'flagged', 'created_at')
    list_filter = ('scenario', 'flagged', 'mood')
    search_fields = ('user__username',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'coins', 'purchased_reward_ids')
    search_fields = ('user__username',)


class PracticeSessionMessageInline(admin.TabularInline):
    model = PracticeSessionMessage
    extra = 0
    ordering = ['order']


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'ended_at', 'total_messages', 'kind_moments', 'flagged_count', 'hurt_moments')
    list_filter = ('scenario',)
    search_fields = ('user__username',)
    inlines = [PracticeSessionMessageInline]
