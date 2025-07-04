from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='home'),

    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/edit/<int:pk>/', views.customer_edit, name='customer_edit'),
    path('customers/delete/<int:pk>/', views.customer_delete, name='customer_delete'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/edit/<int:pk>/', views.order_edit, name='order_edit'),
    path('orders/delete/<int:pk>/', views.order_delete, name='order_delete'),

    path('sales/', views.sales_list, name='sales_list'),
    path('sales/create/', views.sales_create, name='sales_create'),
    path('sales/edit/<int:pk>/', views.sales_edit, name='sales_edit'),
    path('sales/delete/<int:pk>/', views.sales_delete, name='sales_delete'),
]
