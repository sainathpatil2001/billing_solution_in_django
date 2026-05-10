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
    path('payment-history/<int:bill_id>/', views.get_payment_history, name='get_payment_history'),
    path('delete-all-bills/', views.delete_all_bills, name='delete_all_bills'),
    path('backup/', views.backup_page, name='backup_page'),
    path('backup/create/', views.create_backup, name='create_backup'),
    path('backup/restore/', views.restore_backup, name='restore_backup'),
    path('backup/settings/', views.update_backup_settings, name='update_backup_settings'),
    
    # Customer Management
    path('customers/', views.customers_page, name='customers_page'),
    path('customers/save/', views.save_customer, name='save_customer'),
    path('customers/delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),
    path('api/customer-by-phone/<str:phone>/', views.get_customer_by_phone, name='get_customer_by_phone'),
    
    # Tax Center
    path('tax-center/', views.tax_center_page, name='tax_center_page'),
    path('tax-center/search-bills/', views.tax_center_search_bills, name='tax_center_search_bills'),
    path('tax-center/stats/', views.get_tax_stats, name='get_tax_stats'),
    path('tax-center/download/', views.download_tax_report, name='download_tax_report'),
    path('tax-center/ca-pdf-report/', views.ca_pdf_report, name='ca_pdf_report'),
    path('tax-center/download-bills-zip/', views.download_bills_zip, name='download_bills_zip'),
    
    # Analytics
    path('analytics/', views.sales_analytics_page, name='sales_analytics_page'),
    path('analytics/data/', views.get_analytics_data, name='get_analytics_data'),
]
