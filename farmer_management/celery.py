from celery import Celery

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmer_management.settings')

app = Celery('farmer_management')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Disable prefetch and tracing issues on Windows
app.conf.task_track_started = False
app.conf.task_ignore_result = False  # Ensure results are stored
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.worker_hijack_root_logger = False