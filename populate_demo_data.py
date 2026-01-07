import random
from datetime import date, timedelta
from inventory.models import Product, Category, Unit

def create_demo_data():
    print("Starting demo data creation...")

    # 1. Create Units
    units_data = [
        {'name': 'Piece', 'symbol': 'pc'},
        {'name': 'Strip', 'symbol': 'strip'},
        {'name': 'Bottle', 'symbol': 'btl'},
        {'name': 'Kilogram', 'symbol': 'kg'},
        {'name': 'Liter', 'symbol': 'L'},
    ]
    
    units = {}
    for u in units_data:
        unit_obj, created = Unit.objects.get_or_create(name=u['name'], defaults={'symbol': u['symbol']})
        units[u['symbol']] = unit_obj
        if created:
            print(f"Created Unit: {u['name']}")

    # 2. Create Categories
    categories_data = [
        {'name': 'Pharma', 'is_food_item': False},
        {'name': 'Grocery', 'is_food_item': True},
        {'name': 'Cosmetics', 'is_food_item': False},
        {'name': 'Beverages', 'is_food_item': True},
    ]
    
    categories = {}
    for c in categories_data:
        cat_obj, created = Category.objects.get_or_create(name=c['name'], defaults={'is_food_item': c['is_food_item']})
        categories[c['name']] = cat_obj
        if created:
            print(f"Created Category: {c['name']}")

    # 3. Create Products
    products_list = [
        # Pharma
        {'name': 'Paracetamol 500mg', 'cat': 'Pharma', 'unit': 'strip', 'dp': 15, 'sp': 25, 'mrp': 30, 'qty': 200, 'gst': 12, 'batch': 'PARA001', 'exp_days': 365},
        {'name': 'Cough Syrup 100ml', 'cat': 'Pharma', 'unit': 'btl', 'dp': 60, 'sp': 95, 'mrp': 110, 'qty': 50, 'gst': 12, 'batch': 'CSYR202', 'exp_days': 180},
        {'name': 'Vitamin C Tablets', 'cat': 'Pharma', 'unit': 'strip', 'dp': 30, 'sp': 50, 'mrp': 60, 'qty': 150, 'gst': 12, 'batch': 'VITC99', 'exp_days': 500},
        {'name': 'Dolo 650', 'cat': 'Pharma', 'unit': 'strip', 'dp': 18, 'sp': 28, 'mrp': 35, 'qty': 300, 'gst': 12, 'batch': 'DOLO65', 'exp_days': 400},
        {'name': 'Bandage Roll', 'cat': 'Pharma', 'unit': 'pc', 'dp': 10, 'sp': 20, 'mrp': 25, 'qty': 100, 'gst': 5, 'batch': 'BAND01', 'exp_days': 1000},
        
        # Grocery
        {'name': 'Basmati Rice', 'cat': 'Grocery', 'unit': 'kg', 'dp': 80, 'sp': 110, 'mrp': 130, 'qty': 500, 'gst': 0, 'batch': 'BRICE1', 'exp_days': 180},
        {'name': 'Toor Dal', 'cat': 'Grocery', 'unit': 'kg', 'dp': 90, 'sp': 130, 'mrp': 150, 'qty': 200, 'gst': 0, 'batch': 'TDAL02', 'exp_days': 90},
        {'name': 'Sunflower Oil 1L', 'cat': 'Grocery', 'unit': 'L', 'dp': 110, 'sp': 145, 'mrp': 160, 'qty': 100, 'gst': 5, 'batch': 'OIL55', 'exp_days': 200},
        {'name': 'Sugar', 'cat': 'Grocery', 'unit': 'kg', 'dp': 35, 'sp': 42, 'mrp': 45, 'qty': 300, 'gst': 0, 'batch': 'SUG12', 'exp_days': 365},
        {'name': 'Tata Salt', 'cat': 'Grocery', 'unit': 'kg', 'dp': 18, 'sp': 24, 'mrp': 28, 'qty': 150, 'gst': 0, 'batch': 'SALT99', 'exp_days': 700},

        # Cosmetics
        {'name': 'Face Wash 100ml', 'cat': 'Cosmetics', 'unit': 'btl', 'dp': 80, 'sp': 120, 'mrp': 150, 'qty': 40, 'gst': 18, 'batch': 'FWASH1', 'exp_days': 300},
        {'name': 'Shampoo 200ml', 'cat': 'Cosmetics', 'unit': 'btl', 'dp': 110, 'sp': 170, 'mrp': 200, 'qty': 60, 'gst': 18, 'batch': 'SHAM02', 'exp_days': 400},
        {'name': 'Moisturizer', 'cat': 'Cosmetics', 'unit': 'btl', 'dp': 150, 'sp': 220, 'mrp': 250, 'qty': 30, 'gst': 18, 'batch': 'MOIST5', 'exp_days': 365},
        
        # Beverages
        {'name': 'Cola 500ml', 'cat': 'Beverages', 'unit': 'btl', 'dp': 25, 'sp': 38, 'mrp': 40, 'qty': 120, 'gst': 18, 'batch': 'COLA01', 'exp_days': 90},
        {'name': 'Mango Juice 1L', 'cat': 'Beverages', 'unit': 'btl', 'dp': 60, 'sp': 90, 'mrp': 100, 'qty': 80, 'gst': 12, 'batch': 'MANG22', 'exp_days': 120},
    ]

    count = 0
    today = date.today()

    for p in products_list:
        # Check if exists
        if Product.objects.filter(name=p['name']).exists():
            print(f"Skipping {p['name']}, already exists.")
            continue
            
        Product.objects.create(
            name=p['name'],
            category=categories[p['cat']],
            unit=units[p['unit']],
            dealer_price=p['dp'],
            selling_price=p['sp'],
            mrp=p['mrp'],
            quantity=p['qty'],
            gst_rate=p['gst'],
            minimum_stock=10,
            batch_number=p['batch'],
            expiry_date=today + timedelta(days=p['exp_days']),
            show_product=True
        )
        count += 1
        print(f"Created Product: {p['name']}")

    print(f"Successfully added {count} new demo products.")

create_demo_data()
