"""
URL configuration for sociable_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os

def serve_html_file(request, filename):
    file_path = os.path.join(settings.BASE_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse('File not found', status=404)

def dashboard_view(request):
    return serve_html_file(request, 'dashboard.html')

def index_view(request):
    return serve_html_file(request, 'index.html')

def about_view(request):
    return serve_html_file(request, 'about.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('simulator.urls')), # Routes all simulator calls to /api/chat/
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/index.html', dashboard_view, name='dashboard_index'),
    path('', index_view, name='index'),
    path('about/', about_view, name='about'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
