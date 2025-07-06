from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard_view'),
    path('', views.home_redirect, name='home'),
    path('raw_table/<str:table_name>/', views.dynamic_table_sql_crud, name='dynamic_table_sql_crud'),
    path('raw_table/<str:table_name>/delete/<str:pk_value>/', views.delete_row, name='delete_row'),
    path('edit/<str:table_name>/<str:pk>/', views.dynamic_edit_row, name='dynamic_edit_row'),
    path('create_table/', views.create_table_view, name='create_table'),
    
    path('sql/', views.sql_editor, name='sql_editor'),
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('show/<str:table_name>/<str:pk>/', views.dynamic_show_row, name='dynamic_show_row'),
    ]