#!/bin/sh
set -e

echo "==> Running Database Migrations..."
python manage.py migrate --noinput || echo "Migration skipped or failed, continuing..."

echo "==> Starting Celery Worker in background..."
celery -A core worker --loglevel=info --concurrency=1 &

echo "==> Starting Gunicorn Server on 0.0.0.0:8000..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120