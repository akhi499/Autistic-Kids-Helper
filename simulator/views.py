from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserSerializer
from .utils import analyze_interaction
from .models import InteractionLog


class SignupView(generics.CreateAPIView):
    """
    Allow anyone to register. Creates user with hashed password via UserSerializer.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ChatInteractionView(APIView):
    """
    Endpoint for the 'Interactive Social Roleplay Platform'.
    Handles Vibe Check, Adaptive AI responses, and Mood shifts.
    Requires Token authentication so the backend knows who is chatting.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_text = request.data.get('message')
        scenario = request.data.get('scenario', 'Grocery Store')

        if not user_text:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        result = analyze_interaction(user_text, scenario)

        # Log for analytics
        if result.get('status') == 'flagged':
            InteractionLog.objects.create(
                user=request.user, scenario=scenario, mood='', flagged=True
            )
        elif result.get('status') in ('success', 'error'):
            InteractionLog.objects.create(
                user=request.user,
                scenario=scenario,
                mood=result.get('mood', 'NEUTRAL'),
                flagged=False,
            )

        return Response(result, status=status.HTTP_200_OK)


class AnalyticsView(APIView):
    """
    Returns analytics for the authenticated user: totals, by scenario, by mood, last 7 days.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logs = InteractionLog.objects.filter(user=user)

        total = logs.count()
        by_scenario = {}
        by_mood = {}
        flagged_count = 0
        for log in logs:
            by_scenario[log.scenario] = by_scenario.get(log.scenario, 0) + 1
            if log.flagged:
                flagged_count += 1
            else:
                m = log.mood or 'NEUTRAL'
                by_mood[m] = by_mood.get(m, 0) + 1

        since = timezone.now() - timedelta(days=7)
        last_7 = logs.filter(created_at__gte=since)
        by_day = {}
        for log in last_7:
            day = log.created_at.date().isoformat()
            by_day[day] = by_day.get(day, 0) + 1
        last_7_days = [{"date": d, "count": c} for d, c in sorted(by_day.items())]

        return Response({
            "total_interactions": total,
            "flagged_count": flagged_count,
            "by_scenario": by_scenario,
            "by_mood": by_mood,
            "last_7_days": last_7_days,
        }, status=status.HTTP_200_OK)
