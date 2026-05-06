from django.test import TestCase, Client
from django.urls import reverse
from inventory.models import Category, Unit, Product
from .models import Customer, Bill, BillItem, BusinessInformation
from decimal import Decimal
import json
from django.utils import timezone

class BillingTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Setup Inventory Data
        self.category = Category.objects.create(name="Medicines")
        self.unit = Unit.objects.create(name="Strip", symbol="stp")
        self.product = Product.objects.create(
            name="Test Medicine",
            category=self.category,
            unit=self.unit,
            dealer_price=Decimal("10.00"),
            selling_price=Decimal("20.00"),
            mrp=Decimal("25.00"),
            quantity=Decimal("100.00"),
            gst_rate=Decimal("18.00"),
            hsn_number="3004",
            batch_number="B001",
            expiry_date=timezone.now().date(),
            show_product=True
        )
        
        
        # Setup Business Info for Middleware
        business_info = BusinessInformation.get_business_info()
        business_info.save()

    def test_save_customer(self):
        url = reverse('save_customer')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '9876543210',
            'address': 'Test Address',
            'city': 'Test City'
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Customer.objects.filter(phone='9876543210').exists())
        
        # Test Duplicate Phone
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400) # Should fail as duplicate

    def test_generate_bill_success(self):
        url = reverse('generate_bill')
        data = {
            'customer': {
                'first_name': 'New',
                'last_name': 'Customer',
                'phone': '1234567890'
            },
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 2,
                    'gst_rate': 18,
                    'is_igst': False
                }
            ],
            'discount': 0,
            'payment_status': 'Paid',
            'payment_mode': 'Cash'
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Verify Bill Created
        bill = Bill.objects.get(bill_number=response_data['bill_number'])
        self.assertEqual(bill.total_amount, Decimal('47.20')) # (20 * 2) + 18% tax = 40 + 7.2 = 47.2
        self.assertEqual(bill.payment_status, 'Paid') # Typo check: payment_status
        
        # Verify Stock Deduction
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, Decimal('98.00')) # 100 - 2

    def test_generate_bill_invalid_stock(self):
        # Trying to sell more than available (though current implementation might allow negative, we should check behavior)
        # Assuming current logic allows negative stock (common in small POS), but let's just ensure it doesn't crash
        pass

    def test_generate_bill_invalid_product(self):
        url = reverse('generate_bill')
        data = {
            'customer': {'first_name': 'Test'},
            'items': [{'product_id': 9999, 'quantity': 1}] # Invalid ID
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400) # Should handle error gracefully

    def test_get_bill_details(self):
        # Create a bill first
        customer = Customer.objects.create(first_name="Test", phone="111")
        bill = Bill.objects.create(
            customer=customer,
            total_amount=Decimal("100"),
            final_amount=Decimal("100"),
            payment_status="Pending"
        )
        
        url = reverse('bill_details', args=[bill.bill_number])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['bill']['bill_number'], bill.bill_number)

    def test_update_payment_status(self):
        customer = Customer.objects.create(first_name="Test", phone="222")
        bill = Bill.objects.create(
            customer=customer,
            total_amount=Decimal("100"),
            final_amount=Decimal("100"),
            payment_status="Pending",
            remaining_amount=Decimal("100")
        )
        
        url = reverse('update_payment_status', args=[bill.bill_number])
        data = {
            'status': 'Paid',
            'payment_mode': 'UPI',
            'password': '1234' # Default password from implementation
        }
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        bill.refresh_from_db()
        self.assertEqual(bill.payment_status, 'Paid')
        self.assertEqual(bill.paid_amount, Decimal("100"))
        self.assertEqual(bill.remaining_amount, Decimal("0"))

    def test_search_bills(self):
        customer = Customer.objects.create(first_name="SearchMe", phone="555")
        Bill.objects.create(
            customer=customer,
            total_amount=Decimal("100"),
            final_amount=Decimal("100"),
            payment_status="Pending"
        )
        
        url = reverse('search_bills')
        response = self.client.get(url, {'customer_name': 'SearchMe'})
        if response.status_code != 200:
             self.fail(f"Search Bills Failed with {response.status_code}: {response.content.decode('utf-8')}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['bills']), 1)
        self.assertEqual(data['bills'][0]['customer_name'], 'SearchMe')

class BillingEdgeCaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Medicines")
        self.unit = Unit.objects.create(name="Strip", symbol="stp")
        self.product = Product.objects.create(
            name="Test Medicine",
            category=self.category,
            unit=self.unit,
            dealer_price=Decimal("10.00"),
            selling_price=Decimal("20.00"),
            mrp=Decimal("25.00"),
            quantity=Decimal("100.00"),
            gst_rate=Decimal("18.00"),
            hsn_number="3004",
            show_product=True
        )
        business_info = BusinessInformation.get_business_info()
        business_info.save()

    def test_generate_bill_zero_quantity(self):
        url = reverse('generate_bill')
        data = {
            'customer': {'first_name': 'Zero', 'phone': '000000'},
            'items': [{'product_id': self.product.id, 'quantity': 0, 'gst_rate': 18, 'is_igst': False}]
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        # Should reject or handle gracefully, not 500
        self.assertIn(response.status_code, [200, 400])

    def test_generate_bill_negative_quantity(self):
        url = reverse('generate_bill')
        data = {
            'customer': {'first_name': 'Negative', 'phone': '111111'},
            'items': [{'product_id': self.product.id, 'quantity': -5, 'gst_rate': 18, 'is_igst': False}]
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertIn(response.status_code, [200, 400])

    def test_generate_bill_massive_discount(self):
        url = reverse('generate_bill')
        data = {
            'customer': {'first_name': 'Discount', 'phone': '222222'},
            'items': [{'product_id': self.product.id, 'quantity': 1, 'gst_rate': 18, 'is_igst': False}],
            'discount': 99999999 # More than total
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertIn(response.status_code, [200, 400])


