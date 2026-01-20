
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_maker.settings')
django.setup()

from inventory.models import Product, Category, Unit

def create_demo_products():
    # 1. Ensure Category
    category, _ = Category.objects.get_or_create(
        name='Demo', 
        defaults={'description': 'Demo Products', 'is_food_item': False}
    )

    # 2. Ensure Unit
    unit, _ = Unit.objects.get_or_create(
        name='Pieces', 
        defaults={'symbol': 'Pc'}
    )

    # 3. Create Products 'a' through 'j'
    product_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    
    created_count = 0
    for name in product_names:
        product, created = Product.objects.get_or_create(
            name=name,
            defaults={
                'category': category,
                'unit': unit,
                'dealer_price': Decimal('50.00'),
                'selling_price': Decimal('100.00'),
                'mrp': Decimal('120.00'),
                'quantity': Decimal('1000.00'),
                'minimum_stock': Decimal('10.00'),
                'gst_rate': Decimal('5.00'),
                'batch_number': 'DEMO001',
                'hsn_number': '9999',
            }
        )
        
        # Ensure tax is 5% even if product existed but was different (optional, but requested "set all to tax 5 percent")
        if not created or product.gst_rate != Decimal('5.00'):
            product.gst_rate = Decimal('5.00')
            product.save() # This triggers the save() method which updates igst/cgst/sgst
            
        print(f"Processed product: {name}")

if __name__ == '__main__':
    create_demo_products()
    print("Demo products added successfully.")
