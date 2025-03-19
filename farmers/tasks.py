from celery import shared_task
from django.contrib.auth.models import User
from .models import Farmer
import redis
from datetime import datetime, timedelta
from django.core.management import call_command

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

@shared_task
def update_daily_farmer_counts():
    today = datetime.now().date()  # Use today's date
    date_str = today.strftime('%Y-%m-%d')
    users = User.objects.all()
    for user in users:
        try:
            # Reset count for the day
            key = f'user:{user.id}:daily_farmer_count:{date_str}'
            r.delete(key)  # Clear previous count
            # Count Farmer objects with surveyor=user and created_at__date=today
            farmer_count = Farmer.objects.filter(surveyor=user, created_at__date=today).count()
            if farmer_count > 0:
                r.incrby(key, farmer_count)  # Atomically set the count
        except Exception as e:
            print(f"Error for user {user.id}: {e}")
    return "Daily farmer counts updated"

@shared_task
def increment_block_farmer_count(block_id):
    today = datetime.now().date()
    date_str = today.strftime('%Y-%m-%d')
    key = f'block:{block_id}:farmer_count:{date_str}'
    count = r.incr(key) # increment by 1
    print(f"Incremented block {block_id} on {date_str} to {count} (triggered by signal or manual call)") #debug
    return f"Incremented farmer count for block {block_id} on {date_str}"


@shared_task
def run_monthly_farmer_report():
    call_command('generate_monthly_report')
    return "Monthly farmer report generated"