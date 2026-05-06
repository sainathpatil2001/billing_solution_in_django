from django.test import TestCase, Client
from django.urls import reverse
from .models import Category, Unit, Product
from decimal import Decimal
import json

class InventoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Medicines", description="All medicines")
        self.unit = Unit.objects.create(name="Strip", symbol="stp")
        self.product = Product.objects.create(
            name="Paracetamol",
            category=self.category,
            unit=self.unit,
            dealer_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
            mrp=Decimal("20.00"),
            quantity=Decimal("100.00"),
            minimum_stock=Decimal("10.00"),
            gst_rate=Decimal("12.00")
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Paracetamol")
        self.assertEqual(self.product.gst_rate, Decimal("12.00"))
        # Check automatic tax calculation
        self.assertEqual(self.product.igst, Decimal("12.00"))
        self.assertEqual(self.product.cgst, Decimal("6.00"))
        self.assertEqual(self.product.sgst, Decimal("6.00"))

    def test_stock_status(self):
        self.product.quantity = Decimal("100.00")
        self.assertEqual(self.product.stock_status, "In Stock")
        
        self.product.quantity = Decimal("5.00")
        self.assertEqual(self.product.stock_status, "Low Stock")
        
        self.product.quantity = Decimal("0.00")
        self.assertEqual(self.product.stock_status, "Out of Stock")

    def test_total_value(self):
        # 5 * 15.00 = 75.00
        self.product.quantity = Decimal("5.00")
        self.assertEqual(self.product.total_value, Decimal("75.00"))


class InventoryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Medicines")
        self.unit = Unit.objects.create(name="Strip", symbol="stp")
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            unit=self.unit,
            dealer_price=Decimal("100"),
            selling_price=Decimal("150"),
            mrp=Decimal("200"),
            quantity=Decimal("50"),
            minimum_stock=Decimal("10"),
            gst_rate=Decimal("18")
        )
        
        # Setup Business Info for Middleware
        from genrate_bill.models import BusinessInformation
        from django.utils import timezone
        business_info = BusinessInformation.get_business_info()
        business_info.activation_expiry_date = timezone.now().date() + timezone.timedelta(days=365)
        business_info.save()

    def test_add_product(self):
        url = reverse('inventory_management')
        data = {
            'name': 'New Product',
            'category': self.category.id,
            'unit': self.unit.id,
            'dealer_price': '50',
            'selling_price': '80',
            'mrp': '100',
            'quantity': '20',
            'minimum_stock': '5',
            'gst_rate': '12',
            'batch_number': 'B123',
            'hsn_number': '1234',
            'show_product': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Product.objects.filter(name='New Product').exists())

    def test_update_product(self):
        url = reverse('inventory_management')
        data = {
            'product_id': self.product.id,
            'name': 'Updated Product',
            'category': self.category.id,
            'unit': self.unit.id,
            'dealer_price': '100',
            'selling_price': '160',
            'mrp': '200',
            'quantity': '60',
            'minimum_stock': '10',
            'gst_rate': '18',
            'show_product': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        # Check for error in context
        if response.context and 'error' in response.context:
             print(f"Update Product Error: {response.context['error']}")
             
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product')
        self.assertEqual(self.product.quantity, Decimal('60.000')) # Model has 3 decimal places

    def test_search_product(self):
        url = reverse('search_product')
        response = self.client.get(url, {'query': 'Test'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data['products']), 0)
        self.assertEqual(data['products'][0]['name'], 'Test Product')

    def test_delete_product(self):
        url = reverse('delete_product', args=[self.product.id])
        response = self.client.post(url) # Using POST as per require_POST decorator
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_manage_categories(self):
        url = reverse('manage_categories')
        
        # Test Create
        data = {'name': 'New Category', 'description': 'Test Desc'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Category.objects.filter(name='New Category').exists())
        
        # Test Delete (need a category without products)
        cat = Category.objects.create(name="Delete Me")
        del_url = reverse('delete_category', args=[cat.id])
        response = self.client.delete(del_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Category.objects.filter(id=cat.id).exists())

    def test_manage_units(self):
        url = reverse('manage_units')
        
        # Test Create
        data = {'name': 'Box', 'symbol': 'box'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Unit.objects.filter(name='Box').exists())

class InventoryEdgeCaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Edge Case Category")
        self.unit = Unit.objects.create(name="Edge Unit", symbol="eu")
        # Setup Business Info for Middleware
        from genrate_bill.models import BusinessInformation
        from django.utils import timezone
        business_info = BusinessInformation.get_business_info()
        business_info.activation_expiry_date = timezone.now().date() + timezone.timedelta(days=365)
        business_info.save()

    def test_add_product_missing_fields(self):
        url = reverse('inventory_management')
        data = {
            'name': 'Incomplete Product',
            # missing required fields
        }
        response = self.client.post(url, data)
        # Should not crash, should just return to the form with errors or handle gracefully
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(name='Incomplete Product').exists())

    def test_add_product_negative_price(self):
        url = reverse('inventory_management')
        data = {
            'name': 'Negative Price Product',
            'category': self.category.id,
            'unit': self.unit.id,
            'dealer_price': '-50',  # invalid
            'selling_price': '-80', # invalid
            'mrp': '-100',
            'quantity': '20',
            'minimum_stock': '5',
            'gst_rate': '12',
            'show_product': True
        }
        response = self.client.post(url, data)
        # Assuming the form validation handles it, it shouldn't crash (500)
        self.assertEqual(response.status_code, 200)

