from celery import Celery
from celery.schedules import crontab

app = Celery('farmer_management')

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
app.autodiscover_tasks(['farmers'])

# Schedule the monthly report generation
app.conf.beat_schedule = {
    'generate-monthly-report': {
        'task': 'farmers.tasks.run_monthly_farmer_report',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # Run on the 1st of each month at midnight
        'args': (), #previous month
    },
}