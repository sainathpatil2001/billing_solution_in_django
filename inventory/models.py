from django.db import models

class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., kg, liter, piece
    symbol = models.CharField(max_length=10)  # e.g., kg, L, pc
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_food_item = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    dealer_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)  # Changed to decimal for fractional quantities
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)  # Added minimum stock level
    show_product = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit.symbol if self.unit else ''}"
    
    @property
    def stock_status(self):
        if self.quantity <= 0:
            return "Out of Stock"
        elif self.quantity <= self.minimum_stock:
            return "Low Stock"
        return "In Stock"
    
    @property
    def total_value(self):
        return self.quantity * self.selling_price
