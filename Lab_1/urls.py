"""
URL configuration for Lab_1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from bmstu_lab import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib import admin
urlpatterns = [
    path('', views.coffee_list, name='home'),
    path('coffee/', views.coffee_list, name='coffee_list'),
    path('coffee/<int:coffee_id>/', views.coffee_detail, name='coffee_detail'),
    path('basket/', views.basket_detail, name='basket_detail'),
    path('basket/add/<int:product_id>/', views.add_to_basket, name='add_to_basket'),
    path('search/', views.search_results, name='search'),
    path('admin/', admin.site.urls),
]
# test
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)