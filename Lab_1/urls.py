from django.db import router
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from Lab_1 import settings
from bmstu_lab.views import (
    ServicesListView,
    ServicesDetailView,
    ServicesImageUploadView,
    AddToDraftView,
    DishListView,
    DishDetailView,
    FormDishView,
    CompleteDishView, UserViewSet, login_view, logout_view
)

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router.register(r'user', UserViewSet, basename='user')

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

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('login',  login_view, name='login'),
    path('logout', logout_view, name='logout'),
]