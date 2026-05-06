from django.contrib import admin
from .models import Customer, Bill, BillItem, BusinessInformation

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address')
    search_fields = ('name', 'phone')

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'customer', 'total_amount', 'discount', 'final_amount')
    list_filter = ('customer',)
    search_fields = ('bill_number', 'customer__name')

@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    list_display = ('bill', 'product', 'quantity', 'price', 'total_price')
    list_filter = ('product',)
    search_fields = ('bill__bill_number', 'product__name')

@admin.register(BusinessInformation)
class BusinessInformationAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'phone', 'email')
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'address_line1', 'address_line2')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Tax Information', {
            'fields': ('gst_number',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one business information record
        return not BusinessInformation.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of business information
        return False
