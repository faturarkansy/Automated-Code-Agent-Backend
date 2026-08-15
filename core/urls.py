from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.repositories.urls')),
    path('api/v1/', include('apps.audit_logs.urls')),
]