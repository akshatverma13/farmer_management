# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Farmer
# from .tasks import update_daily_farmer_counts, increment_block_farmer_count
# import redis
# from datetime import datetime

# r = redis.Redis(host='localhost', port=6379, db=0)

# @receiver(post_save, sender=Farmer)
# def farmer_added(sender, instance, created, **kwargs):
#     if created:
#         date_str = instance.created_at.date().isoformat()
#         month_str = instance.created_at.strftime('%Y-%m')
        
#         # Use a Redis pipeline to batch increments
#         pipe = r.pipeline()
        
#         # Increment daily counts
#         user_daily_key = f'user:{instance.surveyor_id}:daily_farmer_count:{date_str}'
#         block_daily_key = f'block:{instance.block_id}:farmer_count:{date_str}'
#         pipe.incr(user_daily_key)
#         pipe.incr(block_daily_key)
        
#         # Increment monthly counts
#         user_monthly_key = f'user:{instance.surveyor_id}:monthly_farmer_count:{month_str}'
#         block_monthly_key = f'block:{instance.block_id}:monthly_farmer_count:{month_str}'
#         pipe.incr(user_monthly_key)
#         pipe.incr(block_monthly_key)
        
#         # Execute the pipeline
#         pipe.execute()
        
#         # Trigger daily count tasks (unchanged)
#         update_daily_farmer_counts.delay(instance.surveyor_id, date_str)
#         increment_block_farmer_count.delay(instance.block_id, date_str)

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Farmer
from .tasks import update_daily_farmer_counts, increment_block_farmer_count

@receiver(post_save, sender=Farmer)
def farmer_added(sender, instance, created, **kwargs):
    if created:
        date_str = instance.created_at.date().isoformat()
        month_str = instance.created_at.strftime('%Y-%m')
        # Trigger daily and monthly count updates
        update_daily_farmer_counts.delay(instance.surveyor_id, date_str, month_str)
        increment_block_farmer_count.delay(instance.block_id, date_str, month_str) 
       