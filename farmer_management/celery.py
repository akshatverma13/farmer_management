# Apply eventlet monkey patch at the very top
import sys
if 'worker' in sys.argv and '-P' in sys.argv and 'eventlet' in sys.argv:
    import eventlet
    eventlet.monkey_patch()

from celery import Celery

# Set the default Django settings module for Celery
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmer_management.settings')

app = Celery('farmer_management')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Update the package path for autodiscovery
app.autodiscover_tasks(['farmer_management.farmers'])