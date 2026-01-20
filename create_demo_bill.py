
import os
import django
import random
from decimal import Decimal
from django.utils import timezone

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bill_maker.settings")
django.setup()

from inventory.models import Product, Category, Unit
from genrate_bill.models import Bill, BillItem, Customer

def ensure_products_exist():
    """Ensures at least 10 products exist in the database."""
    count = Product.objects.count()
    if count >= 10:
        print(f"Found {count} existing products.")
        return

    print(f"Only found {count} products. Creating demo products...")
    
    # Create Units if needed
    unit, _ = Unit.objects.get_or_create(name='Piece', defaults={'symbol': 'pc'})
    category, _ = Category.objects.get_or_create(name='General', defaults={'is_food_item': False})
    
    for i in range(count + 1, 12):
        Product.objects.create(
            name=f"Demo Product {i}",
            category=category,
            unit=unit,
            dealer_price=50.00,
            selling_price=100.00,
            mrp=120.00,
            quantity=100,
            gst_rate=18.00,
            minimum_stock=10,
            batch_number=f"DEMO{i}",
            show_product=True
        )
    print("Created additional demo products.")

def create_bill():
    ensure_products_exist()
    
    # 1. Get or Create Customer
    customer, created = Customer.objects.get_or_create(
        name="Demo Customer",
        defaults={
            'phone': '9876543210',
            'address': '123 Demo St, Demo City',
            'state': 'Maharashtra', 
            'city': 'Demo City',
            'pincode': '400001'
        }
    )
    if created:
        print(f"Created Customer: {customer.name}")
    else:
        print(f"Using Customer: {customer.name}")

    # 2. Get 10 Products
    products = Product.objects.all().order_by('?')[:10]  # Random 10
    
    # 3. Create Bill
    bill = Bill.objects.create(
        customer=customer,
        date=timezone.now(),
        total_amount=0,
        final_amount=0,
        payment_status='Pending',
        payment_mode='Cash'
    )
    print(f"Created Bill #{bill.bill_number}")

    total_bill_amount = Decimal('0.00')

    # 4. Add Bill Items
    for product in products:
        qty = Decimal(random.randint(1, 5))
        price = product.selling_price
        
        # Determine Tax Structure
        # Assuming intra-state (Maharashtra) -> CGST + SGST
        # Django 'check_customer_state' logic implies if state == Maharashtra then GST (CGST+SGST), else IGST
        
        is_intra_state = (customer.state.strip().lower() == 'maharashtra')
        
        if is_intra_state:
             cgst_rate = product.gst_rate / 2
             sgst_rate = product.gst_rate / 2
             igst_rate = Decimal('0.00')
        else:
             cgst_rate = Decimal('0.00')
             sgst_rate = Decimal('0.00')
             igst_rate = product.gst_rate
             
        # Calculate Amounts
        base_amount = qty * price
        cgst_amt = ((base_amount * cgst_rate) / 100).quantize(Decimal('0.01'))
        sgst_amt = ((base_amount * sgst_rate) / 100).quantize(Decimal('0.01'))
        igst_amt = ((base_amount * igst_rate) / 100).quantize(Decimal('0.01'))
        
        total_item_price = (base_amount + cgst_amt + sgst_amt + igst_amt).quantize(Decimal('0.01'))
        
        BillItem.objects.create(
            bill=bill,
            product=product,
            quantity=qty,
            price=price,
            mrp=product.mrp,
            batch_number=product.batch_number,
            expiry_date=product.expiry_date,
            cgst_rate=cgst_rate,
            cgst_amount=cgst_amt,
            sgst_rate=sgst_rate,
            sgst_amount=sgst_amt,
            igst_rate=igst_rate,
            igst_amount=igst_amt,
            total_price=total_item_price
        )
        print(f"Added Item: {product.name} (Qty: {qty}, Total: {total_item_price:.2f})")
        total_bill_amount += total_item_price

    # 5. Update Bill Totals
    bill.total_amount = total_bill_amount
    bill.final_amount = total_bill_amount
    bill.save()
    print(f"\nSUCCESS: Bill #{bill.bill_number} finalized with Total Amount: {bill.final_amount:.2f}")

if __name__ == "__main__":
    create_bill()
