from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory.urls')),
    path('billing/', include('genrate_bill.urls')),  # This will handle all billing routes
]
