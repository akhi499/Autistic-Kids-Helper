import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.shortcuts import render
from django.http import HttpResponse
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
from .models import InteractionLog, UserProfile, PracticeSession, PracticeSessionMessage

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Reward shop: id, name, cost, description (suitable for kids)
REWARDS = [
    {"id": "kindness_badge", "name": "Kindness Badge", "cost": 25, "description": "A shiny badge for your profile."},
    {"id": "star_border", "name": "Star Avatar Border", "cost": 50, "description": "Stars around your character."},
    {"id": "rainbow_theme", "name": "Rainbow Theme", "cost": 75, "description": "Colorful rainbow chat theme."},
    {"id": "certificate", "name": "Certificate of Kindness", "cost": 100, "description": "Print a certificate!"},
    {"id": "confetti", "name": "Confetti Effect", "cost": 40, "description": "Celebrate with confetti when you reach a goal."},
]


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
        history = request.data.get('history')  # list of { sender: 'user'|'assistant', text: '...' }

        if not user_text:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(history, list):
            history = []
        # Keep last N turns to avoid huge context (e.g. last 10 messages = 5 exchanges)
        max_history = 12
        history = history[-max_history:]

        result = analyze_interaction(user_text, scenario, history=history)

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


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"coins": 0})
    return profile


class ProfileView(APIView):
    """Returns the current user's coins and purchased reward ids."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_or_create_profile(request.user)
        return Response({
            "username": request.user.username,
            "coins": profile.coins,
            "purchased_reward_ids": profile.purchased_reward_ids,
        }, status=status.HTTP_200_OK)


class AwardCoinsView(APIView):
    """Award coins for kind moments or reaching a goal. Called by frontend."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount", 0)
        if not isinstance(amount, int) or amount <= 0 or amount > 100:
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)
        profile = get_or_create_profile(request.user)
        profile.coins += amount
        profile.save(update_fields=["coins"])
        return Response({"coins": profile.coins, "awarded": amount}, status=status.HTTP_200_OK)


class ShopView(APIView):
    """List available rewards."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_or_create_profile(request.user)
        rewards = []
        for r in REWARDS:
            rewards.append({
                **r,
                "owned": r["id"] in (profile.purchased_reward_ids or []),
            })
        return Response({"rewards": rewards, "coins": profile.coins}, status=status.HTTP_200_OK)


class RedeemRewardView(APIView):
    """Spend coins to purchase a reward."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reward_id = request.data.get("reward_id")
        if not reward_id:
            return Response({"error": "reward_id required"}, status=status.HTTP_400_BAD_REQUEST)
        reward = next((r for r in REWARDS if r["id"] == reward_id), None)
        if not reward:
            return Response({"error": "Unknown reward"}, status=status.HTTP_400_BAD_REQUEST)
        profile = get_or_create_profile(request.user)
        purchased = profile.purchased_reward_ids or []
        if reward_id in purchased:
            return Response({"error": "Already owned", "coins": profile.coins}, status=status.HTTP_400_BAD_REQUEST)
        if profile.coins < reward["cost"]:
            return Response({"error": "Not enough coins", "coins": profile.coins}, status=status.HTTP_400_BAD_REQUEST)
        profile.coins -= reward["cost"]
        purchased = list(purchased) + [reward_id]
        profile.purchased_reward_ids = purchased
        profile.save(update_fields=["coins", "purchased_reward_ids"])
        return Response({
            "coins": profile.coins,
            "reward_id": reward_id,
            "purchased_reward_ids": profile.purchased_reward_ids,
        }, status=status.HTTP_200_OK)


class EndPracticeView(APIView):
    """Log the current conversation as a practice session for parent review, then frontend resets chat."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        scenario = request.data.get('scenario', 'Grocery Store')
        messages = request.data.get('messages')  # list of { sender, text, mood? }
        total_messages = request.data.get('total_messages', 0)
        kind_moments = request.data.get('kind_moments', 0)
        flagged_count = request.data.get('flagged_count', 0)
        hurt_moments = request.data.get('hurt_moments', 0)

        if not isinstance(messages, list):
            messages = []

        session = PracticeSession.objects.create(
            user=request.user,
            scenario=scenario,
            total_messages=total_messages,
            kind_moments=kind_moments,
            flagged_count=flagged_count,
            hurt_moments=hurt_moments,
        )
        for i, m in enumerate(messages):
            sender = (m.get('sender') or 'user').lower()
            if sender not in ('user', 'assistant'):
                continue
            PracticeSessionMessage.objects.create(
                session=session,
                sender=sender,
                text=(m.get('text') or '')[:4096],
                mood=(m.get('mood') or '')[:16] if sender == 'assistant' else '',
                order=i,
            )
        return Response({
            "session_id": session.id,
            "message_count": len(messages),
        }, status=status.HTTP_200_OK)


class SessionListView(APIView):
    """List practice sessions for the authenticated user (parent review)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = PracticeSession.objects.filter(user=request.user)[:50]
        data = [
            {
                "id": s.id,
                "scenario": s.scenario,
                "ended_at": s.ended_at.isoformat(),
                "total_messages": s.total_messages,
                "kind_moments": s.kind_moments,
                "flagged_count": s.flagged_count,
                "hurt_moments": s.hurt_moments,
            }
            for s in sessions
        ]
        return Response({"sessions": data}, status=status.HTTP_200_OK)


class SessionDetailView(APIView):
    """Get one practice session with full message transcript for parent review."""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = PracticeSession.objects.filter(user=request.user, id=session_id).first()
        if not session:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        messages = [
            {"sender": m.sender, "text": m.text, "mood": m.mood or None}
            for m in session.messages.all()
        ]
        return Response({
            "id": session.id,
            "scenario": session.scenario,
            "ended_at": session.ended_at.isoformat(),
            "total_messages": session.total_messages,
            "kind_moments": session.kind_moments,
            "flagged_count": session.flagged_count,
            "hurt_moments": session.hurt_moments,
            "messages": messages,
        }, status=status.HTTP_200_OK)


class TextToSpeechView(APIView):
    """Proxy to ElevenLabs TTS. Keeps API key on server. Set ELEVENLABS_API_KEY and optionally ELEVENLABS_VOICE_ID in .env."""
    permission_classes = [AllowAny]

    def post(self, request):
        api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM").strip()  # Rachel (default)
        if not api_key:
            return Response({"error": "ElevenLabs API key not configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        text = (request.data.get("text") or request.query_params.get("text") or "").strip()[:500]
        if not text:
            return Response({"error": "text required"}, status=status.HTTP_400_BAD_REQUEST)
        url = "https://api.elevenlabs.io/v1/text-to-speech/{}?output_format=mp3_44100_128".format(voice_id)
        payload = json.dumps({"text": text, "model_id": "eleven_multilingual_v2"}).encode("utf-8")
        req = Request(
            url,
            data=payload,
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=15) as resp:
                audio_bytes = resp.read()
        except HTTPError as e:
            return Response({"error": "TTS failed", "detail": str(e.code)}, status=status.HTTP_502_BAD_GATEWAY)
        except URLError as e:
            return Response({"error": "TTS failed", "detail": str(e.reason)}, status=status.HTTP_502_BAD_GATEWAY)
        return HttpResponse(audio_bytes, content_type="audio/mpeg")
