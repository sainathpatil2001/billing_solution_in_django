
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_maker.settings')
django.setup()

from genrate_bill.models import Bill

try:
    print(f"Total bills: {Bill.objects.count()}")
    for bill in Bill.objects.all()[:5]:
        print(f"Bill: {bill.bill_number}")
        print(f"  Date: {bill.date}")
        print(f"  Status: {bill.payment_status}")
        print(f"  Mode: {bill.payment_mode}")
        print(f"  P.Date: {bill.payment_date}")
except Exception as e:
    print(f"Error: {e}")
