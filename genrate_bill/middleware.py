import datetime
from django.utils import timezone
from django.shortcuts import redirect
from genrate_bill.models import BusinessInformation

class ActivationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        
        # Paths that don't require activation
        allowed_paths = [
            '/billing/activation/', 
            '/billing/activate-license/', 
            '/activation/', 
            '/activate-license/', 
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        if any(path.startswith(p) for p in allowed_paths):
            return self.get_response(request)
            
        # Check activation
        try:
            business_info = BusinessInformation.get_business_info()
            if not business_info.activation_expiry_date or business_info.activation_expiry_date < timezone.now().date():
                return redirect('activation_page')
        except Exception:
            # If DB is not ready or migration issue, let it slide or handle gracefully.
            pass

        response = self.get_response(request)
        return response
