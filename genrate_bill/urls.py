from django.urls import path
from . import views

urlpatterns = [
    path('', views.generate_bill, name='billing'),
    path('generate-bill/', views.generate_bill, name='generate_bill'),
    path('search-bills/', views.search_bills, name='search_bills'),
    path('bill-details/<int:bill_id>/', views.get_bill_details, name='bill_details'),
    path('search-products/', views.search_billing_products, name='search_billing_products'),
    path('bills/', views.bills_page, name='bills_page'),
]
