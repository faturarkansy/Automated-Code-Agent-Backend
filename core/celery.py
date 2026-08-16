import os
from celery import Celery

# Set default settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Membaca konfigurasi dengan prefix CELERY_ dari settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Otomatis mendeteksi tasks.py di semua registered apps
app.autodiscover_tasks()