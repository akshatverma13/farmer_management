from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from farmers.models import Farmer, Block
import redis
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

r = redis.Redis(host='localhost', port=6379, db=0)

class Command(BaseCommand):
    help = 'Generate monthly farmer addition report'

    def handle(self, *args, **kwargs):
        # Get the previous month
        today = datetime.now().date()
        last_month = today - relativedelta(months=1)
        month_str = last_month.strftime('%Y-%m')

        # Count farmers per user
        users = User.objects.all()
        for user in users:
            try:
                farmer_count = Farmer.objects.filter(
                    surveyor=user,
                    created_at__year=last_month.year,
                    created_at__month=last_month.month
                ).count()
                key = f'user:{user.id}:monthly_farmer_count:{month_str}'
                r.delete(key)  # Reset count
                if farmer_count > 0:
                    r.incrby(key, farmer_count)  # Atomic increment
                self.stdout.write(self.style.SUCCESS(f"User {user.id}: {farmer_count} farmers in {month_str}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error for user {user.id}: {e}"))

        # Count farmers per block
        blocks = Block.objects.all()
        for block in blocks:
            try:
                farmer_count = Farmer.objects.filter(
                    block=block,
                    created_at__year=last_month.year,
                    created_at__month=last_month.month
                ).count()
                key = f'block:{block.id}:monthly_farmer_count:{month_str}'
                r.delete(key)  # Reset count
                if farmer_count > 0:
                    r.incrby(key, farmer_count)  # Atomic increment
                self.stdout.write(self.style.SUCCESS(f"Block {block.id}: {farmer_count} farmers in {month_str}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error for block {block.id}: {e}"))