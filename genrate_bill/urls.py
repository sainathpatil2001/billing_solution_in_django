from django.urls import path
from . import views

urlpatterns = [
    path('', views.generate_bill, name='billing'),
    path('generate-bill/', views.generate_bill, name='generate_bill'),
    path('search-bills/', views.search_bills, name='search_bills'),
    path('bill-details/<int:bill_id>/', views.get_bill_details, name='bill_details'),
    path('search-products/', views.search_billing_products, name='search_billing_products'),
    path('bills/', views.bills_page, name='bills_page'),
    path('business-settings/', views.business_settings, name='business_settings'),
    path('update-payment-status/<int:bill_id>/', views.update_payment_status, name='update_payment_status'),
    path('activation/', views.activation_page, name='activation_page'),
    path('activate-license/', views.activate_license, name='activate_license'),
    path('backup/', views.backup_page, name='backup_page'),
    path('backup/create/', views.create_backup, name='create_backup'),
    path('backup/restore/', views.restore_backup, name='restore_backup'),
    path('backup/settings/', views.update_backup_settings, name='update_backup_settings'),
]
