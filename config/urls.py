"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import TemplateView
from users.profile_views import account_profile
from users.views import home as home_view
from reports.views import history as scan_history

urlpatterns = [
    # Modern website pages
    # `home_view` sends a remembered browser straight to its read-only dashboard
    # on the first visit of a session; brand-new visitors get the landing page.
    path('', home_view, name='home'),
    path('features/', TemplateView.as_view(template_name='features-modern.html'), name='features'),
    path('about/', TemplateView.as_view(template_name='about-modern.html'), name='about'),
    path('faq/', TemplateView.as_view(template_name='faq-modern.html'), name='faq'),
    path('profile/', TemplateView.as_view(template_name='profile-modern.html'), name='profile'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # App URLs
    path('users/', include('users.urls')),
    path('scanner/', include('scanner.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('alerts/', include('alerts.urls')),
    path('reports/', include('reports.urls')),
    path('history/', scan_history, name='scan_history'),
    path('accounts/profile/', account_profile, name='account_profile'),
    path('quiz/', include('quiz.urls')),
    path('chatbot/', include('chatbot.urls')),
    path("accounts/", include("allauth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

