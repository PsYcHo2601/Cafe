from django.urls import path
from bmstu_lab import views

app_name = 'coffee'

urlpatterns = [
    path('table_list', views.TableListView.as_view(), name='table_list'),
    path('', views.TableListView.as_view(), name='table_list'),
    path('products/', views.ProductListView.as_view(), name='product_list'),

    path('order/create/<int:table_id>/', views.OrderCreateView.as_view(), name='order_create'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('order/<int:pk>/update/', views.OrderUpdateView.as_view(), name='order_update'),
    path('order/<int:pk>/update-status/', views.OrderStatusUpdateView.as_view(), name='order_status_update'),
]
