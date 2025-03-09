from django.contrib import admin
from .models import Customer, Bill, BillItem

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
