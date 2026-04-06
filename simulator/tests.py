import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import InteractionLog, UserProfile, PracticeSession, PracticeSessionMessage
from .utils import analyze_interaction


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_user_profile_creation(self):
        profile = UserProfile.objects.create(user=self.user, coins=10)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.coins, 10)
        self.assertEqual(profile.purchased_reward_ids, [])

    def test_interaction_log_creation(self):
        log = InteractionLog.objects.create(
            user=self.user,
            scenario='Grocery Store',
            mood='HAPPY',
            flagged=False
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.scenario, 'Grocery Store')
        self.assertEqual(log.mood, 'HAPPY')
        self.assertFalse(log.flagged)

    def test_practice_session_creation(self):
        session = PracticeSession.objects.create(
            user=self.user,
            scenario='Grocery Store',
            total_messages=5,
            kind_moments=3,
            flagged_count=1,
            hurt_moments=0
        )
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.scenario, 'Grocery Store')
        self.assertEqual(session.total_messages, 5)

    def test_practice_session_message_creation(self):
        session = PracticeSession.objects.create(user=self.user, scenario='Test')
        message = PracticeSessionMessage.objects.create(
            session=session,
            sender='user',
            text='Hello',
            order=0
        )
        self.assertEqual(message.session, session)
        self.assertEqual(message.sender, 'user')
        self.assertEqual(message.text, 'Hello')


class UtilsTests(TestCase):
    def test_analyze_interaction_without_mistral(self):
        # Test fallback when Mistral is not available
        result = analyze_interaction('Hello', 'Grocery Store')
        self.assertEqual(result['status'], 'error')
        self.assertIn('Mistral API key not configured', result['reply'])
        self.assertEqual(result['mood'], 'NEUTRAL')


class ViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_signup_view(self):
        self.client.logout()
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'new@example.com'
        }
        response = self.client.post('/api/signup/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_profile_view(self):
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['coins'], 0)

    def test_award_coins_view(self):
        data = {'amount': 10}
        response = self.client.post('/api/coins/award/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['coins'], 10)

        # Check invalid amount
        data = {'amount': 0}
        response = self.client.post('/api/coins/award/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shop_view(self):
        response = self.client.get('/api/shop/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rewards', response.data)
        self.assertIn('coins', response.data)

    def test_redeem_reward_view(self):
        # First award coins
        self.client.post('/api/coins/award/', {'amount': 50})

        # Redeem a reward
        data = {'reward_id': 'kindness_badge'}
        response = self.client.post('/api/shop/redeem/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['coins'], 25)  # 50 - 25 = 25

        # Try to redeem again
        response = self.client.post('/api/shop/redeem/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_interaction_view(self):
        data = {
            'message': 'Hello',
            'scenario': 'Grocery Store',
            'history': []
        }
        response = self.client.post('/api/chat/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Since Mistral is not configured, it should return error
        self.assertEqual(response.data['status'], 'error')

    def test_analytics_view(self):
        # Create some logs
        InteractionLog.objects.create(user=self.user, scenario='Grocery Store', mood='HAPPY')
        InteractionLog.objects.create(user=self.user, scenario='Grocery Store', flagged=True)

        response = self.client.get('/api/analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_interactions'], 2)
        self.assertEqual(response.data['flagged_count'], 1)

    def test_end_practice_view(self):
        data = {
            'scenario': 'Grocery Store',
            'messages': [
                {'sender': 'user', 'text': 'Hello'},
                {'sender': 'assistant', 'text': 'Hi there!', 'mood': 'HAPPY'}
            ],
            'total_messages': 2,
            'kind_moments': 1,
            'flagged_count': 0,
            'hurt_moments': 0
        }
        response = self.client.post('/api/practice/end/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PracticeSession.objects.filter(user=self.user).exists())

    def test_session_list_view(self):
        PracticeSession.objects.create(user=self.user, scenario='Test')
        response = self.client.get('/api/sessions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['sessions']), 1)

    def test_session_detail_view(self):
        session = PracticeSession.objects.create(user=self.user, scenario='Test')
        PracticeSessionMessage.objects.create(session=session, sender='user', text='Hello', order=0)

        response = self.client.get(f'/api/sessions/{session.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['scenario'], 'Test')
        self.assertEqual(len(response.data['messages']), 1)

    def test_text_to_speech_view_no_api_key(self):
        data = {'text': 'Hello world'}
        response = self.client.post('/api/tts/', data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
