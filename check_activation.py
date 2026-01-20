
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_maker.settings')
django.setup()

from genrate_bill.models import ActivationKey, BusinessInformation

def check_status():
    print("Checking Activation Status...")
    bind = BusinessInformation.get_business_info()
    print(f"Business Info: {bind}")
    print(f"Activation Expiry: {bind.activation_expiry_date}")
    
    keys = ActivationKey.objects.all()
    print(f"Total keys in DB: {keys.count()}")
    for key in keys:
        print(f" - {key}")

if __name__ == "__main__":
    check_status()
