
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_maker.settings')
django.setup()

from genrate_bill.models import ActivationKey

def restore_keys():
    keys = [
        "25F70E24-9FB5-47B9-9C79-",
        "27C55DE9-D162-4EF6-98C7-",
        "E5476737-5267-4776-9575-",
        "8FDF9B51-557B-4C49-8548-",
        "51C45FC4-F6C1-462D-8898-",
        "7645C17B-2069-496C-B90C-",
        "EB099D5B-FCF4-4493-B777-",
        "D2A8A995-1E77-41E1-B995-",
        "D3CCA8BD-41C0-49FF-8F5D-",
        "5B323D5D-96F4-493F-9612-"
    ]
    
    count = 0
    for key in keys:
        obj, created = ActivationKey.objects.get_or_create(
            key=key,
            defaults={'duration_months': 6, 'is_used': False}
        )
        if created:
            count += 1
            print(f"Restored key: {key}")
        else:
            print(f"Key already exists: {key}")
            
    print(f"Restored {count} keys.")

if __name__ == "__main__":
    restore_keys()
