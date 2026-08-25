#!/bin/sh
set -e

echo "==> Running Database Migrations..."
python manage.py migrate --noinput

echo "==> Starting Celery Worker..."
celery -A core worker --loglevel=info --concurrency=1 &

echo "==> Starting Gunicorn Server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
