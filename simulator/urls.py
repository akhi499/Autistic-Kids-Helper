from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    ChatInteractionView,
    SignupView,
    AnalyticsView,
    ProfileView,
    AwardCoinsView,
    ShopView,
    RedeemRewardView,
    EndPracticeView,
    SessionListView,
    SessionDetailView,
)

urlpatterns = [
    path('chat/', ChatInteractionView.as_view(), name='chat_interaction'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', obtain_auth_token, name='login'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('coins/award/', AwardCoinsView.as_view(), name='coins_award'),
    path('shop/', ShopView.as_view(), name='shop'),
    path('shop/redeem/', RedeemRewardView.as_view(), name='shop_redeem'),
    path('practice/end/', EndPracticeView.as_view(), name='practice_end'),
    path('sessions/', SessionListView.as_view(), name='session_list'),
    path('sessions/<int:session_id>/', SessionDetailView.as_view(), name='session_detail'),
]