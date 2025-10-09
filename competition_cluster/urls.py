# FILE: competition_cluster/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('', include('exams.urls')), 
]

# This is required to serve static and media files during development
if settings.DEBUG:
    # Do NOT add the line for STATIC_URL here, Django handles it automatically
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)