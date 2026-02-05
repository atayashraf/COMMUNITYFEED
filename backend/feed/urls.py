"""
URL configuration for the feed API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts', views.PostViewSet, basename='post')

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('', include(router.urls)),
    path('comments/<int:pk>/like/', views.CommentLikeView.as_view(), name='comment-like'),
    path('comments/<int:pk>/', views.CommentDeleteView.as_view(), name='comment-delete'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('users/<int:pk>/karma/', views.UserKarmaView.as_view(), name='user-karma'),
    path('users/', views.users_view, name='users'),
]
