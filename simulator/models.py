from django.db import models
from django.conf import settings


class InteractionLog(models.Model):
    """Stores each chat outcome for analytics: user, scenario, mood, flagged."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interaction_logs')
    scenario = models.CharField(max_length=64)
    mood = models.CharField(max_length=16, blank=True)  # HAPPY, SAD, ANGRY, NEUTRAL, or '' for flagged/error
    flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class UserProfile(models.Model):
    """Coins balance and purchased rewards for the coins/shop system."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    coins = models.PositiveIntegerField(default=0)
    purchased_reward_ids = models.JSONField(default=list)  # list of reward ids the user has bought

    class Meta:
        ordering = ['user']


class PracticeSession(models.Model):
    """One practice session (one scenario), logged when user ends practice for parent review."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='practice_sessions')
    scenario = models.CharField(max_length=64)
    ended_at = models.DateTimeField(auto_now_add=True)
    # Snapshot of session stats for the recap
    total_messages = models.PositiveIntegerField(default=0)
    kind_moments = models.PositiveIntegerField(default=0)
    flagged_count = models.PositiveIntegerField(default=0)
    hurt_moments = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-ended_at']


class PracticeSessionMessage(models.Model):
    """One message in a practice session transcript (for parent review)."""
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=16)  # 'user' or 'assistant'
    text = models.TextField()
    mood = models.CharField(max_length=16, blank=True)  # for assistant: HAPPY, SAD, ANGRY, NEUTRAL
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
