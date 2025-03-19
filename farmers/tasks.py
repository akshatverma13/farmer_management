from celery import shared_task
from django.contrib.auth.models import User
from .models import UserProfile
import redis
from datetime import datetime, timedelta

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

@shared_task
def update_daily_farmer_counts():
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')
    users = User.objects.all()
    for user in users:
        try:
            farmer_count = UserProfile.objects.filter(user=user, created_at__date=yesterday.date()).count()
            r.set(f'user:{user.id}:daily_farmer_count:{date_str}', farmer_count)
        except Exception as e:
            print(f"Error for user {user.id}: {e}")
    return "Daily farmer counts updated"