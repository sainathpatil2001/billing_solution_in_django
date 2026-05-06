from . import views
from django.urls import path

urlpatterns = [
    path('', views.landing_home_page, name='home'),
    path('inventory_management/', views.Manage_inventory, name='inventory_management'),
    path('search-product/', views.search_product, name='search_product'),
    path('product-details/<int:product_id>/', views.product_details, name='product_details'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('manage-categories/', views.manage_categories, name='manage_categories'),
    path('manage-categories/<int:category_id>/', views.manage_categories, name='delete_category'),
    path('manage-units/', views.manage_units, name='manage_units'),
    path('manage-units/<int:unit_id>/', views.manage_units, name='delete_unit'),
]