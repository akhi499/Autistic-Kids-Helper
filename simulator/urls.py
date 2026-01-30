from django.urls import path
from .views import ChatInteractionView

urlpatterns = [
    path('chat/', ChatInteractionView.as_view(), name='chat_interaction'),
]