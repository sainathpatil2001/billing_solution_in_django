from django.db import models
from django.utils import timezone
from inventory.models import Product

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Bill(models.Model):
    bill_number = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Bill #{self.bill_number} - {self.customer.name}"

    class Meta:
        ordering = ['-date']

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)
