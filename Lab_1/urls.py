from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('', include('bmstu_lab.urls', namespace='coffee')),  # Обратите внимание на namespace
    path('accounts/', include('django.contrib.auth.urls')),  # Стандартные auth URLs
    path('admin/', admin.site.urls),  # Стандартные auth URLs
]
