from django.db import models
from django.utils import timezone
from inventory.models import Product
import uuid
import datetime

# Create your models here.



class BusinessInformation(models.Model):
    company_name = models.CharField(max_length=200, default="Your Company Name")
    address_line1 = models.CharField(max_length=200, default="Address Line 1")
    address_line2 = models.CharField(max_length=200, blank=True, default="Address Line 2")
    phone = models.CharField(max_length=20, default="+1234567890")
    email = models.EmailField(default="example@email.com")
    city = models.CharField(max_length=100, default="City")
    pincode = models.CharField(max_length=20, default="000000")
    state = models.CharField(max_length=100, default="State")
    district = models.CharField(max_length=100, default="District")
    sub_district = models.CharField(max_length=100, default="Taluka")
    gst_number = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)

    website = models.URLField(blank=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    security_password = models.CharField(max_length=50, default="1234")
    upi_id = models.CharField(max_length=50, blank=True, help_text="UPI ID for receiving payments (e.g. username@bank)")
    terms_and_conditions = models.TextField(default="1. Goods once sold will not be taken back or exchanged.\n2. All disputes are subject to jurisdiction only.")
    
    
    # Backup configuration
    last_backup_date = models.DateTimeField(null=True, blank=True)
    backup_reminder_days = models.IntegerField(default=7, help_text="Recommend backup every N days")
    
    class Meta:
        verbose_name = "Business Information"
        verbose_name_plural = "Business Information"
    
    def __str__(self):
        return self.company_name
    
    @classmethod
    def get_business_info(cls):
        """Get the business information, create default if none exists"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Customer(models.Model):
    first_name = models.CharField(max_length=50, default='')
    middle_name = models.CharField(max_length=50, blank=True, default='')
    last_name = models.CharField(max_length=50, blank=True, default='')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    sub_district = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    drug_license_number = models.CharField(max_length=50, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    extra_note = models.TextField(blank=True, null=True)
    
    @property
    def name(self):
        """Return full name by combining first, middle, and last name."""
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(part for part in parts if part).strip()
    
    def __str__(self):
        return self.name

class Bill(models.Model):
    bill_number = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Partially Paid', 'Partially Paid')], default='Pending')
    payment_mode = models.CharField(max_length=20, choices=[('Cash', 'Cash'), ('Online', 'Online')], null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Transport / Invoice Details
    transport_mode = models.CharField(max_length=50, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    supply_date = models.DateField(null=True, blank=True)
    place_of_supply = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Bill #{self.bill_number} - {self.customer.name}"

    class Meta:
        ordering = ['-date']

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    hsn_number = models.CharField(max_length=50, blank=True)
    mfg_date = models.DateField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cgst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    igst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # self.total_price is calculated in the view or here if needed
        # We should respect the values if they are set, or calculate them
        # For safety/consistency with the view:
        base_price = self.quantity * self.price
        self.total_price = base_price + self.cgst_amount + self.sgst_amount + self.igst_amount
        super().save(*args, **kwargs)

class PaymentHistory(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payment_history')
    payment_date = models.DateField(default=timezone.now)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=[('Cash', 'Cash'), ('Online', 'Online')], null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment of {self.amount_paid} for Bill #{self.bill.bill_number} on {self.payment_date}"
