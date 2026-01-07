from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inventory/', include('inventory.urls')),
    path('billing/', include('genrate_bill.urls')),
    path('', include('genrate_bill.urls')),  # Launch billing directly at root
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
