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
