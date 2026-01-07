
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_maker.settings')
django.setup()

from genrate_bill.models import Bill

print("Checking full bill processing...")
try:
    bills = Bill.objects.all().order_by('-date')[:5]
    for bill in bills:
        try:
            print(f"Processing Bill {bill.bill_number}...")
            data = {
                'id': bill.bill_number,
                'bill_number': bill.bill_number,
                'date': bill.date.strftime('%Y-%m-%d') if bill.date else '',
                'customer_name': bill.customer.name if bill.customer else 'N/A',
                'customer_phone': bill.customer.phone if bill.customer else '',
                'total_amount': str(bill.total_amount),
                'discount': str(bill.discount),
                'final_amount': str(bill.final_amount),
                'payment_status': bill.payment_status,
                'payment_mode': bill.payment_mode,
                'payment_date': bill.payment_date.strftime('%Y-%m-%d') if bill.payment_date else ''
            }
            print(f"  Success: {data['bill_number']}")
        except Exception as e:
            print(f"  FAILED Bill {bill.bill_number}: {e}")
except Exception as e:
    print(f"Top level error: {e}")
