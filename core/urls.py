from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('api/v1/', include('apps.repositories.urls')),
    path('api/v1/', include('apps.audit_logs.urls')),
]