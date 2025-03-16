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
from django.contrib import admin
from django.urls import path
from bmstu_lab.views import coffee_list, coffee_detail, basket_detail, add_to_basket

urlpatterns = [
    path("", coffee_list, name="product_list"),  # <-- Здесь добавляем name="product_list"
    path("coffee/<int:coffee_id>/", coffee_detail, name="clothes_detail"),
    path("basket/", basket_detail, name="basket_detail"),
    path("basket/add/<int:product_id>/", add_to_basket, name="add_to_basket"),
]

