from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # ✅ IMPORT THIS

urlpatterns = [
    path('admin/', admin.site.urls),   # ✅ FIXED HERE
    path('', include('rental.urls')),
]

# Only add media URL patterns in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)