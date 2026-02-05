"""
URL configuration for Community Feed project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_root(request):
    """Root endpoint with API information."""
    return JsonResponse({
        'name': 'Playto Community Feed API',
        'version': '1.0.0',
        'endpoints': {
            'posts': '/api/posts/',
            'leaderboard': '/api/leaderboard/',
            'users': '/api/users/',
        },
        'docs': 'Visit /api/ for the browsable API',
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/', include('feed.urls')),
]
