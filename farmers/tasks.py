from celery import shared_task
from django.core.management import call_command
import redis
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, db=0)

@shared_task
def update_daily_farmer_counts(user_id, date_str):
    key = f'user:{user_id}:daily_farmer_count:{date_str}'
    r.incr(key)  # Increment the count by 1
    return f"Incremented daily farmer count for user {user_id} on {date_str}"

@shared_task
def increment_block_farmer_count(block_id, date_str):
    key = f'block:{block_id}:farmer_count:{date_str}'
    r.incr(key)  # Increment the count by 1
    return f"Incremented block farmer count for block {block_id} on {date_str}"

@shared_task
def generate_monthly_report_task(year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    call_command('generate_monthly_report', year=year, month=month)
    return f"Monthly farmer report generated for {year}-{month:02d}"