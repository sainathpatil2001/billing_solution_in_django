
import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_maker.settings')
django.setup()

from genrate_bill.models import BusinessInformation

def activate_software():
    info = BusinessInformation.get_business_info()
    new_expiry = timezone.now().date() + timedelta(days=365)
    info.activation_expiry_date = new_expiry
    info.save()
    print(f"Software manually activated until {new_expiry}")

if __name__ == "__main__":
    activate_software()
