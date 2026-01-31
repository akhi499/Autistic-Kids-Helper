from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import ChatInteractionView, SignupView, AnalyticsView

urlpatterns = [
    path('chat/', ChatInteractionView.as_view(), name='chat_interaction'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', obtain_auth_token, name='login'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]