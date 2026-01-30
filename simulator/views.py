from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import analyze_interaction

class ChatInteractionView(APIView):
    """
    Endpoint for the 'Interactive Social Roleplay Platform'.
    Handles Vibe Check, Adaptive AI responses, and Mood shifts.
    """
    def post(self, request):
        user_text = request.data.get('message')
        scenario = request.data.get('scenario', 'Grocery Store') # Default MVP scenario

        if not user_text:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Process via the AI Engine (OpenAI/Gemini logic from your utils)
        result = analyze_interaction(user_text, scenario)
        
        return Response(result, status=status.HTTP_200_OK)
# Create your views here.
