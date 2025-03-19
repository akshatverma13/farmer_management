from celery import Celery
from celery.schedules import crontab
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmer_management.settings')

app = Celery('farmer_management')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'generate-monthly-report': {
        'task': 'farmers.tasks.run_monthly_farmer_report',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # Run on the 1st of every month at midnight
    },
}

# Disable prefetch and tracing issues on Windows
app.conf.task_track_started = False
app.conf.task_ignore_result = False  # Ensure results are stored
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.worker_hijack_root_logger = False