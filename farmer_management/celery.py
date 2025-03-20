import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmer_management.settings')

app = Celery('farmer_management')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule the monthly report generation
app.conf.beat_schedule = {
    'generate-monthly-report': {
        'task': 'farmers.tasks.generate_monthly_report_task',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # Run on the 1st of each month at night
    },
}