from django.urls import path

from Lab_1 import settings
from bmstu_lab.views import (
    ServicesListView,
    ServicesDetailView,
    ServicesImageUploadView,
    AddToDraftView,
    DishListView,
    DishDetailView,
    FormDishView,
    CompleteDishView
)

urlpatterns = [
    # URLs для услуг (Services)
    path('services/', ServicesListView.as_view(), name='services-list'),
    path('services/<uuid:pk>/', ServicesDetailView.as_view(), name='services-detail'),
    path('services/<uuid:pk>/image/', ServicesImageUploadView.as_view(), name='services-image-upload'),
    path('services/<uuid:service_id>/add-to-draft/', AddToDraftView.as_view(), name='add-to-draft'),

    # URLs для заявок (Dish)
    path('dishes/', DishListView.as_view(), name='dishes-list'),
    path('dishes/<uuid:pk>/', DishDetailView.as_view(), name='dishes-detail'),
    path('dishes/<uuid:pk>/form/', FormDishView.as_view(), name='form-dish'),
    path('dishes/<uuid:pk>/complete/', CompleteDishView.as_view(), name='complete-dish'),
]