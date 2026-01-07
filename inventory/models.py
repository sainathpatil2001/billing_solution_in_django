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
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)  # Changed to decimal for fractional quantities
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Added GST rate
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)  # Added minimum stock level
    batch_number = models.CharField(max_length=50, blank=True)
    hsn_number = models.CharField(max_length=50, blank=True)
    mfg_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Tax Details
    igst = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    show_product = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.gst_rate is not None:
             self.igst = self.gst_rate
             self.cgst = self.gst_rate / 2
             self.sgst = self.gst_rate / 2
        super().save(*args, **kwargs)

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
